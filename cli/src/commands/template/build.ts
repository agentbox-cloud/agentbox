import * as commander from 'commander'
import fs from 'fs'
import path from 'path'
import * as e2b from 'e2b'
import boxen from 'boxen'
import commandExists from 'command-exists'
import archiver from 'archiver'
import { minimatch } from 'minimatch'


import { wait } from 'src/utils/wait'
import { client, connectionConfig, ensureAccessToken } from 'src/api'
import { getRoot } from 'src/utils/filesystem'
import {
  asBold,
  asBuildLogs,
  asFormattedSandboxTemplate,
  asLocal,
  asLocalRelative,
  asPrimary,
  asPython,
  asTypescript,
  withDelimiter,
} from 'src/utils/format'
import { configOption, pathOption, teamOption } from 'src/options'
import { defaultDockerfileName, fallbackDockerfileName } from 'src/docker/constants'
import { configName, getConfigPath, loadConfig, saveConfig } from 'src/config'
import * as child_process from 'child_process'
import { handleE2BRequestError } from '../../utils/errors'
import { getUserConfig } from 'src/user'
import { buildWithProxy } from './buildWithProxy'
import { getArchString, parseArchToEnvType, parseArchToBuildType, getArchDisplayName } from 'src/utils/platform'

const templateCheckInterval = 500 // 0.5 sec

// 定义 AgentBox 模板构建状态类型
type AgentBoxTemplateBuild = {
  templateID: string
  buildID: string
  status: 'building' | 'waiting' | 'ready' | 'error'
  logs: string
}

// 定义选项类型
type BuildOptions = {
  path?: string
  dockerfile?: string
  name?: string
  cmd?: string
  team?: string
  config?: string
  cpuCount?: number
  memoryMb?: number
  buildArg?: [string]
  noCache?: boolean
  custom?: boolean
  platform?: string
}

type BuildContext = {
  // templateID: string | undefined;
  // opts: BuildOptions;
  root: string;
  configPath: string;
  relativeConfigPath: string;
  config: Awaited<ReturnType<typeof loadConfig>> | undefined;
  archString: string;
}

async function createBuildContext(
  opts: BuildOptions
): Promise<BuildContext> {
  const root = getRoot(opts.path)
  const configPath = getConfigPath(root, opts.config)
  
  // Check if e2b.toml exists
  const configExists = fs.existsSync(configPath)
  let config: Awaited<ReturnType<typeof loadConfig>> | undefined
  
  if (configExists) {
    config = await loadConfig(configPath)
  }
  
  // Validate platform parameter
  let archString: string
  if (opts.platform) {
    const validPlatforms = ['linux_x86', 'linux_arm64', 'android']
    if (!validPlatforms.includes(opts.platform)) {
      throw new Error(`Invalid platform "${opts.platform}". Valid platforms are: ${validPlatforms.join(', ')}`)
    }
    archString = opts.platform
    
    // If e2b.toml exists and has a different platform, reject the build
    if (config && config.platform && config.platform !== opts.platform) {
      console.error(
        '❌ Platform mismatch detected!\n' +
        `   e2b.toml specifies platform: ${config.platform}\n` +
        `   --platform flag specifies: ${opts.platform}\n` +
        '   \n' +
        '   Please either:\n' +
        '   1. Remove the e2b.toml file to create a new template, or\n' +
        `   2. Change --platform to match the existing configuration: --platform ${config.platform}`
      )
      process.exit(1)
    }
    
  } else if (config?.platform) {
    archString = config.platform
  } else {
    archString = getArchString()
  }
  
  // If e2b.toml doesn't exist and platform is specified, create a new config
  if (!configExists && opts.platform) {
    console.log(`📝 Creating new e2b.toml with platform: ${getArchDisplayName(opts.platform)}`)
    // Note: The config will be saved later in the build process with all the template details
  }

  const relativeConfigPath = path.relative(root, configPath)

  return {
    root,
    configPath,
    relativeConfigPath,
    config,
    archString,
  }
}

async function getTemplateBuildLogs({
  templateID,
  buildID,
  logsOffset,
}: {
  templateID: string
  buildID: string
  logsOffset: number
}) {
  const signal = connectionConfig.getSignal()
  const res = await client.api.GET(
    '/templates/{templateID}/builds/{buildID}/status',
    {
      signal,
      params: {
        path: {
          templateID,
          buildID,
        },
        query: {
          logsOffset,
        },
      },
    }
  )

  handleE2BRequestError(res, 'Error getting template build status')
  return res.data as AgentBoxTemplateBuild
}

