"""mp 自媒体端 - 接口登录用例（PO 调用 + 断言，不碰请求细节）。

真实环境行为（实测）：
    正确账号    HTTP 200, code=0, data.token 有值
    错误密码    HTTP 200, code=2, errorMessage="密码错误"
    未登录访问  HTTP 401（无 body），因此鉴权断言要看状态码而非业务码
"""
import os

import pytest

from common.assertion import assert_biz_code, assert_status
from common.config.settings import get_endpoint
from common.utils.data_reader import load_data

cases = load_data("mp/api/login_cases.yaml")
RUN_REAL = os.getenv("RUN_REAL") == "1"


@pytest.mark.api
@pytest.mark.mp
def test_mp_login_structure(mp_api):
    """结构校验：接口路径固定、域名按端配置注入（离线可跑，能抓出 PO 改坏）。"""
    api = mp_api.api
    ep = get_endpoint("mp")
    assert api.url_login == "/wemedia/login/in"
    assert api.url_news_list == "/wemedia/api/v1/news/list"
    assert api.client.base_url == ep["base_url"], "base_url 未按端配置注入"
    assert api.client.api_prefix == ep["api_prefix"]


@pytest.mark.api
@pytest.mark.mp
@pytest.mark.skipif(not RUN_REAL, reason="设置 RUN_REAL=1 才跑真实接口")
@pytest.mark.parametrize("case", cases)
def test_mp_login_real(mp_api, case):
    """真实登录：成功拿 token 并注入请求头，失败返回 code=2。"""
    if case["use_config"]:
        resp = mp_api.api.login()          # 密码按当天日期动态生成
    else:
        resp = mp_api.api.login("demo", case["password"])

    if case["expect_success"]:
        body = assert_biz_code(resp, 0)
        token = (body.get("data") or {}).get("token")
        assert token, f"登录成功但未返回 token: {resp.text[:200]}"
        # token 必须落到 client 头上，否则后续接口仍会 401
        assert mp_api.api.client.headers.get("token") == token, "token 未注入 client 请求头"
    else:
        body = resp.json()
        assert body.get("code") == 2, (
            f"错误密码应返回 code=2（密码错误），实际 {body.get('code')}: {resp.text[:200]}"
        )


@pytest.mark.api
@pytest.mark.mp
@pytest.mark.skipif(not RUN_REAL, reason="设置 RUN_REAL=1 才跑真实接口")
def test_mp_access_without_login(mp_api):
    """未登录访问文章列表应被拒绝：验证鉴权真实生效（HTTP 401）。"""
    resp = mp_api.api.news_list(page=1, size=5)
    assert_status(resp, 401)
