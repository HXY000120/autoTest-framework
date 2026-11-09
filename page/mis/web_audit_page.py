"""mis 后台审核端审核页(Web PO)。

定位器按常见列表页结构编写，接入实际系统时按 DOM 复核：
    数据行       .el-table__body-wrapper tbody tr
    操作按钮     「查看」「通过」「驳回」（文本按钮，按实际 DOM 复核）

重要：行内的「通过 / 驳回」按钮初始为 disabled（is-disabled），
必须先点「查看」进入详情才能执行审核；直接 click 会报元素不可交互。
"""


from selenium.webdriver.common.by import By

from base.web_base import WebBase


class AuditPage(WebBase):
    _article_rows = (By.CSS_SELECTOR, ".el-table__body-wrapper tbody tr")
    _view = (By.XPATH, "//button[contains(., '查看')]")
    _approve = (By.XPATH, "//button[contains(., '通过')]")
    _reject = (By.XPATH, "//button[contains(., '驳回')]")

    def article_count(self) -> int:
        return len(self.find_all(self._article_rows))

    def open_audit(self, base_url: str):
        """打开「内容审核」列表页并确认已切换过去。

        登录后默认在 /#/auth/index（用户审核）。SPA 路由切换时旧页 DOM
        仍然存在，只等「有行」会被用户审核的行骗过（6 列 vs 内容审核 9 列）。
        因此等「单图文章 / 多图文章」这类内容审核独有列出现。
        """
        self.open(f"{base_url}/#/news/index")
        from selenium.webdriver.support.ui import WebDriverWait

        WebDriverWait(self.driver, 25).until(
            lambda d: any(
                "图文章" in r.text for r in d.find_elements(*self._article_rows)
            )
        )

    def row_texts(self):
        return [r.text for r in self.find_all(self._article_rows)]

    def audit(self, action: str):
        """执行审核动作。action: "approve" / "reject"。

        注意受页面约束：未进入详情时通过/驳回按钮为禁用态。
        """
        if action == "approve":
            self.click(self._approve)
        elif action == "reject":
            self.click(self._reject)
        else:
            raise ValueError(f"未知审核动作: {action}")
