"""Web 页面基类：封装 Selenium 通用元素操作 + Web 专属 open。

Web / App 共用的 UI 操作(find / click / input / get_text 等)统一放在这里，
App 端特有的 swipe / toast 在 base/app_base 中扩展。
"""


from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait

from common.logger.logger import get_logger

log = get_logger("web_base")


class UIBase:
    def __init__(self, driver, timeout: int = 10):
        self.driver = driver
        self.timeout = timeout

    def find(self, loc):
        log.info("查找元素: %s", loc)
        return WebDriverWait(self.driver, self.timeout).until(
            EC.visibility_of_element_located(loc)
        )

    def find_all(self, loc):
        return self.driver.find_elements(*loc)

    def click(self, loc):
        log.info("点击元素: %s", loc)
        self.find(loc).click()

    def input(self, loc, text):
        el = self.find(loc)
        el.clear()
        el.send_keys(text)

    def get_text(self, loc):
        return self.find(loc).text

    def exists(self, loc) -> bool:
        try:
            self.find(loc)
            return True
        except Exception:
            return False


class WebBase(UIBase):
    def open(self, url: str):
        self.driver.get(url)
