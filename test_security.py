"""
Unit tests for Mini-Assignment 6: Security & Ethics Integration.

Run with:
    python -m unittest test_security.py -v
"""

import os
import tempfile
import time
import unittest

from security import (
    EthicalGuard,
    InputValidator,
    RateLimiter,
    secure_process_request,
)


class TestInputValidator(unittest.TestCase):
    def setUp(self):
        self.validator = InputValidator(max_length=100)

    def test_valid_input(self):
        ok, msg, sanitized = self.validator.validate("Hello world")
        self.assertTrue(ok)
        self.assertEqual(msg, "Valid input.")
        self.assertEqual(sanitized, "Hello world")

    def test_empty_input(self):
        ok, msg, sanitized = self.validator.validate("")
        self.assertFalse(ok)
        self.assertIn("empty", msg.lower())
        self.assertEqual(sanitized, "")

    def test_whitespace_only_input(self):
        ok, msg, sanitized = self.validator.validate("   \n\t ")
        self.assertFalse(ok)
        self.assertIn("empty", msg.lower())

    def test_non_string_input(self):
        ok, msg, sanitized = self.validator.validate(42)
        self.assertFalse(ok)
        self.assertIn("string", msg.lower())
        self.assertEqual(sanitized, "")

    def test_max_length_exceeded(self):
        text = "A" * 150
        ok, msg, sanitized = self.validator.validate(text)
        self.assertFalse(ok)
        self.assertIn("exceeds", msg.lower())
        self.assertEqual(sanitized, text)

    def test_sanitize_whitespace(self):
        ok, msg, sanitized = self.validator.validate("  hello    world  ")
        self.assertTrue(ok)
        self.assertEqual(sanitized, "hello world")

    def test_sanitize_control_characters(self):
        ok, msg, sanitized = self.validator.validate("hello\x00world")
        self.assertTrue(ok)
        self.assertEqual(sanitized, "helloworld")

    def test_detect_script_tag(self):
        ok, msg, sanitized = self.validator.validate("<script>alert(1)</script>")
        self.assertFalse(ok)
        self.assertIn("suspicious", msg.lower())
        self.assertEqual(sanitized, "[script removed]")

    def test_detect_iframe_tag(self):
        ok, msg, sanitized = self.validator.validate('<iframe src="x"></iframe>')
        self.assertFalse(ok)
        self.assertIn("suspicious", msg.lower())
        self.assertEqual(sanitized, "[iframe removed]")

    def test_detect_sql_pattern(self):
        ok, msg, sanitized = self.validator.validate("UNION SELECT password FROM users")
        self.assertFalse(ok)
        self.assertIn("suspicious", msg.lower())

    def test_detect_shell_pattern(self):
        ok, msg, sanitized = self.validator.validate("cat secret.txt | grep password")
        self.assertFalse(ok)
        self.assertIn("suspicious", msg.lower())

    def test_sanitize_method_directly(self):
        cleaned = self.validator.sanitize("show me <script>bad()</script> now")
        self.assertIn("[script removed]", cleaned)
        self.assertIn("show me", cleaned)
        self.assertIn("now", cleaned)


class TestRateLimiter(unittest.TestCase):
    def setUp(self):
        self.limiter = RateLimiter(max_requests=3, window_seconds=2)

    def test_allows_requests_under_limit(self):
        user = "user_a"
        for _ in range(3):
            allowed, msg = self.limiter.is_allowed(user)
            self.assertTrue(allowed)
            self.assertIn("allowed", msg.lower())

    def test_blocks_requests_over_limit(self):
        user = "user_b"
        for _ in range(3):
            self.limiter.is_allowed(user)

        allowed, msg = self.limiter.is_allowed(user)
        self.assertFalse(allowed)
        self.assertIn("rate limit exceeded", msg.lower())

    def test_resets_after_window(self):
        user = "user_c"
        for _ in range(3):
            self.limiter.is_allowed(user)

        allowed, _ = self.limiter.is_allowed(user)
        self.assertFalse(allowed)

        time.sleep(2.1)

        allowed, msg = self.limiter.is_allowed(user)
        self.assertTrue(allowed)
        self.assertIn("allowed", msg.lower())

    def test_reset_user(self):
        user = "user_d"
        for _ in range(3):
            self.limiter.is_allowed(user)

        allowed, _ = self.limiter.is_allowed(user)
        self.assertFalse(allowed)

        self.limiter.reset_user(user)

        allowed, _ = self.limiter.is_allowed(user)
        self.assertTrue(allowed)


