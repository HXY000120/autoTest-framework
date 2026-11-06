"""mp 自媒体端文章详情页(Web PO)。只封装操作，不含断言。

发布后停留/跳转到的文章详情页，用于读取发布结果等信息。
"""


from selenium.webdriver.common.by import By

from base.web_base import WebBase


class ArticlePage(WebBase):
    _result = (By.CSS_SELECTOR, ".publish-result")
    _title = (By.CSS_SELECTOR, ".article-title")

    def get_result_text(self):
        return self.get_text(self._result)

    def get_title(self):
        return self.get_text(self._title)
