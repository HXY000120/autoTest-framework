"""app 用户端 - 首页/频道 UI 用例（数据驱动；未装 appium 自动 skip）。"""
import pytest

from common.utils.data_reader import load_data

cases = load_data("app/ui/home_cases.yaml")


@pytest.mark.app
@pytest.mark.parametrize("case", cases)
def test_app_home_ui(app_ui, case):
    home = app_ui.home_screen
    if case.get("channel"):
        home.switch_channel(case["channel"])
    count = home.article_count()
    if case["expect_articles"]:
        assert count >= 1, "首页文章流为空"
    else:
        assert count == 0
