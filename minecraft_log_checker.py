import paramiko
from typing import Optional, Dict, List, Tuple
import re
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np
from collections import defaultdict
import os
from config import SSH_CONFIG, VIZ_CONFIG
from statistics import mean, stdev


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


def calculate_player_statistics(player_sessions: Dict[str, List[Tuple[datetime, str]]]) -> Dict[str, Dict]:
    """
    Calculate statistics for each player's sessions

    Args:
        player_sessions: Dictionary of player sessions with timestamps and actions

    Returns:
        Dictionary containing statistics for each player
    """
    stats = {}

    for player, sessions in player_sessions.items():
        # Sort sessions by timestamp
        sessions.sort(key=lambda x: x[0])

        # Calculate session durations
        durations = []
        join_time = None
        total_time = timedelta()
        session_count = 0

        for timestamp, action in sessions:
            if action == 'joined':
                join_time = timestamp
            elif action == 'left' and join_time is not None:
                duration = timestamp - join_time
                durations.append(duration)
                total_time += duration
                session_count += 1
                join_time = None

        # Handle case where player hasn't logged out
        if join_time is not None:
            duration = sessions[-1][0] - join_time
            durations.append(duration)
            total_time += duration
            session_count += 1

        # Calculate statistics
        stats[player] = {
            'total_sessions': session_count,
            'total_time': total_time,
            'average_session': total_time / session_count if session_count > 0 else timedelta(0),
            'min_session': min(durations) if durations else timedelta(0),
            'max_session': max(durations) if durations else timedelta(0),
        }

        # Calculate standard deviation if we have more than one session
        if len(durations) > 1:
            duration_seconds = [d.total_seconds() for d in durations]
            stats[player]['session_stddev'] = timedelta(
                seconds=stdev(duration_seconds))
        else:
            stats[player]['session_stddev'] = timedelta(0)

    return stats


def format_timedelta(td: timedelta) -> str:
    """Format timedelta in a human-readable format"""
    total_seconds = int(td.total_seconds())
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    if hours > 0:
        return f"{hours}h {minutes}m"
    return f"{minutes}m"


def print_player_statistics(stats: Dict[str, Dict]):
    """Print player statistics in a formatted table"""
    print("\nPlayer Statistics:")
    print("-" * 100)
    print(f"{'Player':<20} {'Sessions':<10} {'Total Time':<15} {'Avg Session':<15} "
          f"{'Min Session':<15} {'Max Session':<15} {'Std Dev':<15}")
    print("-" * 100)

    for player, player_stats in sorted(stats.items()):
        print(
            f"{player:<20} "
            f"{player_stats['total_sessions']:<10} "
            f"{format_timedelta(player_stats['total_time']):<15} "
            f"{format_timedelta(player_stats['average_session']):<15} "
            f"{format_timedelta(player_stats['min_session']):<15} "
            f"{format_timedelta(player_stats['max_session']):<15} "
            f"{format_timedelta(player_stats['session_stddev']):<15}"
        )
    print("-" * 100)


def visualize_player_sessions(start_date: str = None, end_date: str = None, output_path: str = None):
    """
    Fetch logs and create a visual timeline of player sessions within a date range

    Args:
        start_date: Optional start date in 'YYYY-MM-DD' format (overrides config)
        end_date: Optional end date in 'YYYY-MM-DD' format (overrides config)
        output_path: Optional full path for output file (overrides config)
    """
    # Use provided parameters or fall back to config values
    start_date = start_date or VIZ_CONFIG.get('start_date')
    end_date = end_date or VIZ_CONFIG.get('end_date')
    output_path = output_path or VIZ_CONFIG.get(
        'output_path', 'output/minecraft_sessions.png')

    # Ensure output directory exists
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    log_data = check_minecraft_logs()
    if not log_data:
        print("No log data available")
        return

    print("Processing log data...", flush=True)
    # Convert date strings to datetime objects if provided
    start_datetime = None
    end_datetime = None
    if start_date:
        start_datetime = datetime.strptime(start_date, '%Y-%m-%d')
    if end_date:
        end_datetime = datetime.strptime(
            end_date, '%Y-%m-%d') + timedelta(days=1)  # Include the entire end date

    # Process log lines
    player_sessions = defaultdict(list)

    for line in log_data.strip().split('\n'):
        try:
            timestamp, player, action = parse_log_line(line)

            # Skip if outside the specified date range
            if start_datetime and timestamp < start_datetime:
                continue
            if end_datetime and timestamp > end_datetime:
                continue

            player_sessions[player].append((timestamp, action))
        except ValueError as e:
            print(f"Error processing line: {e}")
            continue

    if not player_sessions:
        print("No valid sessions found in the specified date range")
        return

    # Calculate and display statistics
    print("\nCalculating player statistics...", flush=True)
    stats = calculate_player_statistics(player_sessions)
    print_player_statistics(stats)

    # Create visualization
    print("\nGenerating visualization...", flush=True)
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
    title = 'Minecraft Server Player Sessions'
    if start_date or end_date:
        date_range = f" ({start_date or 'start'} to {end_date or 'end'})"
        title += date_range
    plt.title(title)

    # Format x-axis
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d %H:%M'))
    plt.gcf().autofmt_xdate()  # Rotate and align the tick labels

    # Add grid
    plt.grid(True, axis='x', alpha=0.3)

    # Adjust layout
    plt.tight_layout()

    print("Generating visualization...", flush=True)
    # Save the plot
    plt.savefig(output_path)
    print(f"Plot saved as '{output_path}'")


def check_minecraft_logs() -> Optional[str]:
    """
    Connect to server via SSH and check Minecraft logs for player join/leave events

    Returns:
        String containing log output or None if error occurs
    """
    try:
        print("Connecting to server...", flush=True)
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

        print("Fetching log data...", flush=True)
        # Command to execute
        command = 'grep -E "joined the game|left the game" minecraft-server/minecraft-data/logs/*.log && zgrep -E "joined the game|left the game" minecraft-server/minecraft-data/logs/*.gz'

        # Execute command
        stdin, stdout, stderr = ssh.exec_command(command)

        # Get output
        output = stdout.read().decode('utf-8')
        errors = stderr.read().decode('utf-8')

        # Close connection
        ssh.close()
        print("Data fetching complete.", flush=True)

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
    # Example usage:
    # Use config defaults:
    visualize_player_sessions()

    # Override config values:
    # visualize_player_sessions(
    #     start_date="2025-03-23",
    #     end_date="2025-03-25",
    #     output_path="custom_output/player_activity.png"
    # )
