"""mp 自媒体端发布文章页(Web PO)。只封装操作，不含断言。

定位器取自真实页面（2026-11 实测，Element UI）：
    标题      input[placeholder='请在这里输入标题']   （不是「文章标题」）
    标签      input[placeholder='请输入标签']
    频道      input[placeholder='请选择频道']
    定时      input[placeholder='请选择日期时间']
    提交按钮  文案是「提交审核」，不是「发布」
    草稿按钮  文案是「存入草稿」
空表单点提交审核会同时出现 5 条校验提示，可直接做判定表用例。
"""

import time

from selenium.webdriver.common.by import By

from base.web_base import WebBase


class EditorPage(WebBase):
    _title = (By.CSS_SELECTOR, "input[placeholder='请在这里输入标题']")
    _tag = (By.CSS_SELECTOR, "input[placeholder='请输入标签']")
    _channel = (By.CSS_SELECTOR, "input[placeholder='请选择频道']")
    _datetime = (By.CSS_SELECTOR, "input[placeholder='请选择日期时间']")
    _btn_submit = (By.XPATH, "//button[contains(normalize-space(.),'提交审核')]")
    _btn_draft = (By.XPATH, "//button[contains(normalize-space(.),'存入草稿')]")
    _errors = (
        By.CSS_SELECTOR,
        ".el-form-item__error,.el-message,.el-message--error,"
        ".el-notification,[role=alert]",
    )

    def open_publish(self, base_url: str):
        self.open(f"{base_url}/#/news/publish")
        time.sleep(2)  # Vue SPA 异步渲染表单

    def fill_title(self, title: str):
        self.input(self._title, title)

    def submit(self):
        """点击「提交审核」。表单校验不通过时不会真正写库，可安全用于用例。"""
        self.click(self._btn_submit)
        time.sleep(1)

    def validation_messages(self):
        """返回当前页面所有校验提示文本。"""
        return [e.text.strip() for e in self.find_all(self._errors) if e.text.strip()]

    def publish(self, title, content):
        """兼容旧调用：填标题后提交。富文本正文由业务方按需扩展。"""
        self.fill_title(title)
        self.submit()
