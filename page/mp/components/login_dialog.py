"""mp 端内公共组件：登录弹窗（非整页登录，如未登录态触发弹窗登录）。"""


from selenium.webdriver.common.by import By

from base.web_base import WebBase


class LoginDialog(WebBase):
    _mobile = (By.CSS_SELECTOR, ".login-dialog [placeholder='请输入手机号']")
    _code = (By.CSS_SELECTOR, ".login-dialog [placeholder='请输入验证码']")
    _confirm = (By.XPATH, "//div[contains(@class,'login-dialog')]//button[contains(text(),'登录')]")

    def login(self, mobile, code):
        self.input(self._mobile, mobile)
        self.input(self._code, code)
        self.click(self._confirm)

    def is_visible(self) -> bool:
        return self.exists(self._confirm)
