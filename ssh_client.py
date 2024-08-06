import paramiko
from scp import SCPClient
import tenacity

@tenacity.retry(
    stop=tenacity.stop_after_attempt(3),
    wait=tenacity.wait_fixed(2),
    retry=tenacity.retry_if_exception_type(Exception)
)
def create_ssh_client(server, user, key_file):
    ssh = paramiko.SSHClient()
    ssh.load_system_host_keys()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(server, username=user, key_filename=key_file)
    return ssh

class SshClient:
    def __init__(self, server, user, key_file):
        self.server = server
        self.user = user
        self.key_file = key_file
        self.ssh = create_ssh_client(server, user, key_file)

    @tenacity.retry(
        stop=tenacity.stop_after_attempt(3),
        wait=tenacity.wait_fixed(2),
        retry=tenacity.retry_if_exception_type(Exception)
    )
    def download_file(self, remote_path, local_path):
        with SCPClient(self.ssh.get_transport()) as scp:
            scp.get(remote_path, local_path, recursive=True)

    @tenacity.retry(
        stop=tenacity.stop_after_attempt(3),
        wait=tenacity.wait_fixed(2),
        retry=tenacity.retry_if_exception_type(Exception)
    )
    def upload_file(self, local_path, remote_path, is_folder=False):
        with SCPClient(self.ssh.get_transport()) as scp:
            scp.put(local_path, remote_path, recursive=is_folder)

    def execute(self, command):
        stdin, stdout, stderr = self.ssh.exec_command(command)
        output = stdout.readlines()
        error = stderr.readlines()
        return output, error