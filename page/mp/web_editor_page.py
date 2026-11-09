"""mp 自媒体端发布文章页(Web PO)。只封装操作，不含断言。

定位器按常见 Element UI 表单结构编写，接入实际系统时按 DOM 复核：
    标题      input[placeholder='请在这里输入标题']   （不是「文章标题」）
    标签      input[placeholder='请输入标签']
    频道      input[placeholder='请选择频道']
    定时      input[placeholder='请选择日期时间']
    提交按钮  文案是「提交审核」，不是「发布」
    草稿按钮  文案是「存入草稿」
空表单提交会触发多项必填校验，可直接做判定表用例。
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

    def fill_tag(self, tag: str):
        """填写标签。多标签以英文逗号分隔。"""
        self.input(self._tag, tag)

    def select_channel(self, channel: str):
        """选择频道（Element UI 级联/下拉）。点击输入框展开后点含文本的 option。"""
        self.click(self._channel)
        time.sleep(0.5)
        from selenium.webdriver.common.by import By

        options = self.driver.find_elements(
            By.CSS_SELECTOR, ".el-select-dropdown__item"
        )
        for opt in options:
            if channel in opt.text:
                opt.click()
                time.sleep(0.3)
                return
        raise AssertionError(f"频道下拉未找到选项：{channel}")

    def submit(self):
        """点击「提交审核」。表单校验不通过时不会真正写库，可安全用于用例。"""
        self.click(self._btn_submit)
        time.sleep(1)

    def save_draft(self):
        """点击「存入草稿」，返回页面提示文案（成功时含「成功」）。"""
        self.click(self._btn_draft)
        time.sleep(1)
        return self.message_text()

    def selected_channel(self) -> str:
        """返回频道输入框当前值，用于断言「确实选中了」。"""
        return self.find(self._channel).get_attribute("value") or ""

    def message_text(self) -> str:
        """当前页面顶部提示文案（Element UI message / notification）。"""
        locs = (
            By.CSS_SELECTOR,
            ".el-message, .el-message-box, .el-notification",
        )
        return " ".join(e.text.strip() for e in self.find_all(locs) if e.text.strip())

    def validation_messages(self):
        """返回当前页面所有校验提示文本。"""
        return [e.text.strip() for e in self.find_all(self._errors) if e.text.strip()]

    def publish(self, title, content):
        """兼容旧调用：填标题后提交。富文本正文由业务方按需扩展。"""
        self.fill_title(title)
        self.submit()
