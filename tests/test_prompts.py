import pytest

from src.rag.prompts import (
    ACTIVE_VERSION,
    get_prompt,
    get_active_prompt,
    list_versions,
    get_language_name,
)


def test_get_prompt_returns_active_by_default():
    prompt = get_prompt()
    assert prompt["version"] == ACTIVE_VERSION
    assert "system" in prompt
    assert "human" in prompt
    assert "date" in prompt


def test_get_prompt_invalid_version_raises():
    with pytest.raises(ValueError):
        get_prompt("9.9.9")


def test_get_active_prompt_matches_default():
    assert get_active_prompt()["version"] == get_prompt()["version"]


def test_list_versions_contains_active():
    versions = list_versions()
    active_entries = [v for v in versions if v["is_active"]]
    assert len(active_entries) == 1
    assert active_entries[0]["version"] == ACTIVE_VERSION


def test_get_language_name_known_and_unknown():
    assert get_language_name("en") == "English"
    assert get_language_name("xx") == "XX"
