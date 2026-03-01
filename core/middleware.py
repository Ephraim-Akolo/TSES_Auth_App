from ipware import get_client_ip


class ClientInfoMiddleware:
    """
    Attaches client network metadata to request object.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        ip, is_routable = get_client_ip(request)

        request.client_ip = ip
        request.client_ip_is_routable = is_routable
        request.user_agent = request.META.get("HTTP_USER_AGENT", "")

        return self.get_response(request)