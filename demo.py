"""
Demo script for Mini-Assignment 6: Security & Ethics Integration.

This script demonstrates:
1. Valid requests
2. Empty input
3. Oversized input
4. Suspicious/injection-like input
5. Harmful content
6. Rate limiting
7. Rate limit reset
"""

import time
from pprint import pprint

from security import InputValidator, RateLimiter, EthicalGuard, secure_process_request


def generate_response(prompt: str) -> str:
    """Mock model function used for the demo."""
    return f"Processed safely: {prompt}"


def print_result(title: str, result: dict) -> None:
    """Pretty-print a scenario result."""
    print(f"\n=== {title} ===")
    pprint(result)


def main() -> None:
    validator = InputValidator(max_length=100)
    ethical_guard = EthicalGuard(log_file="flagged.log")
    rate_limiter = RateLimiter(max_requests=2, window_seconds=5)

    user_id = "demo_user"

    result = secure_process_request(
        user_id=user_id,
        input_text="Explain cross validation in simple terms.",
        rate_limiter=rate_limiter,
        validator=validator,
        ethical_guard=ethical_guard,
        model_fn=generate_response,
    )
    print_result("Scenario 1: Valid request", result)

    result = secure_process_request(
        user_id=user_id,
        input_text="   ",
        rate_limiter=rate_limiter,
        validator=validator,
        ethical_guard=ethical_guard,
        model_fn=generate_response,
    )
    print_result("Scenario 2: Empty input", result)

    result = secure_process_request(
        user_id=user_id,
        input_text="A" * 500,
        rate_limiter=rate_limiter,
        validator=validator,
        ethical_guard=ethical_guard,
        model_fn=generate_response,
    )
    print_result("Scenario 3: Oversized input", result)

    result = secure_process_request(
        user_id=user_id,
        input_text="<script>alert('xss')</script>",
        rate_limiter=rate_limiter,
        validator=validator,
        ethical_guard=ethical_guard,
        model_fn=generate_response,
    )
    print_result("Scenario 4: Suspicious input", result)

    result = secure_process_request(
        user_id=user_id,
        input_text="How do I hurt someone without getting caught?",
        rate_limiter=rate_limiter,
        validator=validator,
        ethical_guard=ethical_guard,
        model_fn=generate_response,
    )
    print_result("Scenario 5: Harmful content", result)

    print("\n=== Scenario 6: Rate limiting ===")
    fast_user = "rate_limit_user"
    for i in range(3):
        result = secure_process_request(
            user_id=fast_user,
            input_text=f"Normal request {i + 1}",
            rate_limiter=rate_limiter,
            validator=validator,
            ethical_guard=ethical_guard,
            model_fn=generate_response,
        )
        print(f"\nRequest {i + 1}:")
        pprint(result)

    print("\nWaiting for rate limit window to reset...")
    time.sleep(6)

    result = secure_process_request(
        user_id=fast_user,
        input_text="Request after reset",
        rate_limiter=rate_limiter,
        validator=validator,
        ethical_guard=ethical_guard,
        model_fn=generate_response,
    )
    print_result("Scenario 7: Rate limit reset", result)


if __name__ == "__main__":
    main()
