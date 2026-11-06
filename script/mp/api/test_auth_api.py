"""mp 鉴权链路用例：验证 Token 提取与鉴权复用的边界（简历核心项）。

实测环境特性：
    - 只认 `token` 请求头，Authorization: Bearer 返回 401
    - 未登录访问业务接口 HTTP 401（无响应体）
断言不写死 401：不同网关对伪造 token 可能返回 401/403 或业务错误码，
统一红线是「不得返回有效业务数据」。
"""
import os

import pytest

from base.api_base import ApiClient
from common.assertion import assert_no_server_error, assert_response_json
from common.utils.data_reader import load_data
from page.mis.api_mis import ApiMis
from page.mp.api_mp import ApiMp

cases = load_data("mp/api/auth_cases.yaml")
RUN_REAL = os.getenv("RUN_REAL") == "1"


def _assert_rejected(resp):
    assert_no_server_error(resp)
    if resp.status_code in (401, 403, 405):
        return  # 网关直接拒绝，符合预期
    body = assert_response_json(resp, require_code=False)
    if body.get("code") in (0, 200):
        data = body.get("data")
        assert not (isinstance(data, list) and data), (
            f"越权：非法 token 竟返回业务数据 {resp.text[:200]}"
        )


@pytest.mark.api
@pytest.mark.mp
@pytest.mark.skipif(not RUN_REAL, reason="设置 RUN_REAL=1 才跑真实接口")
@pytest.mark.parametrize("case", cases, ids=[c["case_id"] for c in cases])
def test_mp_auth_rejects_invalid_token(case):
    """5 种非法/跨端 token 全部不得拿到业务数据。"""
    client = ApiClient(end="mp")
    api = ApiMp(client)
    mode = case["token_mode"]

    if mode == "none":
        pass
    elif mode == "empty":
        client.headers["token"] = ""
    elif mode == "forged":
        client.set_token("forged_token_for_auth_test")
    elif mode == "bearer":
        client.headers.pop("token", None)
        client.headers["Authorization"] = "Bearer forged_token_for_auth_test"
    elif mode == "cross_end":
        mis = ApiMis(ApiClient(end="mis"))
        mis.login()
        assert mis.client.token, "前置条件失败：mis 端未取到 token"
        client.headers["token"] = mis.client.token
    else:
        pytest.fail(f"未支持的 token_mode: {mode}")

    _assert_rejected(api.news_list(page=1, size=5))


@pytest.mark.api
@pytest.mark.mp
@pytest.mark.skipif(not RUN_REAL, reason="设置 RUN_REAL=1 才跑真实接口")
def test_mp_valid_token_grants_access(mp_api):
    """对照组：合法 token 必须能拿到数据，否则上面的拒绝用例没有意义。"""
    mp_api.api.login()
    assert mp_api.api.client.token, "登录成功但未取到 token"
    from common.assertion import assert_list_data

    assert_list_data(mp_api.api.news_list(page=1, size=5))
