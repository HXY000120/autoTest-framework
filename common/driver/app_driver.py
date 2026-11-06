"""Appium 驱动管理。"""
from appium import webdriver
from appium.options.android import UiAutomator2Options

from common.config.settings import load_config


def get_app_driver(caps: dict = None):
    cfg = load_config()
    app_caps = caps or cfg.get("app_caps", {})
    server = cfg.get("appium_server", "http://127.0.0.1:4723/wd/hub")
    options = UiAutomator2Options().load_capabilities(app_caps)
    return webdriver.Remote(server, options=options)


def quit_app_driver(driver):
    if driver:
        driver.quit()