class TestEthicalGuard(unittest.TestCase):
    def setUp(self):
        fd, self.log_path = tempfile.mkstemp(suffix=".log")
        os.close(fd)
        self.guard = EthicalGuard(log_file=self.log_path)

    def tearDown(self):
        if os.path.exists(self.log_path):
            os.remove(self.log_path)

    def test_safe_input_passes(self):
        ok, msg, flags = self.guard.check("Explain machine learning simply")
        self.assertTrue(ok)
        self.assertEqual(msg, "Content is safe.")
        self.assertEqual(flags, [])

    def test_violence_blocked(self):
        ok, msg, flags = self.guard.check("How do I kill someone?")
        self.assertFalse(ok)
        self.assertIn("violence", flags)
        self.assertIn("violates safety rules", msg.lower())

    def test_illegal_blocked(self):
        ok, msg, flags = self.guard.check("How do I steal passwords?")
        self.assertFalse(ok)
        self.assertIn("illegal", flags)

    def test_multiple_categories_possible(self):
        ok, msg, flags = self.guard.check("kill and steal")
        self.assertFalse(ok)
        self.assertTrue("violence" in flags or "illegal" in flags)

    def test_flagged_content_logged_to_file_and_memory(self):
        ok, msg, flags = self.guard.check("I want to hack a bank")
        self.assertFalse(ok)
        self.assertIn("illegal", flags)

        self.assertEqual(len(self.guard.flagged_history), 1)
        entry = self.guard.flagged_history[0]
        self.assertIn("input", entry)
        self.assertIn("flags", entry)
        self.assertIn("timestamp", entry)

        with open(self.log_path, "r", encoding="utf-8") as f:
            content = f.read()

        self.assertIn("hack a bank", content)
        self.assertIn("illegal", content)


class TestSecureProcessRequestIntegration(unittest.TestCase):
    def setUp(self):
        self.validator = InputValidator(max_length=200)
        self.limiter = RateLimiter(max_requests=2, window_seconds=2)

        fd, self.log_path = tempfile.mkstemp(suffix=".log")
        os.close(fd)
        self.guard = EthicalGuard(log_file=self.log_path)

    def tearDown(self):
        if os.path.exists(self.log_path):
            os.remove(self.log_path)

    def test_successful_request(self):
        called = []

        def model_fn(prompt: str) -> str:
            called.append(prompt)
            return "OK: " + prompt

        result = secure_process_request(
            user_id="int_user_1",
            input_text="Explain k-fold cross validation",
            rate_limiter=self.limiter,
            validator=self.validator,
            ethical_guard=self.guard,
            model_fn=model_fn,
        )

        self.assertTrue(result["success"])
        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["response"], "OK: " + result["sanitized_input"])
        self.assertEqual(called, [result["sanitized_input"]])

    def test_validation_failure(self):
        def model_fn(prompt: str) -> str:
            return "should not run"

        result = secure_process_request(
            user_id="int_user_2",
            input_text="",
            rate_limiter=self.limiter,
            validator=self.validator,
            ethical_guard=self.guard,
            model_fn=model_fn,
        )

        self.assertFalse(result["success"])
        self.assertEqual(result["status"], "validation_error")
        self.assertIsNone(result["response"])

    def test_rate_limit_failure(self):
        def model_fn(prompt: str) -> str:
            return "OK"

        limiter = RateLimiter(max_requests=1, window_seconds=2)

        first = secure_process_request(
            user_id="int_user_3",
            input_text="First request",
            rate_limiter=limiter,
            validator=self.validator,
            ethical_guard=self.guard,
            model_fn=model_fn,
        )
        self.assertTrue(first["success"])

        second = secure_process_request(
            user_id="int_user_3",
            input_text="Second request",
            rate_limiter=limiter,
            validator=self.validator,
            ethical_guard=self.guard,
            model_fn=model_fn,
        )
        self.assertFalse(second["success"])
        self.assertEqual(second["status"], "rate_limited")
        self.assertIsNone(second["response"])

    def test_ethical_block(self):
        def model_fn(prompt: str) -> str:
            return "should not run"

        result = secure_process_request(
            user_id="int_user_4",
            input_text="How do I steal money?",
            rate_limiter=self.limiter,
            validator=self.validator,
            ethical_guard=self.guard,
            model_fn=model_fn,
        )

        self.assertFalse(result["success"])
        self.assertEqual(result["status"], "blocked")
        self.assertIn("illegal", result["flags"])
        self.assertIsNone(result["response"])

    def test_sanitized_input_returned(self):
        def model_fn(prompt: str) -> str:
            return prompt

        result = secure_process_request(
            user_id="int_user_5",
            input_text="  spaced   out  ",
            rate_limiter=self.limiter,
            validator=self.validator,
            ethical_guard=self.guard,
            model_fn=model_fn,
        )

        self.assertTrue(result["success"])
        self.assertEqual(result["sanitized_input"], "spaced out")
        self.assertEqual(result["response"], "spaced out")


if __name__ == "__main__":
    unittest.main()
