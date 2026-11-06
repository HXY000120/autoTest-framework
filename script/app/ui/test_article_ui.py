"""app 用户端 - App UI 文章流用例（数据驱动）。"""
import pytest

from common.utils.data_reader import load_data

cases = load_data("app/ui/article_cases.yaml")


@pytest.mark.app
@pytest.mark.parametrize("case", cases)
def test_app_article_ui(app_ui, case):
    from page.app.app_article_screen import ArticleScreen
    from page.app.components.scroll_helper import ScrollHelper

    screen = app_ui.article_screen
    count = screen.article_count()

    helper = app_ui.scroll_helper
    # 演示组件复用：在滑动中查找第一个文章项
    item = helper.find_in_scroll(screen._article_items, max_swipes=3)

    if case["expect_articles"]:
        assert count >= 1 or item is not None
    else:
        assert count == 0
