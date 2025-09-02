from slowapi import Limiter
from slowapi.util import get_remote_address
from fastapi import Request

limiter = Limiter(key_func=get_remote_address)

def limit_middleware(app):
    """

    :param app:
    :return:
    """
    @app.middleware("http")
    async def rate_limit(request: Request, call_next):
        response = await limiter(request, call_next)
        return response
