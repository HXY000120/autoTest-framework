"""mp 端内公共组件：顶部导航栏（跨页面复用，避免重复定义）。"""


from selenium.webdriver.common.by import By

from base.web_base import WebBase


class NavBar(WebBase):
    _logo = (By.CSS_SELECTOR, ".logo")
    _menu_items = (By.CSS_SELECTOR, ".nav-menu li")

    def go_home(self):
        self.click(self._logo)

    def menu_count(self):
        return len(self.find_all(self._menu_items))
