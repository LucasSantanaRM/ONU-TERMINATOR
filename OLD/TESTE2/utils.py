import paramiko

class SSHConnection:
    def __init__(self, ip, username, password, port=22):
        self.ip = ip
        self.username = username
        self.password = password
        self.port = port
        self.client = None

    def open(self):
        """Open the SSH connection."""
        try:
            self.client = paramiko.SSHClient()
            self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            self.client.connect(self.ip, username=self.username, password=self.password, port=self.port)
            print(f"Connected to {self.ip}")
        except Exception as e:
            print(f"Failed to connect to {self.ip}: {e}")
            raise

    def execute(self, command):
        """Execute a command on the OLT."""
        if self.client:
            stdin, stdout, stderr = self.client.exec_command(command)
            return stdout.read().decode(), stderr.read().decode()
        else:
            raise Exception("Connection not open")

    def close(self):
        """Close the SSH connection."""
        if self.client:
            self.client.close()
            print(f"Connection to {self.ip} closed")
