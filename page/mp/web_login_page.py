"""mp 自媒体端登录页(Web PO)。只封装操作，不含断言。

定位器按常见 Element UI 登录表单结构编写，接入实际系统时按 DOM 复核：
    input[type=text]      账号
    input[type=password]  密码
    登录按钮              <button><span>登 录</span></button>
                          注意文案是「登 录」（中间有空格），
                          故用 normalize-space + 单字「登」匹配；
                          写成 contains(text(),'登录') 会匹配不到
    .user-name            登录后的用户名（实际显示账号名，如 demo）
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
        """等待登录跳转完成（SPA 路由跳转需要时间）。返回跳转后的 URL。"""
        from selenium.webdriver.support.ui import WebDriverWait

        WebDriverWait(self.driver, timeout).until(
            lambda d: "#/login" not in d.current_url
        )
        return self.driver.current_url

    def get_nickname(self):
        return self.get_text(self._nickname)
