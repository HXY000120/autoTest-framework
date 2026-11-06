"""app 用户端首页/频道屏(App PO)：频道切换与文章流。

被测 App：网易新闻（包名 com.netease.newsreader.activity）。

说明：定位器使用 selenium 的 By（Appium 兼容），避免顶层 import appium。
下列 resource-id 为按网易新闻常见结构预估的占位值，需用 uiautomatorviewer
在真机/模拟器上确认后替换；框架只改 PO 即可，用例层零定位器。
"""

from selenium.webdriver.common.by import By

from base.app_base import AppBase

PKG = "com.netease.newsreader.activity"


class HomeScreen(AppBase):
    # 顶部频道 Tab（推荐 / 热点 / 娱乐 ...）
    _channel_tabs = (By.ID, f"{PKG}:id/tab_channel")
    # 文章列表项标题：用于计数与点击进入详情
    _article_item = (By.ID, f"{PKG}:id/article_title")
    # 顶部搜索入口
    _search_entry = (By.ID, f"{PKG}:id/action_search")
    # 下拉刷新容器
    _refresh_layout = (By.ID, f"{PKG}:id/refresh_layout")

    def channel_count(self) -> int:
        """当前可见频道数量。"""
        return len(self.find_all(self._channel_tabs))

    def switch_channel(self, name: str):
        """按频道名切换（相对 XPath 按文案匹配，避免索引脆弱）。"""
        loc = (By.XPATH, f"//*[contains(@text,'{name}')]")
        self.click(loc)

    def article_count(self) -> int:
        """首页文章流可见条数。"""
        return len(self.find_all(self._article_item))

    def open_article(self, index: int = 0):
        """打开第 index 篇文章，进入详情屏。"""
        items = self.find_all(self._article_item)
        if 0 <= index < len(items):
            items[index].click()

    def refresh(self):
        """下拉刷新：首屏顶部向下滑。"""
        size = self.driver.get_window_size()
        cx = size["width"] // 2
        top = int(size["height"] * 0.2)
        bottom = int(size["height"] * 0.6)
        self.swipe(cx, bottom, cx, top)

    def open_search(self):
        self.click(self._search_entry)
