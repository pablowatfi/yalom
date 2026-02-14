from src.ingestion.local_loader import extract_episode_number


def test_extract_episode_number_parses_valid_filename():
    assert extract_episode_number("Episode-123.txt") == 123


def test_extract_episode_number_returns_none_for_invalid_filename():
    assert extract_episode_number("random.txt") is None
