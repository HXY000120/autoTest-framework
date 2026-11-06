"""app 用户端文章详情屏(App PO)：标题 / 正文 / 评论 / 点赞 / 返回。

被测 App：网易新闻。resource-id 为按常见结构预估的占位值，需真机确认后替换。
"""

from selenium.webdriver.common.by import By

from base.app_base import AppBase

PKG = "com.netease.newsreader.activity"


class DetailScreen(AppBase):
    _title = (By.ID, f"{PKG}:id/article_title")
    _content = (By.ID, f"{PKG}:id/article_content")
    _comment_btn = (By.ID, f"{PKG}:id/comment_entry")
    _like_btn = (By.ID, f"{PKG}:id/like_btn")
    _back = (By.ID, f"{PKG}:id/back")

    def get_title(self) -> str:
        return self.get_text(self._title)

    def get_content(self) -> str:
        return self.get_text(self._content)

    def open_comments(self):
        self.click(self._comment_btn)

    def like(self):
        self.click(self._like_btn)

    def back(self):
        self.click(self._back)
