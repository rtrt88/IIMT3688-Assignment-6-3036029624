# Demo Script for Security Scenarios

This script demonstrates various security scenarios that can occur in a web application. Each scenario is represented by a function that tests a specific case.

## Scenarios Covered:
1. Valid requests
2. Empty input
3. Oversized input
4. SQL injection attempt
5. Harmful content
6. Rate limiting
7. Rate limit reset

```python
import time
import random

# Mock function to simulate a web request handling
def web_request_handler(data):
    # Simulated request processing logic
    print(f'Handling request with data: {data}')
    return 'Request handled successfully'

# 1. Valid request
print("Valid Request:")
response = web_request_handler('Valid data')
print(response)

# 2. Empty input
print("\nEmpty Input:")
try:
    response = web_request_handler('')
except ValueError as e:
    print('Error:', e)

# 3. Oversized input
print("\nOversized Input:")
try:
    oversized_data = 'A' * 10000  # Example oversized data
    response = web_request_handler(oversized_data)
except Exception as e:
    print('Error:', e)

# 4. SQL Injection
print("\nSQL Injection:")
try:
    sql_injection = 'SELECT * FROM users WHERE name = \'admin\''
    response = web_request_handler(sql_injection)
except Exception as e:
    print('Error:', e)

# 5. Harmful content
print("\nHarmful Content:")
try:
    harmful_content = '<script>alert(1);</script>'
    response = web_request_handler(harmful_content)
except Exception as e:
    print('Error:', e)

# 6. Rate limiting
print("\nRate Limiting:")
request_times = []
for i in range(10):
    if len(request_times) < 5:
        response = web_request_handler('Request ' + str(i))
        request_times.append(time.time())
    else:
        print('Rate limit exceeded')
    time.sleep(1)  # Simulate waiting time

# 7. Rate limit reset
print("\nRate Limit Reset:")
while request_times and time.time() - request_times[0] > 5:
    request_times.pop(0)

if len(request_times) < 5:
    response = web_request_handler('New Request after reset')
    print(response)
else:
    print('Rate limit still in effect')

```