"""app 用户端接口对象(API Object)。

重要说明（避免误读）：当前被测环境只提供 mp / mis 两个域名，APP 端改用
「示例新闻 App」做 UI 自动化，并没有配套的自有接口服务。因此本对象采用
**配置驱动**：

    endpoints.app.base_url 为空  -> 不发真实请求，只做接口对象契约/单测
    配好 base_url 与 login_path -> 同一套用例自动切到真实联调

这样既不伪造「3 套接口已联调」，也保留了接入真实 APP 服务的能力。
"""

from base.api_base import ApiClient
from common.config.settings import get_endpoint


class ApiApp:
    def __init__(self, client: ApiClient = None):
        ep = get_endpoint("app")
        self.configured = bool(ep.get("base_url"))
        self.client = client or ApiClient(end="app")
        self.url_login = ep.get("login_path") or "/app/v1_0/authorizations"
        self.url_article_list = ep.get("article_list_path") or "/app/v1_0/articles"

    def login(self, mobile, code):
        """APP 登录：手机号与验证码统一转字符串，避免前导零/数值类型问题。

        与 mp/mis 的 API Object 保持一致：登录成功后自动把 token 注入 client，
        后续文章流等接口无需用例手工取 token。
        """
        resp = self.client.post(
            self.url_login, json={"mobile": str(mobile), "code": str(code)}
        )
        try:
            body = resp.json()
            if body.get("code") == 0:
                token = (body.get("data") or {}).get("token")
                if token:
                    self.client.set_token(token)
        except (ValueError, AttributeError):
            pass
        return resp

    def article_list(self, channel_id: int = 0, size: int = 10):
        """APP 首页文章流（真实服务未部署时由虚拟接口提供）。"""
        return self.client.post(
            self.url_article_list,
            json={"channel_id": channel_id, "size": size},
        )
