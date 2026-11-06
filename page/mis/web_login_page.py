"""mis 后台审核端登录页(Web PO)。

定位器按常见 Element UI 登录表单结构编写（与 mp 端一致）：
    账号 input[type=text]、密码 input[type=password]
    按钮文案「登 录」（含空格），用 normalize-space 匹配
"""


from selenium.webdriver.common.by import By

from base.web_base import WebBase


class LoginPage(WebBase):
    _username = (By.CSS_SELECTOR, "input[type='text']")
    _password = (By.CSS_SELECTOR, "input[type='password']")
    _login_btn = (By.XPATH, "//button[contains(normalize-space(.), '登')]")
    _nickname = (By.CSS_SELECTOR, ".user-name")

    def login(self, username, password):
        self.input(self._username, username)
        self.input(self._password, password)
        self.click(self._login_btn)

    def wait_for_login(self, timeout: int = 20):
        """等待登录跳转完成。

        SPA 的前端路由跳转需要时间，点击后立即读 current_url 会仍停在
        /#/login，导致误判为登录失败。返回跳转后的 URL。
        """
        from selenium.webdriver.support.ui import WebDriverWait

        WebDriverWait(self.driver, timeout).until(
            lambda d: "#/login" not in d.current_url
        )
        return self.driver.current_url

    def get_nickname(self):
        return self.get_text(self._nickname)
