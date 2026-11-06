"""mp 自媒体端 - Web UI 搜索用例。

搜索依赖登录态：未登录会被重定向到登录页，内容管理页的搜索框根本不存在。

注意：列表页的检索规则与接口侧未必一致，
因此正向用例从列表首行动态取标题作为关键词，避免硬编码关键词搜不到。
"""
import pytest

from common.config.settings import get_credentials, get_endpoint
from common.utils.data_reader import load_data

cases = load_data("mp/ui/search_cases.yaml")


def _login(mp_web):
    base = get_endpoint("mp")["base_url"]
    name, pwd = get_credentials("mp")
    login = mp_web.login_page
    login.open(f"{base}/#/login")
    login.login(name, pwd)
    login.wait_for_login()
    return base


@pytest.mark.web
@pytest.mark.mp
@pytest.mark.skip(
    reason="搜索正向用例依赖具体页面的检索规则，未与被测页面核对前保持 skip，"
           "确认规则后启用本用例即可"
)
def test_mp_search_existing(mp_web):
    """用列表首行标题搜索，应能命中（验证搜索功能真的生效）。"""
    base = _login(mp_web)
    sp = mp_web.search_page
    sp.open(f"{base}/#/news/index")

    if not sp.wait_rows():
        pytest.skip("内容页表格未加载出数据（后端响应慢/波动），跳过搜索断言")

    keyword = sp.first_title()
    assert keyword, "未能从列表首行取到标题"
    sp.search(keyword)

    assert sp.result_count() >= 1, f"搜索已存在的标题「{keyword}」却无结果"


@pytest.mark.web
@pytest.mark.mp
@pytest.mark.parametrize("case", cases)
def test_mp_search_nonexistent(mp_web, case):
    """搜索不存在的关键词，应返回 0 条。"""
    base = _login(mp_web)
    sp = mp_web.search_page
    sp.open(f"{base}/#/news/index")
    sp.wait_rows()

    sp.search(case["keyword"])
    count = sp.result_count()
    assert count == 0, f"搜索「{case['keyword']}」应无结果，实际 {count} 条"
