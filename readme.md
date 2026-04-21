# Mini-Assignment 6: Security & Ethics Integration

## 1. System Overview

### Problem
AI agents that accept free-form user input are vulnerable to several practical risks, including malformed input, prompt injection-style content, abusive request volume, and harmful or unethical requests. If left unprotected, these issues can reduce reliability, waste system resources, and produce unsafe outputs.

This project implements a lightweight backend-style security layer placed in front of a simulated AI model. Its purpose is to validate and sanitize incoming input, limit abusive usage, block harmful content, and provide clear structured responses. The design prioritizes clarity, modularity, and auditability.

### Workflow
The system follows the pipeline below:

`user input -> validation & sanitization -> rate limiting -> ethical guardrails -> model execution -> structured response`

This ordering ensures that unsafe or invalid input is blocked before reaching the model, while legitimate requests are processed in a controlled and predictable way.

### Key Components
- **InputValidator**: validates input and sanitizes suspicious content
- **RateLimiter**: tracks requests per user within a time window
- **EthicalGuard**: detects harmful or inappropriate requests and logs flagged cases
- **secure_process_request(...)**: orchestrates the full security pipeline and returns a structured result

---

## 2. Threat Model

This module is designed to mitigate the following realistic threats in an AI agent workflow.

### 2.1 Prompt Injection and Markup-Based Attacks
User input may contain script tags, embedded markup, or suspicious execution-like patterns intended to interfere with downstream systems, logs, or interfaces. Even in a simplified assignment setting, such content should be treated as potentially unsafe.

### 2.2 SQL, Shell, or Command Injection Patterns
Inputs may include SQL-like keywords such as `DROP`, `UNION`, or `SELECT`, or shell chaining operators such as `;`, `&&`, and `|`. These patterns may not directly execute in this project, but they represent suspicious behavior that should be detected and filtered before further processing.

### 2.3 Abuse and Denial Through High-Volume Requests
A user or session may send repeated requests in a short period of time, either accidentally or maliciously. Without rate limiting, such behavior can exhaust resources, degrade responsiveness, and make the system unreliable.

### 2.4 Harmful or Unethical Requests
Users may attempt to obtain assistance for violent actions, illegal wrongdoing, hate speech, harassment, or self-harm. An AI agent should not process such requests without safeguards.

### 2.5 Malformed or Oversized Input
Extremely long inputs, empty inputs, or control-character-laden text may break assumptions in the application, reduce usability, or create unnecessary processing overhead.

---

## 3. Security Measures Implemented

### 3.1 Input Validation and Sanitization

#### What it does
The `InputValidator` class checks:
- whether the input is a string
- whether the input is non-empty after trimming whitespace
- whether the input stays within a configurable maximum length
- whether the input contains suspicious high-risk patterns such as script tags, SQL-style fragments, shell chaining operators, or execution-related tokens

The validator also sanitizes input by:
- normalizing repeated whitespace
- removing control characters where appropriate
- neutralizing obvious harmful markup patterns while preserving benign meaning as much as possible

#### Why it matters
This step prevents malformed or suspicious input from being forwarded to later stages of the system. It also improves robustness by failing early and returning clear user-facing error messages.

#### Threats addressed
- malformed input
- oversized input
- prompt injection-style content
- markup-based attacks
- SQL/shell injection-like patterns

---

### 3.2 Rate Limiting

#### What it does
The `RateLimiter` class implements per-user request tracking using an in-memory sliding window. Each user is allowed a configurable number of requests within a specified time period, such as 10 requests per 60 seconds.

If a user exceeds the limit, the system:
- blocks the request
- returns a clear error message
- allows requests again once the time window has passed

#### Why it matters
Rate limiting helps prevent spam, accidental overload, and simple abuse scenarios. It also ensures that the workflow behaves predictably during testing and demonstration.

#### Threats addressed
- abusive repeated usage
- denial-of-service through request flooding
- unfair resource consumption

---

### 3.3 Ethical Guardrails

#### What it does
The `EthicalGuard` class applies rule-based content filtering to detect harmful or inappropriate requests. It checks for patterns associated with:
- violence
- illegal wrongdoing
- hate or harassment
- self-harm

When content is flagged, the system:
- blocks the request
- returns an appropriate user-facing message
- records the flagged content in memory
- appends an audit entry to `flagged.log` for later review

#### Why it matters
This component ensures that the AI agent does not provide assistance for clearly unsafe or unethical requests. It also creates an auditable record of flagged content for accountability and review.

#### Threats addressed
- harmful requests
- illegal requests
- abusive or hateful content
- self-harm-related prompts

---

### 3.4 Integration Workflow

#### What it does
The `secure_process_request(...)` function integrates all security components into one callable workflow. The processing order is:

1. validate and sanitize input  
2. check rate limit  
3. apply ethical guardrails  
4. call the model only if all checks pass  
5. return a structured dictionary response

The returned result includes:
- `success`
- `status`
- `message`
- `sanitized_input`
- `response`
- `flags`

The main status values used in this implementation are:
- `ok`
- `validation_error`
- `rate_limited`
- `blocked`

#### Why it matters
The integrated pipeline is important because the assignment requires the security mechanisms to be exercised in a callable workflow. A unified function also makes the system easier to test, demonstrate, and extend.

#### Threats addressed
This workflow combines all earlier protections and ensures consistent, reliable behavior across requests.

---

## 4. How to Use the Security Module

### 4.1 Requirements
- Python 3.8+
- No third-party packages are required for the core implementation

### 4.2 Run the Demo
To run the demonstration script:

```bash
python demo.py
