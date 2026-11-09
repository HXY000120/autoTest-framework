"""mp 发布页扩展 - 频道选择 / 存草稿 用例（真实浏览器执行，无地址自动跳过）。

扩展 web_editor_page 的频道下拉与存草稿能力，覆盖发布页交互的更多分支：
    - 频道选择：Element UI 下拉，选错会直接失败
    - 存草稿：提交审核之外的另一条写库路径

真实地址通过 MP_BASE_URL 注入；未配置时整体 skip，不影响离线回归。
"""
import pytest

from common.config.settings import get_credentials, get_endpoint
from common.utils.data_reader import load_data

cases = load_data("mp/ui/editor_ext_cases.yaml")


def _login_and_open(mp_web):
    base = get_endpoint("mp")["base_url"]
    name, password = get_credentials("mp")
    login = mp_web.login_page
    login.open(f"{base}/#/login")
    login.login(name, password)
    login.wait_for_login()
    editor = mp_web.editor_page
    editor.open_publish(base)
    return editor


@pytest.mark.web
@pytest.mark.mp
@pytest.mark.parametrize("case", cases, ids=[c["case_id"] for c in cases])
def test_mp_editor_ext(mp_web, case):
    """频道选择 / 存草稿：验证操作结果，而不是「不报错就算过」。"""
    editor = _login_and_open(mp_web)
    editor.fill_title(case.get("title", "扩展用例标题"))
    editor.select_channel(case["channel"])

    # 断言 1：频道输入框的值必须是所选频道，否则等于没选上
    actual = editor.selected_channel()
    assert actual == case["channel"], (
        f"频道未选中，期望 {case['channel']}，实际 {actual!r}"
    )

    if case.get("title"):
        toast = editor.save_draft()
        # 断言 2：存草稿必须有成功反馈（线上实测提示「新增文章成功」）
        assert "成功" in toast, f"存草稿未出现成功提示，实际提示：{toast!r}"


@pytest.mark.web
@pytest.mark.mp
def test_mp_editor_ext_elements(mp_web):
    """发布页频道下拉与存草稿按钮必须存在。"""
    from selenium.webdriver.common.by import By

    editor = _login_and_open(mp_web)
    d = editor.driver
    assert d.find_elements(
        By.CSS_SELECTOR, "input[placeholder='请选择频道']"
    ), "未找到频道选择框"
    assert d.find_elements(
        By.XPATH, "//button[contains(normalize-space(.),'存入草稿')]"
    ), "未找到「存入草稿」按钮"


@pytest.mark.web
@pytest.mark.mp
def test_mp_editor_ext_case_contract():
    """离线守卫：频道选择场景必须覆盖，且 PO 提供了对应方法。"""
    from page.mp.web_editor_page import EditorPage

    assert hasattr(EditorPage, "select_channel"), "EditorPage 缺少 select_channel"
    assert hasattr(EditorPage, "save_draft"), "EditorPage 缺少 save_draft"
    channels = {c["channel"] for c in cases}
    assert channels, "缺少频道选择场景数据"
