Mini-Assignment 6: Security & Ethics Integration =============================================== System overview --------------- Problem:
Mini-Assignment 6: Security & Ethics Integration

System overview

Problem: AI agents that accept free-form text are vulnerable to a range of practical problems — malicious or accidental prompt injection, abusive high-volume usage, and user requests that are harmful or unethical. This project implements a focused, backend-style security layer that sits in front of a simulated AI model to protect the agent, provide clear user feedback, and make behavior auditable for review.

Workflow (high level):

user input -> validation & sanitization -> rate limiting -> ethical guardrails -> model execution -> structured response
Key components:

InputValidator — robust input checks and sanitization
RateLimiter — per-user sliding-window request throttling
EthicalGuard — pattern-based harmful-content detection and logging
secure_process_request(...) — orchestrates the pipeline and returns a structured result
Threat model

This module is designed to mitigate the following realistic threat classes:

Prompt injection and markup-based attacks: Inputs containing script tags, iframes, embedded event handlers or explicit code execution patterns that could be forwarded to downstream systems or copied into logs/executables.
SQL/shell/content injection: Inputs that resemble SQL statements (UNION/SELECT/DROP) or shell command chaining (;, |, &&) intended to confuse or exploit downstream subsystems.
Abuse and Denial: High-frequency request floods from a single user (or session) intended to exhaust quota or disrupt service.
Harmful / illegal content: Explicit requests that ask for instructions for violence, illegal activity, hate or self-harm.
Malformed or oversized input: Extremely long, binary or control-character-laden inputs that break parsers or cause resource exhaustion.
Security measures implemented

Each subsection explains what is implemented, why it matters, and which threat it addresses.

Input Validation and Sanitization

What: InputValidator checks input type, non-empty content, and enforces a configurable maximum length. It runs regex-based detection for high-risk patterns (script/iframe tags, SQL keywords, shell-chaining tokens, eval/exec). It also normalizes whitespace, removes control characters, and neutralizes obvious markup ([script removed]).
Why: Failing fast on invalid or suspicious content prevents propagation of dangerous payloads to the model or logs, reduces risk of downstream exploits, and provides clear user feedback.
Threats addressed: prompt injection, XSS-like payloads, SQL/shell injection, malformed input.
Rate Limiting

What: RateLimiter implements an in-memory sliding-window per-user tracker. The default is configurable (e.g., 10 requests per 60 seconds). The API returns both a boolean and a user-friendly message including retry-after.
Why: Controls abuse and accidental floods, enforces fairness, and provides predictable behavior for tests and demos. A reset_user() helper supports deterministic testing.
Threats addressed: spam/abuse/denial-of-service by request volume.
Ethical Guardrails

What: EthicalGuard uses clear regex rules grouped by category (violence, illegal wrongdoing, hate/harassment, self-harm). When content is flagged it:
returns a user-facing block message,
records an in-memory audit entry,
appends a JSON line to flagged.log for offline review.
Why: Ensures the agent does not provide assistance for clearly harmful or illegal activities, and produces an audit trail for instructors or content reviewers.
Threats addressed: user attempts to obtain harmful/illegal instructions, hate speech, self-harm requests.
Integration Workflow

What: secure_process_request(user_id, input_text, rate_limiter, validator, ethical_guard, model_fn) enforces the pipeline order:
validate & sanitize
rate limit
ethical check
model call
structured result with fields: success, status, message, sanitized_input, response, flags
Why: The order ensures early failures stop unnecessary work downstream (and prevent leaking data or wasting model quota). The structured result makes automated grading and logging straightforward.
Threats addressed: every stage defends against a class of attacks and ensures consistent behavior.
How to use

Prerequisites

Python 3.8+ (standard library only; no third-party packages required)
Quick start

Run the demo (integrated scenarios):

python demo.py
The demo shows:

valid request processing
empty input rejection
oversized input rejection
SQL/injection detection
harmful request blocked by EthicalGuard
rate limiting and window reset (demo uses short windows for speed)
Run the unit tests (comprehensive coverage):

python -m unittest test_security.py -v
Module usage (programmatic)

Python
from security import InputValidator, RateLimiter, EthicalGuard, secure_process_request

validator = InputValidator(max_length=2000)
rate_limiter = RateLimiter(max_requests=10, window_seconds=60)
ethical_guard = EthicalGuard(log_file="flagged.log")

def model_fn(prompt: str) -> str:
    return f"Processed safely: {prompt}"

result = secure_process_request(
    user_id="alice",
    input_text="Explain cross validation",
    rate_limiter=rate_limiter,
    validator=validator,
    ethical_guard=ethical_guard,
    model_fn=model_fn,
)

# result is a dict with keys: success, status, message, sanitized_input, response, flags
Design choices

Rule-based detection (regex) for clarity and explainability: for this assignment a deterministic and auditable approach is preferred. Regex rules make behavior easy to test, reason about, and grade.
In-memory rate limiting: simplifies testing and keeps the project dependency-free. It is appropriate for a single-process demo and unit tests.
Structured responses: uniform return values (success, status, message, etc.) make integration and grading straightforward.
Logging to both memory and file: immediate inspection (memory) and a persistent audit trail (file) are both useful in classroom and grading contexts.
Limitations and future improvements

This implementation is intentionally simple and pedagogical. Known limitations and suggested improvements include:

Regex-based filtering can overblock (false positives) or miss sophisticated phrasing (false negatives). A production system should combine rules with machine learning-based moderation and contextual checks.
In-memory rate limiting is not suitable for multi-process or distributed deployments. Replace with Redis, Memcached, or a database-backed token bucket for horizontal scalability and persistence.
Sanitization here is conservative and basic (control chars removed, script tags neutralized). A production sanitization library and output escaping strategies (per destination) are recommended.
Audit logging is append-only JSON lines to flagged.log. For a real deployment, use structured centralized logging, tamper-evident storage, and a reviewer dashboard.
Ethical decisions are policy matters. This implementation uses clear, simple rules suitable for classroom demonstration — production systems require policy review, escalation paths (e.g., emergency/self-harm responses), and legal/regulatory considerations.
Appendix and deliverables

Files included in this submission:

security.py — Core module implementing InputValidator, RateLimiter, EthicalGuard, and secure_process_request
demo.py — Integrated demonstration script covering multiple scenarios
test_security.py — Deterministic and thorough unit tests (unittest)
README.md — (this file) documentation and guidance
prompt-log.md — development prompt history and decisions
flagged.log — (generated at runtime if harmful content is detected)
