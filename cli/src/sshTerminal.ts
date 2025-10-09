import * as e2b from 'e2b'
import { Client } from 'ssh2';
import readline from 'readline';

export async function spawnConnectedSSHTerminal(sandbox: e2b.Sandbox) {
  const regex = /ssh\s+-p\s+(\d+)\s+-o\s+([^ ]+)\s+([^\@]+)@([^\s]+)/
  const match = sandbox.connectCommand.match(regex);
  if (match) {
    const sshClient = new Client();
    const sshConfig = {
      host: match[4],
      port: Number(match[1]),
      username: match[3],
      password: sandbox.authPassword,
      options: ['-o', 'StrictHostKeyChecking=no', '-v']
    };
    return new Promise((resolve, reject) => {
        sshClient.on('ready', () => {
          console.log('SSH Connection established.');
          sshClient.shell({ term: 'xterm-color' }, (err, stream) => {
            if (err) {
              console.error('Shell error:', err);
              sshClient.end();
              return;
            }

            // 接收远程输出
            stream.on('data', (data: Buffer) => {
              process.stdout.write(data.toString());
            });

            stream.stderr.on('data', (data: Buffer) => {
              process.stderr.write(data.toString());
            });

            stream.on('close', () => {
              console.log('\nSSH session closed.');
              sshClient.end();
              process.exit(0);
            });

            // 本地输入 => 发送到 SSH
            const rl = readline.createInterface({
              input: process.stdin,
              output: process.stdout,
            });

            rl.on('line', (line) => {
              // stream.write(line.trim() + '\n');
              const input = line.trim();
              stream.write(input + '\n');
              if (input === 'exit') {
                stream.write('\n');
              }
            });

            // Ctrl+C 支持
            rl.on('SIGINT', () => {
              stream.write('\x03'); // Ctrl+C
            });
          });
        }).on('error', (err) => {
          console.error('Connection error:', err);
        }).connect(sshConfig);
    })
  } else {
    console.log('No ssh session found!');
  }
}
