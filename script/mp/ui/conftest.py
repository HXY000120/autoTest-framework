"""mp Web UI 用例 fixture：组装 MpEntry + WebDriver。"""
import pytest

from page.mp.entry import MpEntry


@pytest.fixture
def mp_web(web_driver):
    """业务入口（注入了 Web 驱动），用例只跟它打交道。"""
    return MpEntry(driver=web_driver)
