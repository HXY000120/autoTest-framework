"""接口客户端基类：基于 requests.Session 的统一封装。

特性：
    - 按「业务端」取配置：base_url + 网关前缀 api_prefix
    - 统一 headers（含 token）
    - 统一超时与日志
    - 业务端 API Object(ApiMp 等) 接收外部 client 注入，实现功能/性能双用
"""


import requests

from common.config.settings import get_endpoint, load_config
from common.logger.logger import get_logger
from common.utils.retry import retry_on_fail

log = get_logger("api_client")

# 该环境部署在网关 WAF 之后：requests 默认的 "python-requests/x.x"
# User-Agent 会被直接拦截并返回 405（WAF 拦截页），必须伪装成浏览器。
DEFAULT_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)


class ApiRequestError(RuntimeError):
    """网络层失败（超时 / DNS / 连接重置），与业务失败区分开。"""


class ApiClient:
    """接口客户端。

    :param end: 业务端名（mp / mis / app），按端取域名与网关前缀
    :param base_url: 显式指定域名时覆盖配置（Locust 等场景常用）
    """

    def __init__(self, end: str = None, base_url: str = None, headers: dict = None):
        cfg = load_config()
        if end:
            ep = get_endpoint(end)
            self.base_url = ep["base_url"].rstrip("/")
            self.api_prefix = ep.get("api_prefix", "").rstrip("/")
        else:
            self.base_url = (base_url or cfg.get("base_url", "")).rstrip("/")
            self.api_prefix = cfg.get("api_prefix", "").rstrip("/")
        self.end = end
        self.headers = dict(cfg.get("headers", {"Content-Type": "application/json"}))
        if headers:
            self.headers.update(headers)
        self.headers.setdefault("User-Agent", DEFAULT_UA)
        self.session = requests.Session()
        self.token = None

    def set_token(self, token: str):
        """设置登录态。

        注意：平台网关只认 `token` 请求头，
        使用 `Authorization: Bearer` 会被判为未登录（实测返回 401）。
        """
        self.token = token
        self.headers["token"] = token

    @staticmethod
    @retry_on_fail(max_retries=2)
    def _send(session, **kwargs):
        """底层发送：仅 GET 幂等请求自动重试，POST/PUT/DELETE 绝不重试。"""
        return session.request(**kwargs)

    def request(self, method: str, path: str, **kwargs):
        path = path if path.startswith("/") else f"/{path}"
        url = f"{self.base_url}{self.api_prefix}{path}"
        kwargs.setdefault("headers", self.headers)
        kwargs.setdefault("timeout", 10)
        kwargs["method"] = method
        kwargs["url"] = url
        log.info("请求 %s %s", method.upper(), url)
        try:
            resp = self._send(self.session, **kwargs)
        except requests.RequestException as exc:
            # 网络层异常统一捕获 + 落日志，避免用例里散落 traceback
            log.error("请求失败 %s %s | %s", method.upper(), url, exc)
            raise ApiRequestError(
                f"接口请求失败: {method.upper()} {url} | {exc}"
            ) from exc
        log.info("响应 %s | %s", resp.status_code, resp.text[:200])
        return resp

    def get(self, path, **kwargs):
        return self.request("GET", path, **kwargs)

    def post(self, path, **kwargs):
        return self.request("POST", path, **kwargs)

    def put(self, path, **kwargs):
        return self.request("PUT", path, **kwargs)

    def delete(self, path, **kwargs):
        return self.request("DELETE", path, **kwargs)
