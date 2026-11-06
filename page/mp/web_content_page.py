"""mp 自媒体端内容管理页(Web PO)。只封装操作，不含断言。

对应「内容管理 / 文章列表」页面（通常路由 /#/content/manage）。
定位器按 Element UI 列表页常见结构编写，接入实际系统时按 DOM 复核：
    状态筛选 Tab   文案：草稿 / 待审核 / 已发布 / 已下架
    搜索框         input[placeholder='请输入关键字']
    查询按钮       文案含「查询」或「搜索」
    数据行         .el-table__body-wrapper tbody tr
    分页           .el-pagination

说明：列表页按状态切换本质是同接口带不同 status 参数，故「筛选 Tab」与
「搜索框」都封装为独立操作，便于做状态过滤 / 关键词搜索两类用例。
"""


import time

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

from base.web_base import WebBase


class ContentPage(WebBase):
    _status_tabs = (
        By.XPATH,
        "//div[contains(@class,'el-tabs')]//div[contains(@class,'el-tabs__item')]",
    )
    _keyword = (By.CSS_SELECTOR, "input[placeholder='请输入关键字']")
    _search_btn = (By.XPATH, "//button[contains(normalize-space(.),'查询') or contains(normalize-space(.),'搜索')]")
    _rows = (By.CSS_SELECTOR, ".el-table__body-wrapper tbody tr")
    _pager = (By.CSS_SELECTOR, ".el-pagination")

    def open_content(self, base_url: str):
        self.open(f"{base_url}/#/content/manage")
        time.sleep(2)  # Vue SPA 异步渲染列表

    def select_status(self, label: str):
        """点击状态筛选 Tab（草稿/待审核/已发布/已下架）。"""
        for tab in self.find_all(self._status_tabs):
            if label in tab.text:
                tab.click()
                time.sleep(1)
                return
        raise AssertionError(f"内容管理页未找到状态 Tab：{label}")

    def search(self, keyword: str):
        el = self.find(self._keyword)
        el.clear()
        el.send_keys(keyword)
        el.send_keys(Keys.ENTER)
        time.sleep(2)

    def row_count(self) -> int:
        return len(self.find_all(self._rows))

    def first_row_title(self) -> str:
        rows = self.find_all(self._rows)
        if not rows:
            return ""
        parts = [p.strip() for p in rows[0].text.split("\n") if p.strip()]
        return parts[1] if len(parts) > 1 else (parts[0] if parts else "")

    def has_pagination(self) -> bool:
        return bool(self.find_all(self._pager))

    def wait_rows(self, timeout: int = 25) -> bool:
        """等待表格至少渲染 1 行；列表可能为空或加载慢，返回 bool 交用例决定。"""
        from selenium.webdriver.support.ui import WebDriverWait

        try:
            WebDriverWait(self.driver, timeout).until(
                lambda d: len(d.find_elements(*self._rows)) > 0
            )
            return True
        except Exception:
            return False