// 新增：获取 AgentBox 模板构建状态的专用函数
async function getAgentBoxTemplateBuildStatus({
  templateID,
  buildID,
}: {
  templateID: string
  buildID: string
}): Promise<AgentBoxTemplateBuild> {
  const signal = connectionConfig.getSignal()
  
  try {
    const res = await client.api.GET(
      '/templates/{templateID}/builds/{buildID}/agentbox/status',
      {
        signal,
        params: {
          path: {
            templateID,
            buildID,
          },
        },
      }
    )

    handleE2BRequestError(res, 'Error getting AgentBox template build status')
    
    // 确保返回的数据符合 AgentBoxTemplateBuild 结构
    const data = res.data as any
    return {
      templateID: data.templateID || templateID,
      buildID: data.buildID || buildID,
      status: data.status || 'waiting',
      logs: data.logs
    } as AgentBoxTemplateBuild
  } catch (error) {
    console.error('Failed to get AgentBox template build status:', error)
    // 返回默认结构以保持一致性
    return {
      templateID,
      buildID,
      status: 'error',
      logs: `Error fetching build status: ${error}`
    } as AgentBoxTemplateBuild
  }
}

async function requestTemplateBuild(
  args: e2b.paths['/templates']['post']['requestBody']['content']['application/json']
) {
  return await client.api.POST('/templates', {
    body: args,
  })
}

async function requestTemplateRebuild(
  templateID: string,
  args: e2b.paths['/templates/{templateID}']['post']['requestBody']['content']['application/json']
) {
  return await client.api.POST('/templates/{templateID}', {
    body: args,
    params: {
      path: {
        templateID,
      },
    },
  })
}

// Template validation functions
async function validateTemplateID(
  templateID: string | undefined,
  config: Awaited<ReturnType<typeof loadConfig>> | undefined
) {
  if (config && templateID && config.template_id !== templateID) {
    console.error(
      "You can't specify different ID than the one in config. If you want to build a new sandbox template remove the config file."
    )
    process.exit(1)
  }
}

async function triggerTemplateBuild(templateID: string, buildID: string) {
  let res
  const maxRetries = 3
  for (let i = 0; i < maxRetries; i++) {
    try {
      res = await client.api.POST('/templates/{templateID}/builds/{buildID}', {
        params: {
          path: {
            templateID,
            buildID,
          },
        },
      })
      break
    } catch (e) {
      // If the build and push takes more than 10 minutes the connection gets automatically closed by load balancer
      // and the request fails with UND_ERR_SOCKET error. In this case we just need to retry the request.
      if (
        e instanceof TypeError &&
        ((e as TypeError).cause as any)?.code !== 'UND_ERR_SOCKET'
      ) {
        console.error(e)
        console.log('Retrying...')
      }
    }
  }

  if (!res) {
    throw new Error('Error triggering template build')
  }

  handleE2BRequestError(res, 'Error triggering template build')
  return res.data
}

