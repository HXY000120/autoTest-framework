"""mis Web UI 用例 fixture：组装 MisEntry + WebDriver。

未配置被测系统地址时自动跳过，且**在启动浏览器之前**判断，避免无谓开销。
"""
import pytest

from common.config.settings import get_endpoint
from page.mis.entry import MisEntry


@pytest.fixture
def mis_web(request):
    if not get_endpoint("mis")["base_url"]:
        pytest.skip("未配置 MIS_BASE_URL，跳过 Web UI 用例（见 README「被测环境配置」）")
    return MisEntry(driver=request.getfixturevalue("web_driver"))


@pytest.fixture(scope="module")
def mis_web_logged_in():
    """模块级复用登录：只登录一次，用例内部自行回到目标页面。

    被测系统对高频登录有限流，逐条登录会让后段用例加载变慢而随机失败；
    UI 自动化本就不该每条用例重新登录。
    """
    if not get_endpoint("mis")["base_url"]:
        pytest.skip("未配置 MIS_BASE_URL，跳过 Web UI 用例（见 README「被测环境配置」）")
    try:
        from common.driver.web_driver import get_web_driver, quit_web_driver
    except ImportError:
        pytest.skip("未安装 selenium，跳过 Web 用例")

    from common.config.settings import get_credentials

    base = get_endpoint("mis")["base_url"]
    name, pwd = get_credentials("mis")
    driver = get_web_driver()
    entry = MisEntry(driver=driver)
    entry.login_page.open(f"{base}/#/login")
    entry.login_page.login(name, pwd)
    entry.login_page.wait_for_login()
    yield entry
    quit_web_driver(driver)
