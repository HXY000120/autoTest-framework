"""App 屏幕基类：继承 UIBase，扩展 Appium 专属操作(swipe / toast)。

注意：Appium 相关依赖(appium.webdriver)不在模块顶层导入，避免未安装
Appium 时影响 Web / 接口用例的收集与执行（与 conftest 的延迟导入策略一致）。
"""


from base.web_base import UIBase


class AppBase(UIBase):
    def swipe(self, start_x, start_y, end_x, end_y, duration=800):
        self.driver.swipe(start_x, start_y, end_x, end_y, duration)

    def get_toast_text(self, text_contains: str, timeout=5):
        # Appium toast 通常用 xpath 文本包含匹配；依赖在方法内导入，避免顶层耦合
        from appium.webdriver.common.appiumby import AppiumBy
        from selenium.webdriver.support import expected_conditions as EC
        from selenium.webdriver.support.wait import WebDriverWait

        loc = (AppiumBy.XPATH, f"//*[contains(@text,'{text_contains}')]")
        return WebDriverWait(self.driver, timeout).until(
            EC.presence_of_element_located(loc)
        ).text
