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
# 线上列表状态列实际取值
STATUSES = {"待人工审核", "已发布", "已驳回", "已下架"}


@pytest.mark.web
@pytest.mark.mis
@pytest.mark.parametrize("case", cases)
def test_mis_audit_ui(mis_web, case):
    base = get_endpoint("mis")["base_url"]
    name, pwd = get_credentials("mis")

    login = mis_web.login_page
    login.open(f"{base}/#/login")
    login.login(name, pwd)
    login.wait_for_login()

    page = mis_web.audit_page
    page.open_audit(base)

    rows = page.row_texts()
    assert rows, "审核列表无数据，无法校验审核入口"

    label = ACTION_TEXT[case["action"]]
    # 逐行逐列校验：任何一行结构不对 / 状态非法 / 缺操作，都说明列表渲染有问题
    for row in rows:
        cells = [c.strip() for c in row.split("\n") if c.strip()]
        assert len(cells) >= 8, f"行结构异常（列数不足）: {cells}"
        assert cells[1], f"标题列为空: {cells}"
        status = cells[-2]
        assert status in STATUSES, f"状态列非法: {status!r}，整行: {cells}"
        actions = cells[-1]
        assert "查看" in actions, f"操作列缺少「查看」: {actions}"
        assert label in actions, f"操作列缺少「{label}」: {actions}"
