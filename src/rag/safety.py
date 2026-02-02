"""Safety helpers for prompt-injection checks."""

TRIGGERS = [
    "ignore instructions",
    "ignore your instructions",
    "ignore all instructions",
    "forget instructions",
    "forget previous instructions",
    "ignore previous",
    "disregard previous",
    "system prompt",
    "developer message",
    "jailbreak",
    "bypass safety",
    "override instructions",
]


def is_prompt_injection(text: str) -> bool:
    if not text:
        return False
    lowered = text.lower()
    return any(t in lowered for t in TRIGGERS)


def is_prompt_injection_in_history(history) -> bool:
    if not isinstance(history, list):
        return False
    for item in history:
        content = item.get("content") if isinstance(item, dict) else None
        if content and is_prompt_injection(content):
            return True
    return False
