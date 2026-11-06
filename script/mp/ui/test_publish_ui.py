"""mp 发布文章页 - 表单校验用例（判定表 + 边界值，真实浏览器执行）。

安全说明：本用例只触发前端校验，不产生真实文章。被测环境的 news/submit
接口处于维护中（code=900001），真正发布链路在 script/mp/api/test_publish_api.py
中以「维护中则 skip」的方式诚实标注。
"""
import pytest

from common.config.settings import get_credentials, get_endpoint
from common.utils.data_reader import load_data

cases = load_data("mp/ui/publish_cases.yaml")


def _login_and_open_editor(mp_web):
    base = get_endpoint("mp")["base_url"]
    _, password = get_credentials("mp")
    login = mp_web.login_page
    login.open(f"{base}/#/login")
    login.login("demo", password)
    login.wait_for_login()

    editor = mp_web.editor_page
    editor.open_publish(base)
    return editor


@pytest.mark.web
@pytest.mark.mp
@pytest.mark.parametrize("case", cases, ids=[c["case_id"] for c in cases])
def test_publish_form_validation(mp_web, case):
    """按判定表校验：该出现的提示必须出现，不该出现的必须消失。"""
    editor = _login_and_open_editor(mp_web)
    if case["title"]:
        editor.fill_title(case["title"])
    editor.submit()

    messages = editor.validation_messages()
    assert messages, f"「{case['desc']}」提交后竟没有任何表单校验提示"
    joined = " | ".join(messages)

    for expected in case["expect_errors"]:
        assert any(expected in m for m in messages), (
            f"「{case['desc']}」缺少校验提示「{expected}」，实际: {joined}"
        )
    for absent in case["expect_no_errors"]:
        assert not any(absent in m for m in messages), (
            f"「{case['desc']}」字段已合法却仍提示「{absent}」，实际: {joined}"
        )


@pytest.mark.web
@pytest.mark.mp
def test_publish_page_elements(mp_web):
    """发布页关键元素必须齐全，否则后续用例会静默失效。"""
    from selenium.webdriver.common.by import By

    editor = _login_and_open_editor(mp_web)
    d = editor.driver
    assert d.find_elements(By.CSS_SELECTOR, "input[placeholder='请在这里输入标题']")
    assert d.find_elements(By.CSS_SELECTOR, "input[placeholder='请输入标签']")
    assert d.find_elements(By.CSS_SELECTOR, "input[placeholder='请选择频道']")
    assert d.find_elements(
        By.XPATH, "//button[contains(normalize-space(.),'提交审核')]"
    ), "未找到「提交审核」按钮（旧定位器写的是「发布」，已失效）"
    assert d.find_elements(By.XPATH, "//button[contains(normalize-space(.),'存入草稿')]")


@pytest.mark.web
@pytest.mark.mp
def test_publish_case_contract():
    """离线守卫：判定表与边界值两类场景都要覆盖，且预期提示不得为空。"""
    methods = {c["method"] for c in cases}
    assert {"判定表", "边界值"} <= methods, f"覆盖不全: {methods}"
    for c in cases:
        assert isinstance(c["title"], str)
        assert c["expect_errors"], f"{c['case_id']} 没有任何预期校验提示"
        assert isinstance(c["expect_no_errors"], list)
