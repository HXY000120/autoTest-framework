"""app 用户端登录屏(App PO)。

被测 App：示例新闻 App（包名 com.example.news）。

说明：定位器使用 selenium 的 By（Appium 兼容），避免顶层 import appium，
从而保证未安装 Appium 时不影响其他端用例的收集。

注意：下列 resource-id 为占位值，需用 uiautomatorviewer 在真机上确认后替换。
"""


from selenium.webdriver.common.by import By

from base.app_base import AppBase

PKG = "com.example.news"


class LoginScreen(AppBase):
    _phone = (By.ID, f"{PKG}:id/phone_et")
    _pwd = (By.ID, f"{PKG}:id/pwd_et")
    _login = (By.ID, f"{PKG}:id/login_btn")

    def login(self, phone, pwd):
        self.input(self._phone, phone)
        self.input(self._pwd, pwd)
        self.click(self._login)
