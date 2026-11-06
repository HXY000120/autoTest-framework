"""app 用户端 - 虚拟接口用例。

真实环境未部署 APP 端自有接口服务（UI 改用网易新闻 App），原先该端只有
接口对象契约单测。这里用虚拟服务补齐登录与文章流，形成能跑的 APP 接口链路。
"""
import pytest

from page.app.entry import AppEntry

APP_USER = ("13800138000", "246810")


@pytest.fixture
def app_mock(mock_server):
    return AppEntry(client=mock_server.client("app")), mock_server


@pytest.mark.api
@pytest.mark.app_end
@pytest.mark.mock
def test_app_login_success(app_mock):
    """登录成功返回 token，并自动注入后续请求头。"""
    entry, _ = app_mock
    body = entry.api.login(*APP_USER).json()
    assert body["code"] == 0
    assert body["data"]["token"]
    assert entry.api.client.token == body["data"]["token"]


@pytest.mark.api
@pytest.mark.app_end
@pytest.mark.mock
@pytest.mark.parametrize("mobile,code", [
    ("13800138000", "000000"),
    ("13900000000", "246810"),
    ("", "246810"),
])
def test_app_login_invalid(app_mock, mobile, code):
    """无效等价类：验证码错误 / 手机号不存在 / 空手机号均不得下发 token。"""
    entry, _ = app_mock
    body = entry.api.login(mobile, code).json()
    assert body["code"] == 2
    assert not entry.api.client.token


@pytest.mark.api
@pytest.mark.app_end
@pytest.mark.mock
def test_app_login_payload_stringified(app_mock):
    """契约：手机号与验证码以字符串送达，前导零不丢失。"""
    entry, server = app_mock
    entry.api.login("013800138000", 246810)
    login_reqs = [r for r in server.state.requests if r["path"].endswith("authorizations")]
    payload = login_reqs[-1]["payload"]
    assert payload["mobile"] == "013800138000"
    assert payload["code"] == "246810" and isinstance(payload["code"], str)


@pytest.mark.api
@pytest.mark.app_end
@pytest.mark.mock
def test_app_articles_requires_token(app_mock):
    """未登录拉取文章流应被拒（HTTP 401）。"""
    entry, _ = app_mock
    assert entry.api.article_list().status_code == 401


@pytest.mark.api
@pytest.mark.app_end
@pytest.mark.mock
def test_app_articles_only_approved(app_mock):
    """文章流只应返回审核通过/已发布内容，待审核文章不得泄漏。"""
    entry, server = app_mock
    approved = server.state.add_article(title="已通过文章", content="正文", status=4)
    pending = server.state.add_article(title="待审核文章", content="正文", status=1)
    server.state.add_article(title="已发布文章", content="正文", status=9)
    entry.api.login(*APP_USER)

    data = entry.api.article_list().json()["data"]
    ids = {a["id"] for a in data}
    assert approved["id"] in ids
    assert pending["id"] not in ids, "待审核文章泄漏到了 APP 文章流"
    assert len(ids) == 2, "文章流条数不符合状态过滤"


@pytest.mark.api
@pytest.mark.app_end
@pytest.mark.mock
def test_app_state_endpoint(app_mock):
    """虚拟服务自身契约：状态查询端点能反映真实请求数，防止 mock 变成摆设。"""
    entry, server = app_mock
    entry.api.login(*APP_USER)
    snapshot = entry.api.client.get("/__mock__/state").json()["data"]
    assert snapshot["token_count"] >= 1
    assert len(snapshot["requests"]) >= 2  # 登录 + 本次 state 查询
