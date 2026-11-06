"""mp 自媒体端内容管理/搜索页(Web PO)。只封装操作，不含断言。

定位器取自真实页面：
    搜索框 input[placeholder='请输入关键字']
    结果行 .el-table__body-wrapper tbody tr

注意：该页**没有搜索按钮**（页面上仅分页按钮），输入关键字后需回车触发查询，
写成 click(搜索按钮) 会直接失败。
"""


import time

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

from base.web_base import WebBase


class SearchPage(WebBase):
    _keyword = (By.CSS_SELECTOR, "input[placeholder='请输入关键字']")
    _results = (By.CSS_SELECTOR, ".el-table__body-wrapper tbody tr")

    def search(self, keyword: str):
        el = self.find(self._keyword)
        el.clear()
        el.send_keys(keyword)
        el.send_keys(Keys.ENTER)      # 无搜索按钮，回车触发查询
        time.sleep(2)                 # 等表格异步刷新，否则读到的是旧结果

    def result_count(self) -> int:
        return len(self.find_all(self._results))

    def first_result_text(self) -> str:
        rows = self.find_all(self._results)
        return rows[0].text if rows else ""

    def wait_rows(self, timeout: int = 25) -> bool:
        """等待表格至少渲染出 1 行。

        该页数据异步加载且受后端响应速度影响，可能较慢甚至为空，
        故返回 bool 交由用例决定是否跳过，而不是直接抛错。
        """
        from selenium.webdriver.support.ui import WebDriverWait

        try:
            WebDriverWait(self.driver, timeout).until(
                lambda d: len(d.find_elements(*self._results)) > 0
            )
            return True
        except Exception:
            return False

    def first_title(self) -> str:
        """取首行标题（行文本形如「序号\\n标题\\n阅读\\n...」）。

        用页面真实标题做搜索关键词，比硬编码关键词更稳——
        该页是「内容分析」视图，数据未必包含接口侧的文章。
        """
        rows = self.find_all(self._results)
        if not rows:
            return ""
        parts = [p.strip() for p in rows[0].text.split("\n") if p.strip()]
        return parts[1] if len(parts) > 1 else (parts[0] if parts else "")
