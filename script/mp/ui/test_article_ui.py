"""mp 自媒体端 - Web UI 发布/文章详情用例（数据驱动）。"""
import pytest

from common.utils.data_reader import load_data

cases = load_data("mp/ui/article_cases.yaml")


@pytest.mark.web
@pytest.mark.mp
@pytest.mark.skip(
    reason="发布接口在当前环境维护中（接口返回 code=900001），UI 发布流程暂无法验证；"
           "环境恢复后移除本 skip 即可"
)
@pytest.mark.parametrize("case", cases)
def test_mp_article_ui(mp_web, case):
    from page.mp.web_article_page import ArticlePage
    from page.mp.web_editor_page import EditorPage

    editor = mp_web.editor_page
    editor.publish(case["title"], case["content"])

    article = mp_web.article_page
    if case["expect_success"]:
        assert article.get_result_text() != ""
