"""mis 后台审核端接口对象(API Object)。只封装业务动作，不含断言。

真实环境：今日资讯平台测试项目（Java 版服务端）
    完整地址 = base_url + api_prefix = <配置的域名><网关前缀>

接口可用性（2026-11 实测）：
    可用     admin/login/in              POST  登录，code=0，token 在 data.token
    可用     user/api/v1/auth/list       POST  用户实名认证列表，code=200（有数据）
    可用     user/api/v1/auth/authFail   POST  认证驳回，code=0
    维护中   user/api/v1/auth/authPass   POST  认证通过，环境返回 code=900001
    可用     wemedia/api/v1/news/list    POST  文章列表（后台视角）
    可用     wemedia/api/v1/news/auth_pass  POST  文章审核通过（id 不存在返回 code=1002）
    可用     wemedia/api/v1/news/auth_fail  POST  文章审核驳回（id 不存在返回 code=1002）

业务码约定：
    0 / 200 成功；1002 数据不存在；900001 系统维护中；501 当前文章未发布
注意：authFail 对不存在的 id 也返回「操作成功」（后端未校验存在性），
      写用例时不能仅凭 code=0 判定业务正确。
"""

from base.api_base import ApiClient
from common.config.settings import get_credentials


class ApiMis:
    def __init__(self, client: ApiClient = None):
        self.client = client or ApiClient(end="mis")
        self.url_login = "/admin/login/in"
        self.url_auth_list = "/user/api/v1/auth/list"
        self.url_auth_pass = "/user/api/v1/auth/authPass"
        self.url_auth_fail = "/user/api/v1/auth/authFail"
        self.url_news_list = "/wemedia/api/v1/news/list"
        self.url_news_auth_pass = "/wemedia/api/v1/news/auth_pass"
        self.url_news_auth_fail = "/wemedia/api/v1/news/auth_fail"

    def login(self, name: str = None, password: str = None):
        """登录后台审核端。账号密码缺省时从配置读取（密码按当天日期动态生成）。"""
        if name is None or password is None:
            name, password = get_credentials("mis")
        resp = self.client.post(
            self.url_login, json={"name": name, "password": password}
        )
        try:
            body = resp.json()
            if body.get("code") == 0:
                token = (body.get("data") or {}).get("token")
                if token:
                    self.client.set_token(token)
        except ValueError:
            pass
        return resp

    def post_raw(self, path: str, payload: dict):
        """原样发送业务 payload，专供异常参数 / 边界值用例。"""
        return self.client.post(path, json=payload)

    def auth_list(self, page: int = 1, size: int = 10, status=None):
        """用户实名认证审核列表。status: None 全部 / 0 待审核 / 1 通过 / 2 驳回"""
        payload = {"page": page, "size": size}
        if status is not None:
            payload["status"] = status
        return self.client.post(self.url_auth_list, json=payload)

    def auth_pass(self, user_id, reason: str = None):
        """用户实名认证通过（当前环境维护中，返回 code=900001）。"""
        payload = {"id": user_id}
        if reason:
            payload["msg"] = reason
        return self.client.post(self.url_auth_pass, json=payload)

    def auth_fail(self, user_id, reason: str = "自动化测试驳回"):
        """用户实名认证驳回"""
        return self.client.post(
            self.url_auth_fail, json={"id": user_id, "msg": reason}
        )

    def news_list(self, page: int = 1, size: int = 10, status=None):
        """文章列表（后台视角）。status: 1 待审核 / 4 审核通过 / 9 已发布"""
        payload = {"page": page, "size": size}
        if status is not None:
            payload["status"] = status
        return self.client.post(self.url_news_list, json=payload)

    def audit_article_pass(self, article_id):
        """文章审核通过"""
        return self.client.post(self.url_news_auth_pass, json={"id": article_id})

    def audit_article_fail(self, article_id, reason: str = "自动化测试驳回"):
        """文章审核驳回"""
        return self.client.post(
            self.url_news_auth_fail, json={"id": article_id, "msg": reason}
        )
