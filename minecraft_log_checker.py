import paramiko
from typing import Optional
import re
from datetime import datetime
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np
from collections import defaultdict
from config import SSH_CONFIG


def parse_log_line(line: str) -> tuple[datetime, str, str]:
    """Parse a log line and return datetime, player name, and action"""
    # Try the format with file name prefix
    pattern1 = r'([^:]+):\[(\d{2}:\d{2}:\d{2})\].*?: (\w+) (joined|left) the game'
    # Try the format without file name prefix
    pattern2 = r'\[(\d{2}:\d{2}:\d{2})\].*?: (\w+) (joined|left) the game'

    match = re.match(pattern1, line)
    if match:
        log_file, time_str, player, action = match.groups()
        # Extract date from log file name
        date_match = re.search(r'(\d{4}-\d{2}-\d{2})', log_file)
        if not date_match:
            raise ValueError(f"Cannot extract date from log file: {log_file}")
        date_str = date_match.group(1)
    else:
        match = re.match(pattern2, line)
        if not match:
            raise ValueError(f"Invalid log line format: {line}")
        time_str, player, action = match.groups()
        # Use current date if no date in log file
        date_str = datetime.now().strftime('%Y-%m-%d')

    datetime_str = f"{date_str} {time_str}"
    timestamp = datetime.strptime(datetime_str, '%Y-%m-%d %H:%M:%S')

    return timestamp, player, action


def visualize_player_sessions():
    """Fetch logs and create a visual timeline of player sessions"""
    log_data = check_minecraft_logs()
    if not log_data:
        print("No log data available")
        return

    # Process log lines
    player_sessions = defaultdict(list)

    for line in log_data.strip().split('\n'):
        try:
            timestamp, player, action = parse_log_line(line)
            player_sessions[player].append((timestamp, action))
        except ValueError as e:
            print(f"Error processing line: {e}")
            continue

    if not player_sessions:
        print("No valid sessions found")
        return

    # Create visualization
    plt.figure(figsize=(15, 8))

    # Plot each player's sessions
    colors = plt.cm.Set3(np.linspace(0, 1, len(player_sessions)))
    for (player, sessions), color in zip(player_sessions.items(), colors):
        y_position = list(player_sessions.keys()).index(player)

        # Sort sessions by timestamp
        sessions.sort(key=lambda x: x[0])

        # Create session blocks
        join_time = None
        for timestamp, action in sessions:
            if action == 'joined':
                join_time = timestamp
            elif action == 'left' and join_time is not None:
                plt.hlines(y_position, join_time, timestamp,
                           color=color, linewidth=10)
                join_time = None

        # Handle case where player hasn't logged out
        if join_time is not None:
            plt.hlines(y_position, join_time, timestamp,
                       color=color, linewidth=10)

    # Customize the plot
    plt.yticks(range(len(player_sessions)), list(player_sessions.keys()))
    plt.xlabel('Time')
    plt.ylabel('Players')
    plt.title('Minecraft Server Player Sessions')

    # Format x-axis
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d %H:%M'))
    plt.gcf().autofmt_xdate()  # Rotate and align the tick labels

    # Add grid
    plt.grid(True, axis='x', alpha=0.3)

    # Adjust layout
    plt.tight_layout()

    # Save the plot instead of showing it
    plt.savefig('minecraft_sessions.png')
    print("Plot saved as 'minecraft_sessions.png'")


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
    visualize_player_sessions()
