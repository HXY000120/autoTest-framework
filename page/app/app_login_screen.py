"""app 用户端登录屏(App PO)。

被测 App：网易新闻（包名 com.netease.newsreader.activity）。

说明：定位器使用 selenium 的 By（Appium 兼容），避免顶层 import appium，
从而保证未安装 Appium 时不影响其他端用例的收集。

注意：下列 resource-id 为按网易新闻常见结构预估的占位值，需用 uiautomatorviewer
在真机/模拟器上确认后替换；框架只改 PO 即可，用例层零定位器。
"""


from selenium.webdriver.common.by import By

from base.app_base import AppBase

PKG = "com.netease.newsreader.activity"


class LoginScreen(AppBase):
    _phone = (By.ID, f"{PKG}:id/phone_et")
    _pwd = (By.ID, f"{PKG}:id/pwd_et")
    _login = (By.ID, f"{PKG}:id/login_btn")

    def login(self, phone, pwd):
        self.input(self._phone, phone)
        self.input(self._pwd, pwd)
        self.click(self._login)
