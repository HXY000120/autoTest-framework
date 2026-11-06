"""app 用户端文章屏(App PO)：文章列表与详情。

被测 App：网易新闻。resource-id 为占位值，需真机确认后替换。
"""


from selenium.webdriver.common.by import By

from base.app_base import AppBase

PKG = "com.netease.newsreader.activity"


class ArticleScreen(AppBase):
    _article_items = (By.ID, f"{PKG}:id/article_item")
    _title = (By.ID, f"{PKG}:id/article_title")

    def article_count(self) -> int:
        return len(self.find_all(self._article_items))

    def open_first(self):
        items = self.find_all(self._article_items)
        if items:
            items[0].click()

    def get_first_title(self):
        return self.get_text(self._title)
