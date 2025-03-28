# Minecraft Log Checker

A Python tool that visualizes player activity on your Minecraft server by analyzing log files. It creates timeline visualizations showing when players were online and provides detailed statistics about player sessions.

## Features

- SSH connection to remote Minecraft servers
- Analysis of player join/leave events
- Visual timeline of player sessions
- Detailed statistics including:
  - Total sessions per player
  - Total play time
  - Average session duration
  - Minimum/maximum session lengths
  - Session duration standard deviation
- Configurable date ranges for analysis
- Customizable output paths for visualizations

## Installation

1. Clone the repository:
```bash
git clone https://github.com/herrderkekse/McPlayerLogger.git
cd McPlayerLogger
```

2. Create and activate a virtual environment (recommended):
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install the package:
```bash
pip install -e .
```

## Configuration

1. Create a `config.py` file from the template:
```bash
cp config.template.py config.py
```

2. Edit `config.py` with your server details:
```python
SSH_CONFIG = {
    "hostname": "your.minecraft.server.com",        # Your server hostname/IP
    "username": "your_username",                    # SSH username
    "key_path": "/path/to/your/ssh/key",            # Path to SSH private key
    "port": 22                                      # SSH port (usually 22)
}

VIZ_CONFIG = {
    "start_date": "2024-03-01",                     # Start date or None
    "end_date": "2024-03-25",                       # End date or None
    "output_path": "output/minecraft_sessions.png"  # Output path
}
```

## Usage

Run with default configuration:
```bash
python run.py
```

Or use the module directly with custom parameters:
```python
from minecraft_log_checker import visualize_player_sessions

visualize_player_sessions(
    start_date="2024-03-01",
    end_date="2024-03-25",
    output_path="output/my_minecraft_sessions.png"
)
```

## Output

The tool generates:
1. A PNG visualization showing player sessions over time
2. Printed statistics including:
   - Number of sessions per player
   - Total play time
   - Average session duration
   - Session duration statistics

Example output:
```
Player Statistics:
----------------------------------------------------------------------------------------------------
Player               Sessions   Total Time      Avg Session     Min Session     Max Session     Std Dev
----------------------------------------------------------------------------------------------------
PlayerOne           2          1h 30m         45m             30m             1h              15m
PlayerTwo           1          1h             1h              1h              1h              0m
----------------------------------------------------------------------------------------------------
```

## Development

Install development dependencies:
```bash
pip install -e ".[dev]"
```

Run tests:
```bash
pytest tests/
```

## Requirements

- Python 3.10+
- SSH access to your Minecraft server
- Access to Minecraft server logs
- Required Python packages (installed automatically):
  - paramiko
  - matplotlib
  - numpy
