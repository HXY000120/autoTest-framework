"""mis 用户实名认证列表 - 分页 / 状态 / 字段契约用例（12 组数据驱动）。"""
import os

import pytest

from common.assertion import (
    assert_fields,
    assert_paging,
    assert_rejected_or_json,
)
from common.utils.data_reader import load_data

cases = load_data("mis/api/auth_list_cases.yaml")
RUN_REAL = os.getenv("RUN_REAL") == "1"


@pytest.mark.api
@pytest.mark.mis
@pytest.mark.skipif(not RUN_REAL, reason="设置 RUN_REAL=1 才跑真实接口")
@pytest.mark.parametrize("case", cases, ids=[c["case_id"] for c in cases])
def test_mis_auth_list_params(mis_api, case):
    """按 check 分支执行分页 / 字段契约 / 鲁棒性断言。"""
    mis_api.api.login()
    api = mis_api.api
    resp = api.post_raw(api.url_auth_list, case["payload"])
    check = case["check"]

    if check == "paging":
        assert_paging(resp, case["size"])
    elif check == "contract":
        data = assert_fields(resp, case.get("expect_fields", ["id"]))
        if data:
            assert isinstance(data[0], dict), "列表元素应为对象"
    else:  # robust：WAF 拦截(405)与合法 JSON 都算通过，5xx 一律不允许
        body = assert_rejected_or_json(resp, require_code=False)
        if body is not None:
            assert body, f"异常参数返回空响应体: {resp.text[:200]}"


@pytest.mark.api
@pytest.mark.mis
@pytest.mark.skipif(not RUN_REAL, reason="设置 RUN_REAL=1 才跑真实接口")
def test_mis_auth_list_status_filter(mis_api):
    """状态过滤：status=0 待审核的结果中每条 status 都应为 0（有数据时）。"""
    mis_api.api.login()
    from common.assertion import assert_list_data

    data = assert_list_data(
        mis_api.api.auth_list(page=1, size=10, status=0)
    )
    if data:
        assert all(item.get("status") == 0 for item in data), (
            f"status=0 过滤未生效，实际状态集合: {[i.get('status') for i in data]}"
        )


@pytest.mark.api
@pytest.mark.mis
def test_auth_list_case_contract():
    """离线守卫：分页/状态/非法参数三类场景都要覆盖。"""
    assert len(cases) >= 10
    checks = {c["check"] for c in cases}
    assert {"paging", "contract", "robust"} <= checks, f"覆盖不全: {checks}"
    for c in cases:
        assert isinstance(c.get("payload"), dict), f"{c['case_id']} 缺少 payload"
        if c["check"] == "paging":
            assert isinstance(c.get("size"), int) and c["size"] > 0, (
                f"{c['case_id']} paging 用例缺少有效 size"
            )
