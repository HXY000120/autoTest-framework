"""mp Web 登录 - 异常场景用例（真实浏览器执行）。

与 test_login_ui.py 的正向用例形成对照：异常输入必须停留在登录页，
且不得渲染出登录态专属的 .user-name 元素。
"""
import time

import pytest
from selenium.webdriver.common.by import By

from common.config.settings import get_credentials, get_endpoint
from common.utils.data_reader import load_data

cases = load_data("mp/ui/login_negative_cases.yaml")


@pytest.mark.web
@pytest.mark.mp
@pytest.mark.parametrize("case", cases, ids=[c["case_id"] for c in cases])
def test_mp_login_negative_ui(mp_web, case):
    base = get_endpoint("mp")["base_url"]
    page = mp_web.login_page
    page.open(f"{base}/#/login")
    page.login(case["username"], case["password"])
    time.sleep(2)  # 等 Vue SPA 处理登录请求与错误提示

    url = page.driver.current_url.lower()
    assert "#/login" in url, (
        f"异常输入「{case['desc']}」竟跳转离开登录页: {url}"
    )
    nickname_els = page.driver.find_elements(By.CSS_SELECTOR, ".user-name")
    assert not nickname_els, (
        f"异常输入「{case['desc']}」后出现了登录态用户名元素"
    )


@pytest.mark.web
@pytest.mark.mp
def test_login_negative_case_contract():
    """离线守卫：异常用例必须覆盖 4 类设计方法。"""
    methods = {c["method"].split("-")[0] for c in cases}
    assert {"等价类", "边界值", "判定表", "安全性"} <= methods
    _, correct_password = get_credentials("mp")
    for c in cases:
        assert isinstance(c["username"], str) and isinstance(c["password"], str)
        assert c["password"] != correct_password, (
            f"{c['case_id']} 误用了正确密码，异常用例会自相矛盾"
        )