async function resourceZipUpload(templateID: string, buildID: string, zipFilePath: string) {
  let res
  const maxRetries = 3

  console.log(`🎯 [resourceZipUpload] Template ID: ${templateID}`)
  console.log(`🎯 [resourceZipUpload] Build ID: ${buildID}`)
  console.log(`🎯 [resourceZipUpload] Zip File Path: ${zipFilePath}`)
  
  // 读取 zip 文件
  if (!fs.existsSync(zipFilePath)) {
    throw new Error(`Zip file not found: ${zipFilePath}`)
  }
  
  const zipFileStats = fs.statSync(zipFilePath)
  const zipFileSize = zipFileStats.size
  const zipFileSizeMB = (zipFileSize / (1024 * 1024)).toFixed(2)
  
  console.log(`🎯 [resourceZipUpload] 文件大小: ${zipFileSizeMB} MB (${zipFileSize} bytes)`)
  
  for (let i = 0; i < maxRetries; i++) {
    try {
      const startTime = Date.now()
      console.log(`🎯 [resourceZipUpload] 尝试 ${i + 1}/${maxRetries} ...`)
      
      // 创建文件读取流
      const fileStream = fs.createReadStream(zipFilePath)
      
      // 使用原生 fetch 进行流式上传
      const apiUrl = `${connectionConfig.apiUrl}/templates/${templateID}/builds/${buildID}/resource/upload`
      const accessToken = ensureAccessToken()
      
      const response = await fetch(apiUrl, {
        method: 'POST',
        body: fileStream as any,
        duplex: 'half', // 流式上传所需的选项
        headers: {
          'Content-Type': 'application/octet-stream',
          'X-Object-Name': 'resource.zip',
          'Authorization': `Bearer ${accessToken}`,
        },
      } as any)

      const endTime = Date.now()
      const duration = endTime - startTime
      
      console.log(`🎯 [resourceZipUpload] success! 耗时: ${duration}ms`)
      console.log(`🎯 [resourceZipUpload] resp status: ${response.status}`)
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      
      // 创建兼容 handleE2BRequestError 的响应对象格式
      res = { 
        data: null,
        response: { status: response.status }
      } as any
      
      break
    } catch (e) {
      const retryCount = i + 1
      console.log(`🎯 [resourceZipUpload] 尝试 ${retryCount}/${maxRetries} - 请求失败`)
      console.error('🎯 [resourceZipUpload] 错误详情:', e)
      
      // If the build and push takes more than 10 minutes the connection gets automatically closed by load balancer
      // and the request fails with UND_ERR_SOCKET error. In this case we just need to retry the request.
      if (
        e instanceof TypeError &&
        ((e as TypeError).cause as any)?.code !== 'UND_ERR_SOCKET'
      ) {
        console.error('🎯 [resourceZipUpload] 非预期错误:', e)
        console.log('🎯 [resourceZipUpload] 准备重试...')
      }
      
      if (retryCount < maxRetries) {
        console.log('🎯 [resourceZipUpload] 等待 2 秒后重试...')
        await new Promise(resolve => setTimeout(resolve, 2000))
      }
    }
  }

  if (!res) {
    console.error('🎯 [resourceZipUpload] 所有重试都失败了!')
    throw new Error('Error upload resource file')
  }

  handleE2BRequestError(res, 'Error upload resource file')
  
  return res
}

export const buildCommand = new commander.Command('build')
  .description(
    `build sandbox template defined by ${asLocalRelative(
defaultDockerfileName
    )} or ${asLocalRelative(
      fallbackDockerfileName
    )} in root directory. By default the root directory is the current working directory. This command also creates ${asLocal(
      configName
    )} config.`
  )
  .argument(
    '[template]',
    `specify ${asBold(
      '[template]'
    )} to rebuild it. If you don't specify ${asBold(
      '[template]'
    )} and there is no ${asLocal(
      'e2b.toml'
    )} a new sandbox template will be created.`
  )
  .addOption(pathOption)
  .option(
    '-d, --dockerfile <file>',
    `specify path to Dockerfile. By default E2B tries to find ${asLocal(
defaultDockerfileName
    )} or ${asLocal(fallbackDockerfileName)} in root directory.`
  )
  .option(
    '-n, --name <template-name>',
    'specify sandbox template name. You can use the template name to start the sandbox with SDK. The template name must be lowercase and contain only letters, numbers, dashes and underscores.'
  )
  .option(
    '-c, --cmd <start-command>',
    'specify command that will be executed when the sandbox is started.'
  )
  .addOption(teamOption)
  .addOption(configOption)
  .option(
    '--cpu-count <cpu-count>',
    'specify the number of CPUs that will be used to run the sandbox. The default value is 2.',
    parseInt
  )
  .option(
    '--memory-mb <memory-mb>',
    'specify the amount of memory in megabytes that will be used to run the sandbox. Must be an even number. The default value is 512.',
    parseInt
  )
  .option(
    '--build-arg <args...>',
    'specify additional build arguments for the build command. The format should be <varname>=<value>.'
  )
  .option('--no-cache', 'skip cache when building the template.')
  .requiredOption('--platform <platform>', 'specify the platform for the template, e.g., android, linux_x86, linux_arm64')
  .alias('bd')
  .action(
    async (
      templateID: string | undefined,
      opts: BuildOptions,
    ) => {
      try {
        // Create the build context externally
        const context = await createBuildContext(opts)
        
        // Validate template ID before proceeding
        await validateTemplateID(templateID, context.config)
        
        // Set templateID from config if not provided
        if (context.config && !templateID) {
          templateID = context.config.template_id
        }

        if (context.archString === 'android') {
          await customBuildFlow(templateID, opts, context)
        } else {
          await standardBuildFlow(templateID, opts, context)
        }
      } catch (err: any) {
        console.error(err)
        process.exit(1)
      }
    },
  )

