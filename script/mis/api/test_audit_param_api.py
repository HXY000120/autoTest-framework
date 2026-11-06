"""mis 审核动作 - 参数与异常用例（8 组数据驱动）。

安全约束：所有写操作都用不存在的 id 或缺字段，绝不改动真实审核数据。
"""
import os

import pytest

from common.assertion import assert_no_server_error, assert_response_json
from common.utils.data_reader import load_data

cases = load_data("mis/api/audit_param_cases.yaml")
RUN_REAL = os.getenv("RUN_REAL") == "1"

# path_key -> ApiMis 上的 URL 属性名
PATH_MAP = {
    "news_pass": "url_news_auth_pass",
    "news_fail": "url_news_auth_fail",
    "auth_pass": "url_auth_pass",
    "auth_fail": "url_auth_fail",
}


@pytest.mark.api
@pytest.mark.mis
@pytest.mark.skipif(not RUN_REAL, reason="设置 RUN_REAL=1 才跑真实接口")
@pytest.mark.parametrize("case", cases, ids=[c["case_id"] for c in cases])
def test_mis_audit_params(mis_api, case):
    """接口必须活着；对不存在的 id 不得返回「操作成功」。"""
    mis_api.api.login()
    api = mis_api.api
    path = getattr(api, PATH_MAP[case["path_key"]])
    resp = api.post_raw(path, case["payload"])

    assert_no_server_error(resp)
    assert resp.status_code not in (404, 405), (
        f"审核接口路径失效 HTTP {resp.status_code}: {resp.text[:120]}"
    )
    body = assert_response_json(resp, require_code=False)

    if case["check"] == "reject":
        # 实测：不存在 id 返回 code=1002「数据不存在」；若返回 0/200 说明后端漏校验
        assert body.get("code") not in (0, 200), (
            f"不存在的 id 竟被审核操作成功: {resp.text[:200]}"
        )


@pytest.mark.api
@pytest.mark.mis
def test_audit_case_contract():
    """离线守卫：所有写操作用例都不得引用真实 id，且路径映射必须完整。"""
    for c in cases:
        assert c["path_key"] in PATH_MAP, f"{c['case_id']} 路径映射缺失"
        assert isinstance(c.get("payload"), dict), f"{c['case_id']} 缺少 payload"
        aid = c["payload"].get("id")
        assert aid is None or aid in (0, "not_a_number") or aid >= 99999999, (
            f"{c['case_id']} 使用了可能是真实数据的 id: {aid}"
        )
