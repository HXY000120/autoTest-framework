"""app 用户端统一入口（门面）。

script/ 用例层只 import 这一个入口；页面/接口对象延迟导入，避免重依赖。
"""


class AppEntry:
    def __init__(self, driver=None, client=None):
        self._driver = driver
        self._client = client

    @property
    def api(self):
        from page.app.api_app import ApiApp
        return ApiApp(self._client)

    def _page(self, cls):
        if self._driver is None:
            raise RuntimeError("AppEntry 未注入 driver，无法构建 App 页面对象")
        return cls(self._driver)

    @property
    def login_screen(self):
        from page.app.app_login_screen import LoginScreen
        return self._page(LoginScreen)

    @property
    def article_screen(self):
        from page.app.app_article_screen import ArticleScreen
        return self._page(ArticleScreen)

    @property
    def scroll_helper(self):
        from page.app.components.scroll_helper import ScrollHelper
        return self._page(ScrollHelper)
