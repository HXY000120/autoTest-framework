"""mp 登录接口 - 异常/边界参数用例（等价类 + 边界值 + 判定表 + 安全性）。

断言策略：不写死错误码，而是抓两条红线
    1. 服务端不得 5xx（异常参数不能打垮服务）
    2. 不得下发 token（异常参数不能越权登录成功）
"""
import os

import pytest

from common.assertion import assert_login_failed
from common.utils.data_reader import load_data

cases = load_data("mp/api/login_param_cases.yaml")
RUN_REAL = os.getenv("RUN_REAL") == "1"


@pytest.mark.api
@pytest.mark.mp
@pytest.mark.skipif(not RUN_REAL, reason="设置 RUN_REAL=1 才跑真实接口")
@pytest.mark.parametrize("case", cases, ids=[c["case_id"] for c in cases])
def test_mp_login_invalid_params(mp_api, case):
    """任何一组异常参数都不得登录成功。"""
    resp = mp_api.api.post_raw(mp_api.api.url_login, case["payload"])
    assert_login_failed(resp)


@pytest.mark.api
@pytest.mark.mp
def test_login_param_design_coverage():
    """离线守卫：用例数据必须覆盖 4 类设计方法，防止数据被误删后用例"缩水"。"""
    methods = {c["method"].split("-")[0] for c in cases}
    assert {"等价类", "边界值", "判定表", "安全性"} <= methods, (
        f"用例设计方法覆盖不全: {methods}"
    )
    assert len(cases) >= 10, f"登录异常用例只有 {len(cases)} 条，覆盖不足"
    assert len({c["case_id"] for c in cases}) == len(cases), "用例编号重复"


@pytest.mark.api
@pytest.mark.mp
def test_login_param_payload_contract():
    """离线守卫：每条用例必须有 payload 且为字典，避免 YAML 写错导致假跑。"""
    for c in cases:
        payload = c.get("payload")
        assert isinstance(payload, dict), f"{c['case_id']} 缺少 payload"
        assert set(payload) <= {"name", "password"}, (
            f"{c['case_id']} 出现非登录字段: {set(payload)}"
        )
        for key, value in payload.items():
            assert isinstance(value, str), (
                f"{c['case_id']}.{key} 应为字符串，实际 {type(value)}"
            )
