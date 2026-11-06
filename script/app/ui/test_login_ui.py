"""app 用户端 - App UI 登录用例（数据驱动；未装 appium 自动 skip）。"""
import pytest

from common.utils.data_reader import load_data

cases = load_data("app/ui/login_cases.yaml")


@pytest.mark.app
@pytest.mark.parametrize("case", cases)
def test_app_login_ui(app_ui, case):
    screen = app_ui.login_screen
    screen.login(case["phone"], case["pwd"])

    # 真实断言：登录成功后应进入文章流并取到首条标题
    title = app_ui.article_screen.get_first_title()
    assert title, "登录后未取到文章标题，可能未进入文章流或登录失败"
