"""mis 后台登录 - 异常/边界参数用例（等价类 + 边界值 + 判定表 + 安全性）。"""
import os

import pytest

from common.assertion import assert_login_failed
from common.utils.data_reader import load_data

cases = load_data("mis/api/login_param_cases.yaml")
RUN_REAL = os.getenv("RUN_REAL") == "1"


@pytest.mark.api
@pytest.mark.mis
@pytest.mark.skipif(not RUN_REAL, reason="设置 RUN_REAL=1 才跑真实接口")
@pytest.mark.parametrize("case", cases, ids=[c["case_id"] for c in cases])
def test_mis_login_invalid_params(mis_api, case):
    """异常参数不得下发 token，服务端不得 5xx。"""
    resp = mis_api.api.post_raw(mis_api.api.url_login, case["payload"])
    assert_login_failed(resp)


@pytest.mark.api
@pytest.mark.mis
def test_mis_login_param_contract():
    """离线守卫：数据必须覆盖 4 类设计方法且字段类型正确。"""
    methods = {c["method"].split("-")[0] for c in cases}
    assert {"等价类", "边界值", "判定表", "安全性"} <= methods, (
        f"用例设计方法覆盖不全: {methods}"
    )
    assert len(cases) >= 8
    for c in cases:
        payload = c.get("payload")
        assert isinstance(payload, dict), f"{c['case_id']} 缺少 payload"
        assert set(payload) <= {"name", "password"}
        for key, value in payload.items():
            assert isinstance(value, str), (
                f"{c['case_id']}.{key} 应为字符串，实际 {type(value)}"
            )
