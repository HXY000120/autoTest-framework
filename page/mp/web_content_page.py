"""mp 自媒体端内容管理页(Web PO)。只封装操作，不含断言。

以下结构已按线上页面 DOM 核对（2026-11）：
    路由        /#/news/index
    状态筛选    label.el-radio，文案：全部 / 草稿 / 待审核 / 审核通过 / 审核失败
    搜索框      input[placeholder='请输入关键字']，回车触发
    列表        卡片式布局 div.item-card（**不是** el-table）
    卡片标题    div.item-card .content .center
    分页        .el-pagination

说明：状态切换与关键词搜索都走同一列表接口的不同参数，故筛选 Tab 与
搜索框各封装一个操作，便于做状态过滤 / 关键词搜索两类用例。
"""


import time

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

from base.web_base import WebBase


class ContentPage(WebBase):
    _status_radios = (By.CSS_SELECTOR, "label.el-radio")
    _keyword = (By.CSS_SELECTOR, "input[placeholder='请输入关键字']")
    _cards = (By.CSS_SELECTOR, "div.item-card")
    _card_title = (By.CSS_SELECTOR, "div.item-card .content .center")
    _pager = (By.CSS_SELECTOR, ".el-pagination")

    def open_content(self, base_url: str):
        self.open(f"{base_url}/#/news/index")
        # 该页首屏异步拉列表，实测 5s 左右才渲染卡片；等卡片出现再操作
        self.wait_rows(timeout=20)
        time.sleep(1)

    def status_options(self):
        """返回当前页面所有状态筛选项文案。"""
        return [(r.text or "").strip() for r in self.find_all(self._status_radios)]

    def select_status(self, label: str):
        """点击状态筛选 radio（全部/草稿/待审核/审核通过/审核失败）。"""
        for radio in self.find_all(self._status_radios):
            if (radio.text or "").strip() == label:
                radio.click()
                time.sleep(1.5)
                return
        raise AssertionError(
            f"内容列表未找到状态：{label}，实际可选：{self.status_options()}"
        )

    def search(self, keyword: str):
        el = self.find(self._keyword)
        el.clear()
        el.send_keys(keyword)
        el.send_keys(Keys.ENTER)
        time.sleep(2)

    def row_count(self) -> int:
        return len(self.find_all(self._cards))

    def titles(self):
        return [e.text.strip() for e in self.find_all(self._card_title) if e.text.strip()]

    def first_row_title(self) -> str:
        titles = self.titles()
        return titles[0] if titles else ""

    def has_pagination(self) -> bool:
        return bool(self.find_all(self._pager))

    def wait_rows(self, timeout: int = 25) -> bool:
        """等待列表至少渲染 1 张卡片；列表可能为空，返回 bool 交用例决定。"""
        from selenium.webdriver.support.ui import WebDriverWait

        try:
            WebDriverWait(self.driver, timeout).until(
                lambda d: len(d.find_elements(*self._cards)) > 0
            )
            return True
        except Exception:
            return False
