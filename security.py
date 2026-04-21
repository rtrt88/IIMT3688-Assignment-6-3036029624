class InputValidator:
    def __init__(self, allowed_inputs):
        self.allowed_inputs = allowed_inputs

    def validate(self, input_data):
        if input_data not in self.allowed_inputs:
            raise ValueError(f"Invalid input: {input_data}")
        return True

class RateLimiter:
    def __init__(self, requests_per_minute):
        self.requests_per_minute = requests_per_minute
        self.usage = {}

    def is_allowed(self, user_id):
        current_time = int(time.time())
        if user_id not in self.usage:
            self.usage[user_id] = []
        self.usage[user_id] = [t for t in self.usage[user_id] if t > current_time - 60]
        if len(self.usage[user_id]) < self.requests_per_minute:
            self.usage[user_id].append(current_time)
            return True
        return False

class EthicalGuard:
    def __init__(self, ethical_guidelines):
        self.ethical_guidelines = ethical_guidelines

    def ensure_compliance(self, data):
        for guideline in self.ethical_guidelines:
            if not guideline.check(data):
                raise Exception(f"Ethical violation: {guideline.name}")

def secure_process_request(input_data, user_id, ethical_guidelines, requests_per_minute):
    validator = InputValidator(allowed_inputs=['input1', 'input2', 'input3'])
    rate_limiter = RateLimiter(requests_per_minute)
    guard = EthicalGuard(ethical_guidelines)

    try:
        validator.validate(input_data)
        if not rate_limiter.is_allowed(user_id):
            raise Exception("Rate limit exceeded.")
        guard.ensure_compliance(input_data)
        # Process the request
        return "Request processed successfully."
    except Exception as e:
        return str(e)