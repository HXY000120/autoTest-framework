"""mis 后台审核端审核详情页(Web PO)。只封装操作，不含断言。

真实结构（2026-11 探测所得）：
    列表路由      /#/news/index
    数据行        tr.el-table__row（Element UI 表格）
    行内操作      span 文本「查看 / 通过 / 驳回」
    详情路由      /#/news/detail?id=xxx（**不是弹窗**，是独立页面）
    详情页动作    button「通过」「驳回」
    驳回原因      点「驳回」后出现 textarea / 确认框
"""


import time

from selenium.webdriver.common.by import By

from base.web_base import WebBase


class AuditDetailPage(WebBase):
    _rows = (By.CSS_SELECTOR, ".el-table__row")
    _view = (By.XPATH, ".//span[normalize-space(text())='查看']")
    _detail_mark = (By.XPATH, "//*[normalize-space(text())='文章详情']")
    _approve = (By.XPATH, "//button[normalize-space(text())='通过']")
    _reject = (By.XPATH, "//button[normalize-space(text())='驳回']")
    _reason = (
        By.CSS_SELECTOR,
        ".el-dialog textarea, .el-message-box textarea, textarea",
    )
    _confirm = (
        By.XPATH,
        "//div[contains(@class,'el-dialog') or contains(@class,'el-message-box')]"
        "//button[contains(normalize-space(.),'确定') or contains(normalize-space(.),'提交')]",
    )

    def open_audit(self, base_url: str):
        self.open(f"{base_url}/#/news/index")
        from selenium.webdriver.support.ui import WebDriverWait

        # 登录后默认在用户审核页；SPA 切换时旧 DOM 仍在，只等「有行」会被
        # 用户审核的行骗过（点「查看」会进错详情）。等内容审核独有的
        # 「单图文章 / 多图文章」列出现。
        WebDriverWait(self.driver, 25).until(
            lambda d: any(
                "图文章" in r.text for r in d.find_elements(*self._rows)
            )
        )
        time.sleep(1)  # 表格渲染完成后 DOM 可能整体替换，留出稳定窗口

    def view_first(self):
        """点击列表首个「查看」进入详情页。

        不持有 tr 引用：表格数据刷新后旧元素会 stale，直接按文本定位更稳。
        高频登录后列表加载偶发变慢，失败时刷新重试一次。
        """
        from selenium.webdriver.support import expected_conditions as EC
        from selenium.webdriver.support.ui import WebDriverWait

        for attempt in range(2):
            try:
                el = WebDriverWait(self.driver, 25).until(
                    EC.element_to_be_clickable(
                        (By.XPATH, "//span[normalize-space(text())='查看']")
                    )
                )
                el.click()
                time.sleep(2)
                return
            except Exception:
                if attempt == 0:
                    self.driver.refresh()
                    time.sleep(3)
                else:
                    raise

    def detail_visible(self) -> bool:
        return bool(self.find_all(self._detail_mark)) or "/news/detail" in self.driver.current_url

    def approve(self):
        """在详情页点击「通过」，若弹确认框则确认。"""
        self.click(self._approve)
        time.sleep(1)
        self._confirm_if_present()

    def reject(self, reason: str = "内容不符合规范"):
        """在详情页点击「驳回」，填原因后确认。"""
        self.click(self._reject)
        time.sleep(1)
        boxes = self.find_all(self._reason)
        if boxes:
            boxes[0].clear()
            boxes[0].send_keys(reason)
        self._confirm_if_present()

    def _confirm_if_present(self):
        submits = self.find_all(self._confirm)
        if submits:
            submits[0].click()
            time.sleep(1)
