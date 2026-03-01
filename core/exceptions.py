from rest_framework.exceptions import APIException


class RateLimitedException(APIException):
    status_code = 429
    default_code = "rate_limited"

    def __init__(self, retry_after, detail=None):
        if detail is None:
            detail = "Too many requests. Please try again later."

        self.detail = {
            "error": "rate_limited",
            "message": detail,
            "retry_after": retry_after,
        }
        self.retry_after = retry_after

        