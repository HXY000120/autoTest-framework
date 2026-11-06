"""mis 后台审核端 - Web UI 登录用例（数据驱动）。"""
import pytest

from common.config.settings import get_credentials, get_endpoint
from common.utils.data_reader import load_data

cases = load_data("mis/ui/login_cases.yaml")


@pytest.mark.web
@pytest.mark.mis
@pytest.mark.parametrize("case", cases)
def test_mis_login_ui(mis_web, case):
    base = get_endpoint("mis")["base_url"]
    if case.get("use_config_password"):
        _, password = get_credentials("mis")
    else:
        password = case["password"]

    page = mis_web.login_page
    page.open(f"{base}/#/login")
    page.login(case["username"], password)

    # 真实断言：登录成功后应跳转离开登录页（登录失败时会停留在 /login）
    url = page.wait_for_login()
    assert "#/login" not in url.lower(), f"登录后仍停留在登录页: {url}"
