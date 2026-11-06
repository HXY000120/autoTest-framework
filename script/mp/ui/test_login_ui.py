"""mp 自媒体端 - Web UI 登录用例（数据驱动；未装 selenium 自动 skip）。"""
import pytest

from common.config.settings import get_credentials, get_endpoint
from common.utils.data_reader import load_data

cases = load_data("mp/ui/login_cases.yaml")


@pytest.mark.web
@pytest.mark.mp
@pytest.mark.parametrize("case", cases)
def test_mp_login_ui(mp_web, case):
    # 前端为 Vue hash 路由，登录页地址 /#/login
    base = get_endpoint("mp")["base_url"]
    if case.get("use_config_password"):
        _, password = get_credentials("mp")   # 密码按当天日期动态生成
    else:
        password = case["password"]

    page = mp_web.login_page
    page.open(f"{base}/#/login")
    page.login(case["username"], password)
    page.wait_for_login()          # 等 SPA 路由跳转完成

    nickname = page.get_nickname()
    assert nickname, (
        f"登录后未取到昵称，登录可能失败（当前URL: {page.driver.current_url}）"
    )
    assert nickname == case["expect_nickname"], (
        f"昵称期望 {case['expect_nickname']}, 实际 {nickname}"
    )
