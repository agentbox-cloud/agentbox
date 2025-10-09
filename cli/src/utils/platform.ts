import { arch } from 'os'

export type TargetPlatform = 'android' | 'linux'
export type TargetArch = 'x86' | 'arm64'  // 预备扩容
export type EnvType = 'android' | 'linux_x86' | 'linux_arm64'   
export type BuildType = 'linux/arm64' | 'linux/amd64'

/**
 * 检测当前系统的平台类型
 * 目前支持：Linux, Android(通过环境变量检测)
 */
export function detectTargetPlatform(): TargetPlatform {
  // 首先检查是否在 Android 环境
  if (process.env.ANDROID_DATA || process.env.ANDROID_ROOT) {
    return 'android'
  }
  
  // 默认使用 Linux 平台 (支持 Linux, macOS 开发环境等)
  return 'linux'
}

/**
 * 检测当前系统的架构类型 (预备扩容功能)
 * 将 Node.js 的 arch 映射到目标架构
 */
export function detectTargetArch(): TargetArch {
  const currentArch = arch()
  
  switch (currentArch) {
    case 'x64':
    case 'x32':
      return 'x86'
    case 'arm':
    case 'arm64':
      return 'arm64'
    default:
      // 默认使用 amd64
      return 'x86'
  }
}

/**
 * 生成环境类型字符串，用于请求 API
 * 当前只支持 android 和 linux_x86, linux_arm64 等
 */
export function getEnvType(): EnvType {

  const archString = getArchString()
  
  if (archString === 'android') {
    return 'android'
  }

  if (archString.indexOf('x86') !== -1) {
    return 'linux_x86'
  } else {
    return 'linux_arm64'
  }
}

/**
 * 生成架构描述字符串，用于保存到配置文件
 * 包含完整的平台和架构信息，为将来扩容做准备
 */
export function getArchString(): string {
  const targetPlatform = detectTargetPlatform()
  const targetArch = detectTargetArch()
  
  if (targetPlatform === 'android') {
    return 'android'
  }
  
  // 保存完整信息以备将来使用
  return `linux_${targetArch}`
}

/**
 * 从架构字符串解析出 EnvType
 * 支持新旧格式的兼容性
 */
export function parseArchToEnvType(archString: string): EnvType {
  if (archString === 'android') {
    return 'android'
  }
  
  if (archString === 'linux_x86') {
    return 'linux_x86'
  }
  
  if (archString === 'linux_arm64') {
    return 'linux_arm64'
  }
  
  // 兼容旧格式或未知格式，默认使用当前环境
  return getEnvType()
}

export function parseArchToBuildType(archString: EnvType): BuildType {
  switch (archString) {
    case 'linux_x86':
      return 'linux/amd64'
    case 'linux_arm64':
      return 'linux/arm64'
    case 'android':
      throw new Error('Android platform should use customBuildFlow, not standardBuildFlow')
    default:
      throw new Error(`Unsupported architecture: ${archString}`)
  }
}

/**
 * 获取架构的显示名称，用于日志输出
 */
export function getArchDisplayName(archString?: string): string {
  if (!archString) {
    archString = getArchString()
  }
  
  if (archString === 'android') {
    return 'Android'
  }
  
  if (archString.startsWith('linux_')) {
    const arch = archString.split('_')[1]
    return `Linux ${arch.toUpperCase()}`
  }
  
  return archString
}