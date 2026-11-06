"""mis 后台审核端统一入口（门面）。

script/ 用例层只 import 这一个入口；页面/接口对象延迟导入，避免重依赖。
"""


class MisEntry:
    def __init__(self, driver=None, client=None):
        self._driver = driver
        self._client = client

    @property
    def api(self):
        from page.mis.api_mis import ApiMis
        return ApiMis(self._client)

    def _page(self, cls):
        if self._driver is None:
            raise RuntimeError("MisEntry 未注入 driver，无法构建 Web 页面对象")
        return cls(self._driver)

    @property
    def login_page(self):
        from page.mis.web_login_page import LoginPage
        return self._page(LoginPage)

    @property
    def audit_page(self):
        from page.mis.web_audit_page import AuditPage
        return self._page(AuditPage)

    @property
    def audit_detail_page(self):
        from page.mis.web_audit_detail_page import AuditDetailPage
        return self._page(AuditDetailPage)
