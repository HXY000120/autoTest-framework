"""mp 内容管理页 - 状态筛选 / 关键词搜索用例（真实浏览器执行，无地址自动跳过）。

页面约束：状态筛选 Tab 与关键词搜索都触发同一列表接口（带不同参数），
故用例分别覆盖「状态等价类（草稿/待审核/已发布/已下架）」与「关键词搜索」。
真实地址通过 MP_BASE_URL 注入；未配置时本文件用例整体 skip，不影响离线回归。
"""
import pytest

from common.config.settings import get_credentials, get_endpoint
from common.utils.data_reader import load_data

cases = load_data("mp/ui/content_cases.yaml")


def _login_and_open(mp_web):
    base = get_endpoint("mp")["base_url"]
    name, password = get_credentials("mp")
    login = mp_web.login_page
    login.open(f"{base}/#/login")
    login.login(name, password)
    login.wait_for_login()
    page = mp_web.content_page
    page.open_content(base)
    return page


@pytest.mark.web
@pytest.mark.mp
@pytest.mark.parametrize("case", cases, ids=[c["case_id"] for c in cases])
def test_mp_content_actions(mp_web, case):
    """状态筛选 / 关键词搜索：动作执行后页面表格区域必须仍可用（不报错）。"""
    page = _login_and_open(mp_web)
    all_count = page.row_count()  # 「全部」下的卡片数

    if case["action"] == "status":
        page.select_status(case["value"])
        filtered = page.row_count()
        assert filtered <= all_count, (
            f"筛选「{case['value']}」返回 {filtered} 条，多于全部 {all_count}"
        )
    else:
        page.search(case["value"])
        titles = page.titles()
        if titles:
            assert any(case["value"] in t for t in titles), (
                f"搜索结果未命中关键词「{case['value']}」：{titles}"
            )


@pytest.mark.web
@pytest.mark.mp
def test_mp_content_page_elements(mp_web):
    """内容管理页关键元素齐全性：4 个状态 Tab + 搜索框 + 列表行容器。"""
    from selenium.webdriver.common.by import By

    page = _login_and_open(mp_web)
    d = page.driver
    assert d.find_elements(
        By.CSS_SELECTOR, "input[placeholder='请输入关键字']"
    ), "未找到内容管理页搜索框"
    assert page.status_options(), "未找到状态筛选 radio"
    assert page.row_count() > 0, "内容列表没有任何卡片"
    assert page.has_pagination(), "未找到分页组件"


@pytest.mark.web
@pytest.mark.mp
def test_mp_content_case_contract():
    """离线守卫：状态筛选必须覆盖 4 种状态、且含关键词搜索场景。"""
    actions = {c["action"] for c in cases}
    assert {"status", "search"} <= actions, f"覆盖不全: {actions}"
    statuses = {c["value"] for c in cases if c["action"] == "status"}
    assert {"草稿", "待审核", "审核通过", "审核失败"} <= statuses, (
        f"状态 Tab 覆盖不全: {statuses}"
    )
    for c in cases:
        assert c.get("value"), f"{c['case_id']} 缺少 value"
