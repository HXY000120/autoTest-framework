"""mis 后台审核详情页 - 查看 / 通过 / 驳回 用例（真实浏览器执行，无地址自动跳过）。

页面约束（真实探测所得）：列表行内「通过 / 驳回」初始 disabled，必须先「查看」
进入详情才能审核。本文件把「查看 -> 详情 -> 通过 / 驳回（驳回填原因）」串起来。

真实地址通过 MIS_BASE_URL 注入；未配置时整体 skip，不影响离线回归。
"""
import pytest

from common.config.settings import get_credentials, get_endpoint
from common.utils.data_reader import load_data

cases = load_data("mis/ui/audit_detail_cases.yaml")


def _login_and_open(mis_web):
    base = get_endpoint("mis")["base_url"]
    name, pwd = get_credentials("mis")
    login = mis_web.login_page
    login.open(f"{base}/#/login")
    login.login(name, pwd)
    login.wait_for_login()
    page = mis_web.audit_detail_page
    page.open_audit(base)
    return page


@pytest.mark.web
@pytest.mark.mis
@pytest.mark.parametrize("case", cases, ids=[c["case_id"] for c in cases])
def test_mis_audit_detail(mis_web, case):
    """查看详情 / 审核通过 / 审核驳回：动作执行不抛异常，详情弹窗应可打开。"""
    page = _login_and_open(mis_web)
    page.view_first()
    assert page.detail_visible(), "点击「查看」后详情未展示"

    if case["action"] == "approve":
        page.approve()
    elif case["action"] == "reject":
        page.reject(case.get("reason", "内容不符合规范"))


@pytest.mark.web
@pytest.mark.mis
def test_mis_audit_detail_elements(mis_web):
    """审核页关键入口：列表存在且每行提供「查看」操作。"""
    from selenium.webdriver.common.by import By

    page = _login_and_open(mis_web)
    d = page.driver
    assert d.find_elements(
        By.XPATH, "//button[contains(., '查看')]"
    ), "审核列表未提供「查看」入口"


@pytest.mark.web
@pytest.mark.mis
def test_mis_audit_detail_case_contract():
    """离线守卫：查看 / 通过 / 驳回 三类动作都要覆盖，且驳回带原因。"""
    actions = {c["action"] for c in cases}
    assert {"view", "approve", "reject"} <= actions, f"覆盖不全: {actions}"
    rejects = [c for c in cases if c["action"] == "reject"]
    assert rejects and all(r.get("reason") for r in rejects), "驳回用例必须带原因"
