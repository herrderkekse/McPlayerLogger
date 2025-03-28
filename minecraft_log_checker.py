import paramiko
from typing import Optional
from config import SSH_CONFIG


def check_minecraft_logs() -> Optional[str]:
    """
    Connect to server via SSH and check Minecraft logs for player join/leave events

    Returns:
        String containing log output or None if error occurs
    """
    try:
        # Setup SSH client
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        # Connect using SSH key
        ssh.connect(
            hostname=SSH_CONFIG["hostname"],
            username=SSH_CONFIG["username"],
            key_filename=SSH_CONFIG["key_path"],
            port=SSH_CONFIG["port"]
        )

        # Command to execute
        command = 'grep -E "joined the game|left the game" minecraft-server/minecraft-data/logs/*.log && zgrep -E "joined the game|left the game" minecraft-server/minecraft-data/logs/*.gz'

        # Execute command
        stdin, stdout, stderr = ssh.exec_command(command)

        # Get output
        output = stdout.read().decode('utf-8')
        errors = stderr.read().decode('utf-8')

        # Close connection
        ssh.close()

        # Check for errors (note: if first part of command fails, it's ok due to &&)
        if errors and "No such file or directory" not in errors:
            print(f"Errors encountered: {errors}")
            return None

        return output

    except Exception as e:
        print(f"Error: {str(e)}")
        return None


# Example usage
if __name__ == "__main__":
    result = check_minecraft_logs()
    if result:
        print(result)
