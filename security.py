"""
Security module for Mini-Assignment 6: Security & Ethics Integration.
"""

from __future__ import annotations

import json
import re
import time
from collections import defaultdict
from typing import Any, Callable


class InputValidator:
    """Validate and sanitize user input before model execution."""

    def __init__(self, max_length: int = 1000) -> None:
        self.max_length = max_length
        self.suspicious_patterns = [
            re.compile(r"<\s*script.*?>.*?<\s*/\s*script\s*>", re.IGNORECASE | re.DOTALL),
            re.compile(r"<\s*iframe.*?>.*?<\s*/\s*iframe\s*>", re.IGNORECASE | re.DOTALL),
            re.compile(r"\b(select|union|drop|delete|insert|update)\b", re.IGNORECASE),
            re.compile(r"(;|\|\||&&|\|)"),
            re.compile(r"\b(eval|exec)\s*\(", re.IGNORECASE),
        ]

    def sanitize(self, input_text: str) -> str:
        """Return a cleaned version of the input."""
        cleaned = re.sub(r"[\x00-\x1f\x7f]", "", input_text)
        cleaned = re.sub(
            r"<\s*script.*?>.*?<\s*/\s*script\s*>",
            "[script removed]",
            cleaned,
            flags=re.IGNORECASE | re.DOTALL,
        )
        cleaned = re.sub(
            r"<\s*iframe.*?>.*?<\s*/\s*iframe\s*>",
            "[iframe removed]",
            cleaned,
            flags=re.IGNORECASE | re.DOTALL,
        )
        cleaned = re.sub(r"\s+", " ", cleaned).strip()
        return cleaned

    def validate(self, input_text: str) -> tuple[bool, str, str]:
        """Validate input and return (is_valid, message, sanitized_text)."""
        if not isinstance(input_text, str):
            return False, "Input must be a string.", ""

        sanitized = self.sanitize(input_text)

        if not sanitized:
            return False, "Input cannot be empty.", sanitized

        if len(sanitized) > self.max_length:
            return False, f"Input exceeds {self.max_length} characters.", sanitized

        for pattern in self.suspicious_patterns:
            if pattern.search(input_text):
                return (
                    False,
                    "Input contains suspicious or potentially harmful patterns.",
                    sanitized,
                )

        return True, "Valid input.", sanitized


class RateLimiter:
    """Simple in-memory sliding-window rate limiter."""

    def __init__(self, max_requests: int = 10, window_seconds: int = 60) -> None:
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests: dict[str, list[float]] = defaultdict(list)

    def _cleanup(self, user_id: str) -> None:
        now = time.time()
        self.requests[user_id] = [
            timestamp
            for timestamp in self.requests[user_id]
            if now - timestamp < self.window_seconds
        ]

    def is_allowed(self, user_id: str) -> tuple[bool, str]:
        self._cleanup(user_id)
        now = time.time()

        if len(self.requests[user_id]) >= self.max_requests:
            oldest = min(self.requests[user_id])
            retry_after = max(1, int(self.window_seconds - (now - oldest)) + 1)
            return False, f"Rate limit exceeded. Try again in {retry_after} seconds."

        self.requests[user_id].append(now)
        return True, "Request allowed."

    def reset_user(self, user_id: str) -> None:
        self.requests[user_id] = []


class EthicalGuard:
    """Pattern-based ethical content filter with logging."""

    def __init__(self, log_file: str = "flagged.log") -> None:
        self.log_file = log_file
        self.flagged_history: list[dict[str, Any]] = []
        self.patterns = {
            "violence": [
                re.compile(r"\bkill\b", re.IGNORECASE),
                re.compile(r"\bhurt someone\b", re.IGNORECASE),
                re.compile(r"\battack\b", re.IGNORECASE),
            ],
            "illegal": [
                re.compile(r"\bsteal\b", re.IGNORECASE),
                re.compile(r"\bhack\b", re.IGNORECASE),
                re.compile(r"\bmake a bomb\b", re.IGNORECASE),
            ],
            "hate_or_harassment": [
                re.compile(r"\bhate\b", re.IGNORECASE),
                re.compile(r"\bharass\b", re.IGNORECASE),
            ],
            "self_harm": [
                re.compile(r"\bsuicide\b", re.IGNORECASE),
                re.compile(r"\bself-harm\b", re.IGNORECASE),
                re.compile(r"\bhurt myself\b", re.IGNORECASE),
            ],
        }

    def check(self, input_text: str) -> tuple[bool, str, list[str]]:
        """Check content and return (is_safe, message, flags)."""
        flags: list[str] = []

        for category, patterns in self.patterns.items():
            for pattern in patterns:
                if pattern.search(input_text):
                    flags.append(category)
                    break

        if flags:
            self._log_flagged_content(input_text, flags)
            return (
                False,
                "This request cannot be processed because it violates safety rules.",
                flags,
            )

        return True, "Content is safe.", []

    def _log_flagged_content(self, input_text: str, flags: list[str]) -> None:
        entry = {
            "timestamp": time.time(),
            "input": input_text,
            "flags": flags,
        }
        self.flagged_history.append(entry)

        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")


def secure_process_request(
    user_id: str,
    input_text: str,
    rate_limiter: RateLimiter,
    validator: InputValidator,
    ethical_guard: EthicalGuard,
    model_fn: Callable[[str], str],
) -> dict[str, Any]:
    """Apply validation, rate limiting, ethical checks, then call the model."""
    is_valid, validation_message, sanitized_text = validator.validate(input_text)
    if not is_valid:
        return {
            "success": False,
            "status": "validation_error",
            "message": validation_message,
            "sanitized_input": sanitized_text,
            "response": None,
            "flags": [],
        }

    allowed, rate_message = rate_limiter.is_allowed(user_id)
    if not allowed:
        return {
            "success": False,
            "status": "rate_limited",
            "message": rate_message,
            "sanitized_input": sanitized_text,
            "response": None,
            "flags": [],
        }

    is_safe, ethical_message, flags = ethical_guard.check(sanitized_text)
    if not is_safe:
        return {
            "success": False,
            "status": "blocked",
            "message": ethical_message,
            "sanitized_input": sanitized_text,
            "response": None,
            "flags": flags,
        }

    response = model_fn(sanitized_text)
    return {
        "success": True,
        "status": "ok",
        "message": "Request processed successfully.",
        "sanitized_input": sanitized_text,
        "response": response,
        "flags": [],
    }
