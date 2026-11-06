"""mp 自媒体端统一入口（门面）。

设计意图：
    - script/ 用例层只 import 这一个入口，不直接 import 任何具体页面/接口类；
    - 所有页面/接口对象都在 property 内「延迟导入」，避免未安装 selenium/appium
      时影响其他端用例的收集；
    - 注入 driver / client 后，entry 负责把同一份驱动传给各个页面对象。
"""


class MpEntry:
    def __init__(self, driver=None, client=None):
        self._driver = driver
        self._client = client

    # ---- 接口对象 ----
    @property
    def api(self):
        from page.mp.api_mp import ApiMp
        return ApiMp(self._client)

    # ---- 页面对象（需 driver）----
    def _page(self, cls):
        if self._driver is None:
            raise RuntimeError("MpEntry 未注入 driver，无法构建 Web 页面对象")
        return cls(self._driver)

    @property
    def login_page(self):
        from page.mp.web_login_page import LoginPage
        return self._page(LoginPage)

    @property
    def search_page(self):
        from page.mp.web_search_page import SearchPage
        return self._page(SearchPage)

    @property
    def editor_page(self):
        from page.mp.web_editor_page import EditorPage
        return self._page(EditorPage)

    @property
    def article_page(self):
        from page.mp.web_article_page import ArticlePage
        return self._page(ArticlePage)

    @property
    def content_page(self):
        from page.mp.web_content_page import ContentPage
        return self._page(ContentPage)

    @property
    def nav_bar(self):
        from page.mp.components.nav_bar import NavBar
        return self._page(NavBar)

    @property
    def login_dialog(self):
        from page.mp.components.login_dialog import LoginDialog
        return self._page(LoginDialog)
