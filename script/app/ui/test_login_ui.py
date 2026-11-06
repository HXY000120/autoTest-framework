"""app 用户端 - App UI 登录用例（数据驱动；未装 appium 自动 skip）。"""
import pytest

from common.utils.data_reader import load_data

cases = load_data("app/ui/login_cases.yaml")


@pytest.mark.app
@pytest.mark.parametrize("case", cases)
def test_app_login_ui(app_ui, case):
    app_ui.login_screen.login(case["phone"], case["pwd"])
    if case.get("expect_success"):
        title = app_ui.article_screen.get_first_title()
        assert title, "登录成功却未进入文章流/未取到标题"
    else:
        # 反向：停留在登录页或弹错误提示，不应进入文章流
        assert app_ui.article_screen.article_count() == 0, "登录失败却进入了文章流"
