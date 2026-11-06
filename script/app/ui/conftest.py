"""app UI 用例 fixture：组装 AppEntry + Appium 驱动。"""
import pytest

from page.app.entry import AppEntry


@pytest.fixture
def app_ui(app_driver):
    return AppEntry(driver=app_driver)
