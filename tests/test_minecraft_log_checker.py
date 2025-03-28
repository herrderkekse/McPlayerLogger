from minecraft_log_checker.minecraft_log_checker import (
    parse_log_line,
    calculate_player_statistics,
    format_timedelta
)
import pytest
from datetime import datetime, timedelta
from collections import defaultdict
import sys
from pathlib import Path

# Add the test directory to the Python path
test_dir = Path(__file__).parent
sys.path.insert(0, str(test_dir))


@pytest.fixture
def sample_log_lines():
    return [
        "2025-03-23-1.log:[12:00:00] [Server thread/INFO]: PlayerOne joined the game",
        "2025-03-23-1.log:[12:30:00] [Server thread/INFO]: PlayerOne left the game",
        "2025-03-23-1.log:[13:00:00] [Server thread/INFO]: PlayerTwo joined the game",
        # Format without log file
        "[14:00:00] [Server thread/INFO]: PlayerTwo left the game",
        "invalid line format",
        "2025-03-23-1.log:[15:00:00] [Server thread/INFO]: PlayerOne joined the game",
    ]


@pytest.fixture
def sample_player_sessions():
    sessions = defaultdict(list)

    # PlayerOne: Two sessions
    sessions["PlayerOne"].extend([
        (datetime(2025, 3, 23, 12, 0), "joined"),
        (datetime(2025, 3, 23, 12, 30), "left"),
        (datetime(2025, 3, 23, 15, 0), "joined"),
        (datetime(2025, 3, 23, 16, 0), "left"),
    ])

    # PlayerTwo: One session
    sessions["PlayerTwo"].extend([
        (datetime(2025, 3, 23, 13, 0), "joined"),
        (datetime(2025, 3, 23, 14, 0), "left"),
    ])

    return sessions


def test_parse_log_line_with_log_file():
    line = "2025-03-23-1.log:[12:00:00] [Server thread/INFO]: PlayerOne joined the game"
    timestamp, player, action = parse_log_line(line)

    assert isinstance(timestamp, datetime)
    assert timestamp == datetime(2025, 3, 23, 12, 0)
    assert player == "PlayerOne"
    assert action == "joined"


def test_parse_log_line_without_log_file():
    line = "[14:00:00] [Server thread/INFO]: PlayerTwo left the game"
    timestamp, player, action = parse_log_line(line)

    assert isinstance(timestamp, datetime)
    assert timestamp.hour == 14
    assert timestamp.minute == 0
    assert player == "PlayerTwo"
    assert action == "left"


def test_parse_log_line_invalid_format():
    with pytest.raises(ValueError):
        parse_log_line("invalid line format")


def test_calculate_player_statistics(sample_player_sessions):
    stats = calculate_player_statistics(sample_player_sessions)

    # Test PlayerOne stats
    assert stats["PlayerOne"]["total_sessions"] == 2
    assert stats["PlayerOne"]["total_time"] == timedelta(hours=1, minutes=30)
    assert stats["PlayerOne"]["average_session"] == timedelta(minutes=45)
    assert stats["PlayerOne"]["min_session"] == timedelta(minutes=30)
    assert stats["PlayerOne"]["max_session"] == timedelta(hours=1)
    assert isinstance(stats["PlayerOne"]["session_stddev"], timedelta)

    # Test PlayerTwo stats
    assert stats["PlayerTwo"]["total_sessions"] == 1
    assert stats["PlayerTwo"]["total_time"] == timedelta(hours=1)
    assert stats["PlayerTwo"]["average_session"] == timedelta(hours=1)
    assert stats["PlayerTwo"]["min_session"] == timedelta(hours=1)
    assert stats["PlayerTwo"]["max_session"] == timedelta(hours=1)
    assert stats["PlayerTwo"]["session_stddev"] == timedelta(0)


def test_format_timedelta():
    # Test hours and minutes
    td = timedelta(hours=2, minutes=30)
    assert format_timedelta(td) == "2h 30m"

    # Test minutes only
    td = timedelta(minutes=45)
    assert format_timedelta(td) == "45m"

    # Test zero duration
    td = timedelta(0)
    assert format_timedelta(td) == "0m"


@pytest.mark.parametrize("line,expected", [
    (
        "2025-03-23-1.log:[12:00:00] [Server thread/INFO]: PlayerOne joined the game",
        (datetime(2025, 3, 23, 12, 0), "PlayerOne", "joined")
    ),
    (
        "[14:00:00] [Server thread/INFO]: PlayerTwo left the game",
        (None, "PlayerTwo", "left")  # datetime will be current date
    ),
])
def test_parse_log_line_parametrized(line, expected):
    timestamp, player, action = parse_log_line(line)

    if expected[0] is not None:
        assert timestamp == expected[0]
    assert player == expected[1]
    assert action == expected[2]


def test_empty_player_sessions():
    stats = calculate_player_statistics({})
    assert stats == {}


def test_single_session_without_logout(sample_player_sessions):
    # Add a session without logout
    sample_player_sessions["PlayerThree"].append(
        (datetime(2025, 3, 23, 17, 0), "joined")
    )

    stats = calculate_player_statistics(sample_player_sessions)
    assert "PlayerThree" in stats
    assert stats["PlayerThree"]["total_sessions"] == 1
