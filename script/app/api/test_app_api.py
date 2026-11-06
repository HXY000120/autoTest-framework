"""app 用户端接口对象 - 契约与参数单测（离线可跑，不依赖真实服务）。

说明：本被测环境的 APP 端用示例新闻 App做 UI 自动化，没有配套的自有接口服务。
因此这里用 FakeClient 验证「接口对象是否正确组装请求」，而不是伪造
已联调的假数据。配好 endpoints.app.base_url 后，最后一条用例自动转为真实联调。
"""
import pytest

from common.config.settings import get_endpoint
from page.app.api_app import ApiApp
from page.app.entry import AppEntry


class _FakeResp:
    status_code = 200
    text = '{"code": 0}'

    def json(self):
        return {"code": 0}


class _FakeClient:
    def __init__(self):
        self.calls = []
        self.token = None

    def post(self, path, **kwargs):
        self.calls.append((path, kwargs))
        return _FakeResp()

    def set_token(self, token):
        self.token = token


@pytest.fixture
def fake_app():
    client = _FakeClient()
    return client, AppEntry(client=client).api


@pytest.mark.api
@pytest.mark.app_end
def test_app_login_payload(fake_app):
    """登录请求必须打到配置路径，且 mobile/code 原样放进 json body。"""
    client, api = fake_app
    api.login("13800138000", "246810")
    assert len(client.calls) == 1, "login 应只发一次请求"
    path, kwargs = client.calls[0]
    assert path == api.url_login
    assert kwargs["json"] == {"mobile": "13800138000", "code": "246810"}


@pytest.mark.api
@pytest.mark.app_end
def test_app_login_stringifies_params(fake_app):
    """数值型验证码、带前导零的账号都不得丢失字符。"""
    client, api = fake_app
    api.login("013800138000", 246810)
    payload = client.calls[0][1]["json"]
    assert payload["mobile"] == "013800138000", "前导零丢失"
    assert payload["code"] == "246810", "数值型验证码未转字符串"


@pytest.mark.api
@pytest.mark.app_end
def test_app_login_injects_token():
    """登录成功后 token 必须自动注入 client（与 mp/mis 行为一致）。"""
    class _TokenResp(_FakeResp):
        def json(self):
            return {"code": 0, "data": {"token": "tk_mock_123"}}

    class _TokenClient(_FakeClient):
        def post(self, path, **kwargs):
            self.calls.append((path, kwargs))
            return _TokenResp()

    client = _TokenClient()
    ApiApp(client=client).login("13800138000", "246810")
    assert client.token == "tk_mock_123", "登录成功但未自动复用 token"


@pytest.mark.api
@pytest.mark.app_end
def test_app_api_client_injection(fake_app):
    """接口对象必须支持外部 client 注入（Locust 复用同一套 API Object 的前提）。"""
    client, api = fake_app
    assert api.client is client
    assert callable(api.login)


@pytest.mark.api
@pytest.mark.app_end
def test_app_endpoint_config_contract():
    """配置契约：app 段必须存在且声明 login_path，否则接入真实服务时会拼错 URL。"""
    ep = get_endpoint("app")
    assert "base_url" in ep and "api_prefix" in ep
    assert ep.get("login_path"), "app 段缺少 login_path"
    api = ApiApp(client=_FakeClient())
    assert api.url_login == ep["login_path"]
    assert api.configured is bool(ep["base_url"])


@pytest.mark.api
@pytest.mark.app_end
def test_app_real_login_gated(app_api):
    """真实 APP 端登录：仅在配置了 base_url 时执行，未配置则明示原因跳过。"""
    ep = get_endpoint("app")
    if not ep["base_url"]:
        pytest.skip(
            "当前环境未部署 APP 端接口服务（UI 用示例新闻 App替代）；"
            "配置 endpoints.app.base_url 后本用例自动转为真实联调"
        )
    resp = app_api.api.login("13800138000", "246810")
    assert resp.status_code < 500
    assert "code" in resp.json()
