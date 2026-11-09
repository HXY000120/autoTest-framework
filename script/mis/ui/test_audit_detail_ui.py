"""mis 后台审核详情页 - 查看 / 通过 / 驳回 用例（真实浏览器执行，无地址自动跳过）。

页面约束（真实探测所得）：列表行内「通过 / 驳回」初始 disabled，必须先「查看」
进入详情才能审核。本文件把「查看 -> 详情 -> 通过 / 驳回（驳回填原因）」串起来。

真实地址通过 MIS_BASE_URL 注入；未配置时整体 skip，不影响离线回归。
"""
import os

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
    """查看审核详情（只读）；真实提交审核需 REAL_AUDIT=1。

    审核动作会真实改变文章状态并消耗待审核数据。默认只验证详情页可达与
    入口存在，避免前一个用例把唯一待审核文章审掉、后面用例找不到按钮。
    """
    page = _login_and_open(mis_web)
    page.view_first()
    assert page.detail_visible(), "点击「查看」后详情未展示"

    if os.getenv("REAL_AUDIT") != "1":
        return
    if case["action"] == "approve":
        page.approve()
    elif case["action"] == "reject":
        page.reject(case.get("reason", "内容不符合规范"))


@pytest.mark.web
@pytest.mark.mis
def test_mis_audit_detail_elements(mis_web):
    """审核页关键入口：列表渲染完成后，行内应提供查看/通过/驳回。"""
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait

    page = _login_and_open(mis_web)
    d = page.driver

    # 列表异步渲染，先显式等「查看」出现，避免高频登录后加载慢导致抢跑
    WebDriverWait(d, 20).until(
        lambda x: len(
            x.find_elements(By.XPATH, "//span[normalize-space(text())='查看']")
        ) > 0
    )
    for label in ("查看", "通过", "驳回"):
        assert d.find_elements(
            By.XPATH, f"//span[normalize-space(text())='{label}']"
        ), f"列表未提供「{label}」入口"


@pytest.mark.web
@pytest.mark.mis
def test_mis_audit_detail_case_contract():
    """离线守卫：查看 / 通过 / 驳回 三类动作都要覆盖，且驳回带原因。"""
    actions = {c["action"] for c in cases}
    assert {"view", "approve", "reject"} <= actions, f"覆盖不全: {actions}"
    rejects = [c for c in cases if c["action"] == "reject"]
    assert rejects and all(r.get("reason") for r in rejects), "驳回用例必须带原因"
