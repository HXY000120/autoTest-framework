"""全局 conftest：

1. 确保项目根加入 sys.path（配合 pytest.ini 的 pythonpath，双保险）
2. 提供低层 fixture：api_client / web_driver / app_driver
3. TEST_TARGET 收集隔离：指定单端时忽略其它业务端用例（端维度）；
   技术维度（api/web/app）仍由 ``pytest -m`` 控制
"""
import os
import sys

import pytest

ROOT = os.path.dirname(os.path.abspath(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from base.api_base import ApiClient  # noqa: E402

# 端维度过滤：TEST_TARGET=mp/mis/app 只跑对应端；为空则全部
TEST_TARGET = os.getenv("TEST_TARGET", "").lower()
ENDS = ("mp", "mis", "app")


def pytest_ignore_collect(collection_path, config):
    """指定 TEST_TARGET 时，忽略非目标端的 script 目录（收集阶段隔离）。"""
    if not TEST_TARGET:
        return False
    p = str(collection_path).replace("\\", "/")
    for end in ENDS:
        if end != TEST_TARGET and f"/script/{end}/" in p:
            return True
    return False


@pytest.fixture
def api_client():
    yield ApiClient()


@pytest.fixture
def mock_server():
    """虚拟接口服务：每个用例独立端口与状态，互不污染。

    用于补齐教学环境缺失/维护中的接口（发布、审核动作、APP 端服务），
    详见 common/mock/mock_server.py。
    """
    from common.mock.mock_server import start_server

    server = start_server()
    try:
        yield server
    finally:
        server.shutdown()


@pytest.fixture
def web_driver():
    try:
        from common.driver.web_driver import get_web_driver, quit_web_driver
    except ImportError:
        pytest.skip("未安装 selenium，跳过 Web 用例")
    driver = get_web_driver()
    yield driver
    quit_web_driver(driver)


@pytest.fixture
def app_driver():
    try:
        from common.driver.app_driver import get_app_driver, quit_app_driver
    except ImportError:
        pytest.skip("未安装 appium，跳过 App 用例")
    driver = get_app_driver()
    yield driver
    quit_app_driver(driver)


# ---------- 失败自动截图 ----------
def _extract_driver(item):
    """从已解析的 fixture 中取出可用的 driver（Selenium / Appium 通用）。

    两种形态都要覆盖：
        1. 直接用 web_driver / app_driver fixture
        2. 用 entry 门面（mp_web / mis_web / app_ui），driver 在其 _driver 上
    """
    for name in ("web_driver", "app_driver"):
        drv = item.funcargs.get(name)
        if drv is not None and hasattr(drv, "save_screenshot"):
            return drv
    for obj in item.funcargs.values():
        drv = getattr(obj, "_driver", None)
        if drv is not None and hasattr(drv, "save_screenshot"):
            return drv
    return None


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """用例执行失败（call 阶段）时自动截图，并追加到 Allure 报告。"""
    outcome = yield
    report = outcome.get_result()

    if report.when != "call" or not report.failed:
        return

    driver = _extract_driver(item)
    if driver is None:
        return

    from common.utils.screenshot import take_screenshot

    path = take_screenshot(driver, name=report.nodeid.replace("::", "__"))
    try:  # 装了 allure 就把截图挂进报告，没装也不影响截图落盘
        import allure
        allure.attach.file(
            path, name=report.nodeid,
            attachment_type=allure.attachment_type.PNG,
        )
    except Exception:
        pass
    print(f"\n[失败截图] {path}")
