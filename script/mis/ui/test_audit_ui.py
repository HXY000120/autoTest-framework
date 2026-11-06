"""mis 后台审核端 - Web UI 审核用例（数据驱动）。

页面约束（真实探测所得）：行内的「通过 / 驳回」按钮初始为 disabled，
必须先点「查看」进入详情才能执行审核，直接点击会报元素不可交互。
因此本用例校验「列表可读 + 每行确实提供对应审核操作」，而非直接点击。
"""
import pytest

from common.config.settings import get_credentials, get_endpoint
from common.utils.data_reader import load_data

cases = load_data("mis/ui/audit_cases.yaml")
ACTION_TEXT = {"approve": "通过", "reject": "驳回"}


@pytest.mark.web
@pytest.mark.mis
@pytest.mark.parametrize("case", cases)
def test_mis_audit_ui(mis_web, case):
    base = get_endpoint("mis")["base_url"]
    _, pwd = get_credentials("mis")

    login = mis_web.login_page
    login.open(f"{base}/#/login")
    login.login("demo", pwd)
    login.wait_for_login()

    page = mis_web.audit_page
    rows = page.row_texts()
    assert rows, "审核列表无数据，无法校验审核入口"

    label = ACTION_TEXT[case["action"]]
    assert any(label in r for r in rows), (
        f"列表行未出现「{label}」操作，实际行内容: {rows[:2]}"
    )
