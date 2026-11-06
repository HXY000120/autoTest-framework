"""mis 后台审核端 - 接口登录用例。

真实环境行为（实测）：
    正确账号    HTTP 200, code=0, data.token 有值
    错误密码    HTTP 200, code=2, errorMessage="密码错误"
    未登录访问  HTTP 401
"""
import os

import pytest

from common.assertion import assert_biz_code, assert_status
from common.utils.data_reader import load_data

cases = load_data("mis/api/login_cases.yaml")
RUN_REAL = os.getenv("RUN_REAL") == "1"


@pytest.mark.api
@pytest.mark.mis
def test_mis_login_structure(mis_api):
    """结构校验：接口路径与域名指向真实环境（离线可跑）。"""
    api = mis_api.api
    assert api.url_login == "/admin/login/in"
    assert api.client.base_url == "https://heima-admin-java.itheima.net"
    assert api.client.api_prefix == "/service_6001"


@pytest.mark.api
@pytest.mark.mis
@pytest.mark.skipif(not RUN_REAL, reason="设置 RUN_REAL=1 才跑真实接口")
@pytest.mark.parametrize("case", cases)
def test_mis_login_real(mis_api, case):
    """真实登录：成功拿 token 并注入请求头，失败返回 code=2。"""
    if case["use_config"]:
        resp = mis_api.api.login()
    else:
        resp = mis_api.api.login("demo", case["password"])

    if case["expect_success"]:
        body = assert_biz_code(resp, 0)
        token = (body.get("data") or {}).get("token")
        assert token, f"登录成功但未返回 token: {resp.text[:200]}"
        assert mis_api.api.client.headers.get("token") == token, "token 未注入 client 请求头"
    else:
        body = resp.json()
        assert body.get("code") == 2, (
            f"错误密码应返回 code=2（密码错误），实际 {body.get('code')}: {resp.text[:200]}"
        )


@pytest.mark.api
@pytest.mark.mis
@pytest.mark.skipif(not RUN_REAL, reason="设置 RUN_REAL=1 才跑真实接口")
def test_mis_access_without_login(mis_api):
    """未登录访问审核列表应被拒绝：验证鉴权真实生效（HTTP 401）。"""
    assert_status(mis_api.api.auth_list(page=1, size=5), 401)
