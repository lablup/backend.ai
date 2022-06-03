import paramiko
import sys
import os
import subprocess

if len(sys.argv) == 1:
    print('Usage: python deploy_static_files.py <Worker Node IPs seperated by space>')
    exit(1)

STATIC_FILE = 'https://backend-ai-k8s-agent-static.s3.ap-northeast-2.amazonaws.com/bai-static.tar.gz'

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

for ip in sys.argv[1:]:
    ssh.connect(ip)

    # Get cwd and username
    stdin, stdout, stderr = ssh.exec_command('pwd')
    pwd = stdout.readlines()[0].strip().replace('\n', '')
    print(f'pwd: {pwd}')
    stdin, stdout, stderr = ssh.exec_command('whoami')
    whoami = stdout.readlines()[0].strip().replace('\n', '')
    print(f'whoami: {whoami}')

    # delete old static files
    stdin, stdout, stderr = ssh.exec_command(f'sudo rm -rf /opt/backend.ai && rm -rf {pwd}/bai*')
 
    print(''.join(stdout.readlines()))

    # Extract to /opt/backend.ai
    stdin, stdout, stderr = ssh.exec_command(f'wget https://backend-ai-k8s-agent-static.s3.ap-northeast-2.amazonaws.com/bai-static.tar.gz && tar xvf {pwd}/bai-static.tar.gz && sudo mv {pwd}/backend.ai /opt && sudo chown {whoami}:{whoami} /opt/backend.ai')
 
    print(''.join(stdout.readlines()))