// 标准构建流程
async function standardBuildFlow(
  templateID: string | undefined,
  opts: BuildOptions,
  context: BuildContext,
) {
  console.log(`Using standard build flow (Firecracker) for platform: ${getArchDisplayName(context.archString)}`)
  const dockerInstalled = commandExists.sync('docker')
  if (!dockerInstalled) {
    console.error(
      'Docker is required to build and push the sandbox template. Please install Docker and try again.'
    )
    process.exit(1)
  }

  const dockerBuildArgs: { [key: string]: string } = {}
  if (opts.buildArg) {
    opts.buildArg.forEach((arg) => {
      const [key, value] = arg.split('=')
      dockerBuildArgs[key] = value
    })
  }

  const accessToken = ensureAccessToken()
  process.stdout.write('\n')

  const newName = opts.name?.trim()
  if (newName && !/[a-z0-9-_]+/.test(newName)) {
    console.error(
      `Name ${asLocal(
        newName
      )} is not valid. Name can only contain lowercase letters, numbers, dashes and underscores.`
    )
    process.exit(1)
  }

  let dockerfile = opts.dockerfile
  let startCmd = opts.cmd
  let cpuCount = opts.cpuCount
  let memoryMB = opts.memoryMb
  let teamID = opts.team

  if (context.config) {
    console.log(
      `Found sandbox template ${asFormattedSandboxTemplate(
        {
          templateID: context.config.template_id,
          aliases: context.config.template_name
            ? [context.config.template_name]
            : undefined,
        },
        context.relativeConfigPath
      )}`
    )
    templateID = context.config.template_id
    dockerfile = opts.dockerfile || context.config.dockerfile
    startCmd = opts.cmd || context.config.start_cmd
    cpuCount = opts.cpuCount || context.config.cpu_count
    memoryMB = opts.memoryMb || context.config.memory_mb
    teamID = opts.team || context.config.team_id
  } else {
    if (!opts.platform) {
      console.log(`Detected target platform: ${getArchDisplayName(context.archString)}`)
    }
  }

  const userConfig = getUserConfig()
  if (userConfig) {
    teamID = teamID || userConfig.teamId
  }

  if (context.config && templateID && context.config.template_id !== templateID) {
    console.error(
      "You can't specify different ID than the one in config. If you want to build a new sandbox template remove the config file."
    )
    process.exit(1)
  }

  if (
    newName &&
    context.config?.template_name &&
    newName !== context.config?.template_name
  ) {
    console.log(
      `The sandbox template name will be changed from ${asLocal(
        context.config.template_name
      )} to ${asLocal(newName)}.`
    )
  }
  const name = newName || context.config?.template_name

  const { dockerfileContent, dockerfileRelativePath } = getDockerfile(
    context.root,
    dockerfile
  )

  console.log(
    `Found ${asLocalRelative(
      dockerfileRelativePath
    )} that will be used to build the sandbox template.`
  )

  const envType = parseArchToEnvType(context.archString)
  const buildType = parseArchToBuildType(envType)
  
  const body = {
    alias: name,
    startCmd: startCmd,
    cpuCount: cpuCount,
    memoryMB: memoryMB,
    dockerfile: dockerfileContent,
    teamID: teamID,
    envType: envType,
  }

  if (opts.memoryMb) {
    if (opts.memoryMb % 2 !== 0) {
      console.error(
        `The memory in megabytes must be an even number. You provided ${asLocal(
          opts.memoryMb.toFixed(0)
        )}.`
      )
      process.exit(1)
    }
  }

  const template = await requestBuildTemplate(body, templateID)
  templateID = template.templateID

  console.log(
    `Requested build for the sandbox template ${asFormattedSandboxTemplate(
      template
    )} `
  )

  await saveConfig(
    context.configPath,
    {
      template_id: template.templateID,
      dockerfile: dockerfileRelativePath,
      template_name: name,
      start_cmd: startCmd,
      cpu_count: cpuCount,
      memory_mb: memoryMB,
      team_id: teamID,
      platform: context.archString,
    },
    true
  )

  try {
    child_process.execSync(
      `echo "${accessToken}" | docker login docker.${connectionConfig.domain} -u _e2b_access_token --password-stdin`,
      {
        stdio: 'inherit',
        cwd: context.root,
      }
    )
  } catch (err: any) {
    console.error(
      "Docker login failed. Please try to log in with 'agentbox auth login' and try again."
    )
    process.exit(1)
  }
  process.stdout.write('\n')

  const buildArgs = Object.entries(dockerBuildArgs)
    .map(([key, value]) => `--build-arg "${key}=${value}"`) // Corrected escaping for build args
    .join(' ')

  const noCache = opts.noCache ? '--no-cache' : ''

  const cmd = [
    'docker buildx build',
    `-f ${dockerfileRelativePath}`,
    `--pull --platform ${buildType}`,
    '--load',
    `-t docker.${connectionConfig.domain}/agentbox/custom-envs/${templateID}:${template.buildID}`,
    buildArgs,
    noCache,
    '.',
  ].join(' ')

  console.log(
    `Building docker image with the following command:\n${asBold(cmd)}\n`
  )

  child_process.execSync(cmd, {
    stdio: 'inherit',
    cwd: context.root,
    env: {
      ...process.env,
      DOCKER_CLI_HINTS: 'false',
    },
  })
  console.log('> Docker image built.\n')

  const pushCmd = `docker push docker.${connectionConfig.domain}/agentbox/custom-envs/${templateID}:${template.buildID}`
  console.log(
    `Pushing docker image with the following command:\n${asBold(
      pushCmd
    )}\n`
  )
  try {
    child_process.execSync(pushCmd, {
      stdio: 'inherit',
      cwd: context.root,
    })
  } catch (err: any) {
    await buildWithProxy(
      userConfig,
      connectionConfig,
      accessToken,
      template,
      context.root
    )
  }
  console.log('> Docker image pushed.\n')

  console.log('Triggering build...')
  await triggerBuild(templateID, template.buildID)

  console.log(
    `> Triggered build for the sandbox template ${asFormattedSandboxTemplate(
      template
    )} with build ID: ${template.buildID}`
  )

  console.log('Waiting for build to finish...')
  await waitForBuildFinish(templateID, template.buildID, name, false)

  process.exit(0)
}

