"""app 用户端 - 文章详情 UI 用例（数据驱动；未装 appium 自动 skip）。"""
import pytest

from common.utils.data_reader import load_data

cases = load_data("app/ui/detail_cases.yaml")


@pytest.mark.app
@pytest.mark.parametrize("case", cases)
def test_app_detail_ui(app_ui, case):
    # 先进入首页并打开首条，再进详情屏
    app_ui.home_screen.open_article(0)
    detail = app_ui.detail_screen
    if case.get("expect_detail"):
        assert detail.get_title(), "进入详情页却取不到标题"
    action = case.get("action")
    if action == "comment":
        detail.open_comments()
    elif action == "like":
        detail.like()
