"""mis Web UI 用例 fixture：组装 MisEntry + WebDriver。"""
import pytest

from page.mis.entry import MisEntry


@pytest.fixture
def mis_web(web_driver):
    return MisEntry(driver=web_driver)