// 自定义构建流程
async function customBuildFlow(
  templateID: string | undefined,
  opts: BuildOptions,
  context: BuildContext,
) {
  console.log(`🎯 Starting custom sandbox template build for platform: ${getArchDisplayName(context.archString)}...`)

 // const accessToken = ensureAccessToken()
  process.stdout.write('\n')

  const newName = opts.name?.trim()
  if (newName && !/[a-z0-9-_]+/.test(newName)) {
    console.error(
      `Name ${asLocal(
        newName
      )} is not valid. Name can only contain lowercase letters, numbers, dashes and underscores.`
    )
    process.exit(1)
  }
  let dockerfile = opts.dockerfile
  let startCmd = opts.cmd
  let cpuCount = opts.cpuCount
  let memoryMB = opts.memoryMb
  let teamID = opts.team

  if (context.config) {
    console.log(
      `🎯 Found custom sandbox template ${asFormattedSandboxTemplate(
        {
          templateID: context.config.template_id,
          aliases: context.config.template_name
            ? [context.config.template_name]
            : undefined,
        },
        context.relativeConfigPath
      )}`
    )
    dockerfile = opts.dockerfile || context.config.dockerfile
    templateID = context.config.template_id
    startCmd = opts.cmd || context.config.start_cmd
    cpuCount = opts.cpuCount || context.config.cpu_count
    memoryMB = opts.memoryMb || context.config.memory_mb
    teamID = opts.team || context.config.team_id
  } else {
    console.log(`🎯 Detected target platform: ${getArchDisplayName(context.archString)}`)
  }

  const userConfig = getUserConfig()
  if (userConfig) {
    teamID = teamID || userConfig.teamId
  }

  if (context.config && templateID && context.config.template_id !== templateID) {
    console.error(
      "You can't specify different ID than the one in config. If you want to build a new sandbox template remove the config file."
    )
    process.exit(1)
  }

  if (
    newName &&
    context.config?.template_name &&
    newName !== context.config?.template_name
  ) {
    console.log(
      `🎯 The custom template name will be changed from ${asLocal(
        context.config.template_name
      )} to ${asLocal(newName)}.`
    )
  }
  const name = newName || context.config?.template_name

  // 自定义构建的特殊处理
  console.log('🎯 Applying custom build configurations...')

  const { dockerfileContent, dockerfileRelativePath } = getDockerfile(
    context.root,
    dockerfile
  )
  
  const envType = parseArchToEnvType(context.archString)
  
  const body = {
    alias: name,
    startCmd: startCmd,
    cpuCount: cpuCount,
    memoryMB: memoryMB,
    dockerfile: dockerfileContent,
    teamID: teamID,
    envType: envType
  }

  if (opts.memoryMb) {
    if (opts.memoryMb % 2 !== 0) {
      console.error(
        `The memory in megabytes must be an even number. You provided ${asLocal(
          opts.memoryMb.toFixed(0)
        )}.`
      )
      process.exit(1)
    }
  }

  const template = await requestBuildTemplate(body, templateID)
  templateID = template.templateID

  console.log(
    `🎯 Requested custom build for the sandbox template ${asFormattedSandboxTemplate(
      template
    )} `
  )

  await saveConfig(
    context.configPath,
    {
      template_id: template.templateID,
      dockerfile: dockerfileRelativePath, 
      template_name: name,
      start_cmd: startCmd,
      cpu_count: cpuCount,
      memory_mb: memoryMB,
      team_id: teamID,
      platform: context.archString,
    },
    true
  )

   // 打包用户指定的目录，并请求到一个可上传打包数据的地址，然后上传打包数据
  const zipFilePath = path.join(context.root, './resource.zip')
  try {
    await zipDirectory(context.root, zipFilePath)
    console.log('Zipping completed.')
  } catch (error) {
    console.error('An error occurred during zipping:', error)
  }

  console.log('🎯 Uploading custom resource.......')
  await resourceUpload(template.templateID, template.buildID, zipFilePath)
  console.log('🎯 Uploading custom resource finish')

  
  console.log('🎯 Triggering custom build...')
  await triggerBuild(templateID, template.buildID)

  console.log(
    `🎯 Triggered custom build for the sandbox template ${asFormattedSandboxTemplate(
      template
    )} with build ID: ${template.buildID}`
  )

  console.log('🎯 Waiting for custom build to finish...')
  await customWaitForBuildFinish(templateID, template.buildID, name)

  process.exit(0)
}

