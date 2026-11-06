"""mis 后台审核端审核详情/操作页(Web PO)。只封装操作，不含断言。

真实审核工作流（探测所得）：列表行内「通过 / 驳回」初始为 disabled，
必须先点「查看」进入详情，才能执行审核动作。故本 PO 把「查看 -> 详情 ->
通过 / 驳回（驳回需填原因）」串成可复用操作。

定位器按 Element UI 常见结构编写，接入实际系统时按 DOM 复核：
    查看按钮       行内文本「查看」
    详情容器       弹窗 .el-dialog 或详情面板 .detail / .audit-detail
    通过按钮       文案含「通过」
    驳回按钮       文案含「驳回」
    驳回原因输入框  textarea（驳回时必填）
    提交/确定按钮  文案含「提交」或「确定」
"""


import time

from selenium.webdriver.common.by import By

from base.web_base import WebBase


class AuditDetailPage(WebBase):
    _view = (By.XPATH, "//button[contains(., '查看')]")
    _detail = (
        By.CSS_SELECTOR,
        ".el-dialog,.audit-detail,.detail-panel,[class*='detail']",
    )
    _approve = (By.XPATH, "//button[contains(normalize-space(.), '通过')]")
    _reject = (By.XPATH, "//button[contains(normalize-space(.), '驳回')]")
    _reason = (By.CSS_SELECTOR, "textarea")
    _submit = (
        By.XPATH,
        "//button[contains(normalize-space(.), '提交') or contains(normalize-space(.), '确定')]",
    )

    def open_audit(self, base_url: str):
        self.open(f"{base_url}/#/audit")
        time.sleep(2)

    def view_first(self):
        """点击列表首行的「查看」进入详情。"""
        self.click(self._view)
        time.sleep(1)

    def detail_visible(self) -> bool:
        return bool(self.find_all(self._detail))

    def approve(self):
        """在详情中点击通过并提交。"""
        self.click(self._approve)
        time.sleep(0.5)
        self._submit_if_present()
        time.sleep(1)

    def reject(self, reason: str = "内容不符合规范"):
        """在详情中填写原因并驳回。"""
        el = self.find(self._reason)
        el.clear()
        el.send_keys(reason)
        self.click(self._reject)
        time.sleep(0.5)
        self._submit_if_present()
        time.sleep(1)

    def _submit_if_present(self):
        submits = self.find_all(self._submit)
        if submits:
            submits[0].click()
