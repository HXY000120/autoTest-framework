"""重试装饰器：仅对幂等请求(默认 GET)重试，写操作(POST/PUT/DELETE)绝不重试。

原因：写操作重试会导致重复提交（重复发文/下单），是接口自动化高频事故源。
"""


import functools

import requests


def retry_on_fail(max_retries: int = 3, allowed_methods=("GET",)):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            method = str(kwargs.get("method", "GET")).upper()
            if method not in allowed_methods:
                return func(*args, **kwargs)  # 写操作直接执行，不重试
            last_exc = None
            for _ in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except requests.RequestException as e:
                    last_exc = e
            raise last_exc

        return wrapper

    return decorator