async function waitForBuildFinish(
  templateID: string,
  buildID: string,
  name?: string,
  isCustom?: boolean
) {
  let logsOffset = 0

  let template: Awaited<ReturnType<typeof getTemplateBuildLogs>> | undefined
  const aliases = name ? [name] : undefined

  process.stdout.write('\n')
  do {
    await wait(templateCheckInterval)

    template = await getTemplateBuildLogs({
      templateID,
      logsOffset,
      buildID,
    })

    logsOffset += template.logs.length

    switch (template.status) {
      case 'building':
        
        process.stdout.write(asBuildLogs(template.logs))
        
        break
      case 'ready': {
        const pythonExample = asPython(`from agentbox import Sandbox, AsyncSandbox

# Create sync sandbox
sandbox = Sandbox("${aliases?.length ? aliases[0] : template.templateID}")

# Create async sandbox
sandbox = await AsyncSandbox.create("${
          aliases?.length ? aliases[0] : template.templateID
        }")`)

        const typescriptExample = asTypescript(`import { Sandbox } from 'agentbox'

// Create sandbox
const sandbox = await Sandbox.create('${
          aliases?.length ? aliases[0] : template.templateID
        }')`)

        const examplesMessage = `You can now use the template to create custom sandboxes.\nLearn more on ${asPrimary(
          'https://agentbox.space/docs'
        )}`

        const exampleHeader = boxen(examplesMessage, {
          padding: {
            bottom: 1,
            top: 1,
            left: 2,
            right: 2,
          },
          margin: {
            top: 1,
            bottom: 1,
            left: 0,
            right: 0,
          },
          fullscreen(width) {
            return [width, 0]
          },
          float: 'left',
        })

        const exampleUsage = `${withDelimiter(
          pythonExample,
          'Python SDK'
        )}\n${withDelimiter(typescriptExample, 'JS SDK', true)}`

        const customPrefix = isCustom ? '🎯 Custom ' : ''
        console.log(
          `\n✅ ${customPrefix}Building sandbox template ${asFormattedSandboxTemplate({
            aliases,
            ...template,
          })} finished.\n${exampleHeader}\n${exampleUsage}\n`
        )
        break
      }
      case 'error': {
        process.stdout.write(asBuildLogs(template.logs))
        
        const customPrefix = isCustom ? '🎯 Custom ' : ''
        throw new Error(
          `\n❌ ${customPrefix}Building sandbox template ${asFormattedSandboxTemplate({
            aliases,
            ...template,
          })} failed.\nCheck the logs above for more details or contact us ${asPrimary(
            '(https://agentbox.space/docs/getting-help)'
          )} to get help.\n`
        )
      }
    }
  } while (template.status === 'building')
}

