import * as listen from 'async-listen'
import * as commander from 'commander'
import * as fs from 'fs'
import * as http from 'http'
import * as open from 'open'
import * as path from 'path'
import * as readline from 'readline'

import { pkg } from 'src'
import {
  DOCS_BASE,
  getUserConfig,
  USER_CONFIG_PATH,
  UserConfig,
} from 'src/user'
import { asBold, asFormattedConfig, asFormattedError } from 'src/utils/format'
import { client, connectionConfig } from 'src/api'
import { handleE2BRequestError } from '../../utils/errors'

export const loginCommand = new commander.Command('login')
  .description('log in to CLI')
  .requiredOption('-u, --username <username>', 'email for login')
  .requiredOption('-p, --password <password>', 'password for login')
  .action(async (options) => {
    const { username, password } = options
    const email = username
    let userConfig: UserConfig | null = null

    try {
      userConfig = getUserConfig()
    } catch (err) {
      console.error(asFormattedError('Failed to read user config', err))
    }
    if (userConfig) {
      console.log(
        `\nAlready logged in as ${asBold(userConfig.email)} with team ${asBold(userConfig.teamName)}.\n`
      )
      const shouldOverride = await askUserConfirmation('Do you want to override the current config? (yes/no): ')
      if (!shouldOverride) {
        console.log('Login aborted.')
        return
      }
    }

    console.log('Attempting to log in...')
    try {
      const res = await client.api.POST(
        '/user/cli-sign-in', {
          body: {
            email: email,
            password: password,
          }
        }
      )

      if (!res.response.ok || res.error) {
        console.error('Failed to login:', res.error)
        return
      }

      userConfig = {
        email: res?.data?.email?? 'unknown',
        accessToken: res?.data?.access_token?? 'unknown',
        teamName: res?.data?.team_name?? 'unknown',
        teamId: res?.data?.team_id?? 'unknown',
        teamApiKey: res?.data?.team_api_key?? 'unknown',
      }
      fs.mkdirSync(path.dirname(USER_CONFIG_PATH), { recursive: true })
      fs.writeFileSync(USER_CONFIG_PATH, JSON.stringify(userConfig, null, 2))
      console.log(
        `Logged in as ${asBold(userConfig?.email?? 'Unknown')} with selected team ${asBold(
          userConfig?.teamName??'Unknown'
        )}`
      )
    } catch (error) {
      console.error('Failed to login:', error)
    }
    process.exit(0)
  })

function askUserConfirmation(question: string): Promise<boolean> {
  return new Promise((resolve) => {
    const rl = readline.createInterface({
      input: process.stdin,
      output: process.stdout,
    })

    rl.question(question, (answer) => {
      rl.close()
      resolve(answer.toLowerCase() === 'yes')
    })
  })
}