// 自定义构建的等待流程
async function customWaitForBuildFinish(
  templateID: string,
  buildID: string,
  name?: string
) {

  let template: Awaited<ReturnType<typeof getAgentBoxTemplateBuildStatus>> | undefined
  const aliases = name ? [name] : undefined

  process.stdout.write('\n')
  do {
    await wait(templateCheckInterval)

    template = await getAgentBoxTemplateBuildStatus({
      templateID,
      buildID,
    })

    switch (template.status) {
      case 'building':
        process.stdout.write(asBuildLogs(template.logs))
        
        break
      case 'ready': {
        
        // console.log(
        //   `\n✅ 🎯 Custom sandbox template ${asFormattedSandboxTemplate({
        //     aliases,
        //     ...template,
        //   })} finished building successfully!\n`
        // )
        console.log('\n✅ 🎯 Custom sandbox template finished building successfully!')
        break
      }
      case 'error': {
        throw new Error(
          `\n❌ 🎯 Custom sandbox template ${asFormattedSandboxTemplate({
            aliases,
            ...template,
          })}\n build logs: \n ${template.logs} \n`
        )
      }
    }
  } while (template.status === 'building')
}

function loadFile(filePath: string) {
  if (!fs.existsSync(filePath)) {
    return undefined
  }

  return fs.readFileSync(filePath, 'utf-8')
}

function getDockerfile(root: string, file?: string) {
  // Check if user specified custom Dockerfile exists
  if (file) {
    const dockerfilePath = path.join(root, file)
    const dockerfileContent = loadFile(dockerfilePath)
    const dockerfileRelativePath = path.relative(root, dockerfilePath)

    if (dockerfileContent === undefined) {
      throw new Error(
        `No ${asLocalRelative(
          dockerfileRelativePath
        )} found in the root directory.`
      )
    }

    return {
      dockerfilePath,
      dockerfileContent,
      dockerfileRelativePath,
    }
  }

  // Check if default dockerfile e2b.Dockerfile exists
  let dockerfilePath = path.join(root, defaultDockerfileName)
  let dockerfileContent = loadFile(dockerfilePath)
  const defaultDockerfileRelativePath = path.relative(root, dockerfilePath)
  let dockerfileRelativePath = defaultDockerfileRelativePath

  if (dockerfileContent !== undefined) {
    return {
      dockerfilePath,
      dockerfileContent,
      dockerfileRelativePath,
    }
  }

  // Check if fallback Dockerfile exists
  dockerfilePath = path.join(root, fallbackDockerfileName)
  dockerfileContent = loadFile(dockerfilePath)
  const fallbackDockerfileRelativeName = path.relative(root, dockerfilePath)
  dockerfileRelativePath = fallbackDockerfileRelativeName

  if (dockerfileContent !== undefined) {
    return {
      dockerfilePath,
      dockerfileContent,
      dockerfileRelativePath,
    }
  }

  throw new Error(
    `No ${asLocalRelative(defaultDockerfileRelativePath)} or ${asLocalRelative(
      fallbackDockerfileRelativeName
    )} found in the root directory (${root}). You can specify a custom Dockerfile with ${asBold(
      '--dockerfile <file>'
    )} option.`
  )
}

async function requestBuildTemplate(
  args: e2b.paths['/templates']['post']['requestBody']['content']['application/json'],
  templateID?: string
): Promise<
  Omit<
    e2b.paths['/templates']['post']['responses']['202']['content']['application/json'],
    'logs'
  >
> {
  let res
  if (templateID) {
    res = await requestTemplateRebuild(templateID, args)
  } else {
    res = await requestTemplateBuild(args)
  }

  handleE2BRequestError(res, 'Error requesting template build')
  return res.data as Omit<
    e2b.paths['/templates']['post']['responses']['202']['content']['application/json'],
    'logs'
  >
}

async function triggerBuild(templateID: string, buildID: string) {
  await triggerTemplateBuild(templateID, buildID)

  return
}

async function resourceUpload(templateID: string, buildID: string, zipFilePath: string) {
  await resourceZipUpload(templateID, buildID, zipFilePath)
  return 
}

/**
 * 将指定目录打包成 ZIP 文件
 * @param sourceDir 要打包的目录路径，例如 './my-folder'
 * @param outPath 输出的 ZIP 文件路径，例如 './my-folder.zip'
 * @returns Promise<void>，在打包完成时 resolve
 */
// 导出 AgentBox 相关函数
export { getAgentBoxTemplateBuildStatus }

export function zipDirectory(sourceDir: string, outPath: string): Promise<void> {
  // 确保源目录存在
  if (!fs.existsSync(sourceDir)) {
    throw new Error(`Source directory "${sourceDir}" does not exist.`)
  }

  console.log(`🎯 Starting to create zip archive from: ${sourceDir}`)

  // 创建一个文件写入流来存储 ZIP 文件
  const output = fs.createWriteStream(outPath)
  
  // 创建一个 archiver 实例，指定格式为 'zip'
  // 降低压缩级别以提高速度
  const archive = archiver('zip', {
    zlib: { level: 6 } // 平衡压缩比和速度
  })

  // 排除的文件和目录模式
  const excludePatterns = [
    'node_modules/**',
    '.git/**',
    'dist/**',
    'build/**',
    '.next/**',
    'coverage/**',
    '.nyc_output/**',
    'tmp/**',
    'temp/**',
    '.DS_Store',
    'Thumbs.db',
    '*.log',
    '*.tmp',
    '*.cache',
    '.env',
    '.env.local',
    '.env.*.local',
    'resource.zip', // 排除输出文件本身
    '**/*.zip',
    '**/*.tar.gz',
    '**/*.tar'
  ]

  return new Promise((resolve, reject) => {
    // 设置超时机制 (10 分钟)
    const timeout = setTimeout(() => {
      reject(new Error('ZIP creation timed out after 10 minutes'))
    }, 10 * 60 * 1000)

    let progressInterval: NodeJS.Timeout | null = null
    let lastSize = 0

    // 监听 'close' 事件，当 archiver 完成写入时触发
    output.on('close', () => {
      clearTimeout(timeout)
      if (progressInterval) {
        clearInterval(progressInterval)
      }
      
      const totalBytes = archive.pointer()
      const totalMB = (totalBytes / (1024 * 1024)).toFixed(2)
      
      console.log(`🎯 Successfully created zip archive: ${outPath}`)
      console.log(`🎯 Total size: ${totalMB} MB (${totalBytes} bytes)`)
      resolve()
    })

    // 监听 'error' 事件，处理 archiver 自身的错误
    archive.on('error', (err: Error) => {
      clearTimeout(timeout)
      if (progressInterval) {
        clearInterval(progressInterval)
      }
      reject(err)
    })
    
    // 监听写入流的 'error' 事件
    output.on('error', (err) => {
      clearTimeout(timeout)
      if (progressInterval) {
        clearInterval(progressInterval)
      }
      reject(err)
    })

    // // 监听数据写入进度
    // archive.on('progress', (data) => {
    //   console.log(`🎯 Compressing... ${data.entries} files processed`)
    // })

    // 设置进度显示
    progressInterval = setInterval(() => {
      const currentSize = archive.pointer()
      if (currentSize > lastSize) {
        const currentMB = (currentSize / (1024 * 1024)).toFixed(2)
        console.log(`🎯 Compressing... ${currentMB} MB written`)
        lastSize = currentSize
      }
    }, 3000) // 每3秒显示一次进度

    // 将 archiver 的输出流管道连接到文件写入流
    archive.pipe(output)

    // 将指定目录添加到归档中，排除不必要的文件
    archive.directory(sourceDir, false, (entry) => {
      // 检查是否应该排除这个文件/目录
      const relativePath = path.relative(sourceDir, entry.name)
      
      for (const pattern of excludePatterns) {
        if (minimatch(relativePath, pattern)) {
         // console.log(`🎯 Excluding: ${relativePath}`)
          return false
        }
      }
      
      return entry
    })

    console.log(`🎯 Adding files to archive (excluding: ${excludePatterns.join(', ')})`)

    // 完成归档（这会写入所有数据并关闭流）
    archive.finalize()
  })
}
