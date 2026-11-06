"""mis 后台审核 - 虚拟接口用例。

真实环境里审核列表为空、行内按钮 disabled、authPass 接口维护中，
导致「审核」只能验到列表存在。这里用虚拟接口把审核动作与状态流转跑通。
"""
import pytest

from page.mis.entry import MisEntry
from page.mp.entry import MpEntry

MIS_USER = ("demo", "mock_admin_pwd_123")
MP_USER = ("demo", "mock_pwd_123")


@pytest.fixture
def mis_mock(mock_server):
    entry = MisEntry(client=mock_server.client("mis"))
    entry.api.login(*MIS_USER)
    return entry, mock_server


@pytest.fixture
def with_pending_article(mock_server):
    """前置：先用 mp 端发布一篇待审核文章，供 mis 审核。"""
    mp = MpEntry(client=mock_server.client("mp"))
    mp.api.login(*MP_USER)
    aid = mp.api.publish_article("待审核文章", "正文").json()["data"]["id"]
    return aid


@pytest.mark.api
@pytest.mark.mis
@pytest.mark.mock
def test_audit_pass_changes_status(mis_mock, with_pending_article, mock_server):
    """审核通过：服务端状态 1 -> 4，且写入审核日志。"""
    entry, _ = mis_mock
    aid = with_pending_article
    body = entry.api.audit_article_pass(aid).json()
    assert body["code"] == 0
    assert mock_server.state.find_article(aid)["status"] == 4
    assert mock_server.state.audit_log[-1]["action"] == "pass"


@pytest.mark.api
@pytest.mark.mis
@pytest.mark.mock
def test_audit_fail_keeps_reason(mis_mock, with_pending_article, mock_server):
    """审核驳回：状态改为 2，驳回原因必须透传。"""
    entry, _ = mis_mock
    aid = with_pending_article
    body = entry.api.audit_article_fail(aid, "标题与正文不符").json()
    assert body["code"] == 0
    assert mock_server.state.find_article(aid)["status"] == 2
    assert mock_server.state.audit_log[-1]["msg"] == "标题与正文不符"


@pytest.mark.api
@pytest.mark.mis
@pytest.mark.mock
def test_audit_missing_id(mis_mock, mock_server):
    """不存在的文章 id：返回 1002，不得写入审核日志。"""
    entry, _ = mis_mock
    assert entry.api.audit_article_pass(99999999).json()["code"] == 1002
    assert not mock_server.state.audit_log


@pytest.mark.api
@pytest.mark.mis
@pytest.mark.mock
def test_audit_payload_contract(mis_mock, with_pending_article, mock_server):
    """PO 契约：审核请求只带 id/msg，且带 mis 端 token。"""
    entry, _ = mis_mock
    entry.api.audit_article_fail(with_pending_article, "原因")
    reqs = [r for r in mock_server.state.requests if "auth_fail" in r["path"]]
    assert len(reqs) == 1
    assert set(reqs[0]["payload"]) == {"id", "msg"}
    assert reqs[0]["headers"].get("token") == entry.api.client.token


@pytest.mark.api
@pytest.mark.mis
@pytest.mark.mock
@pytest.mark.parametrize("status,expect_count", [(0, 1), (1, 1), (2, 0)])
def test_auth_list_status_filter(mis_mock, status, expect_count):
    """用户实名认证列表：status 过滤应真实生效。"""
    entry, _ = mis_mock
    data = entry.api.auth_list(page=1, size=10, status=status).json()["data"]
    assert len(data) == expect_count
    assert all(row["status"] == status for row in data)


@pytest.mark.api
@pytest.mark.mis
@pytest.mark.mock
@pytest.mark.parametrize("path_key", ["auth_pass", "auth_fail"])
def test_user_auth_actions_available(mis_mock, path_key):
    """真实环境维护中的 authPass / 正常可用的 authFail，在虚拟服务里都能跑通。"""
    entry, _ = mis_mock
    api = entry.api
    resp = api.auth_pass(7001) if path_key == "auth_pass" else api.auth_fail(7001, "原因")
    assert resp.json()["code"] == 0


@pytest.mark.api
@pytest.mark.mis
@pytest.mark.mock
def test_mis_login_and_token_required(mock_server):
    """错误密码不得下发 token；未登录访问审核接口应 401。"""
    from page.mis.api_mis import ApiMis

    api = ApiMis(mock_server.client("mis"))
    wrong = api.login("demo", "bad_pwd").json()
    assert wrong["code"] == 2 and not api.client.token

    another = ApiMis(mock_server.client("mis"))
    assert another.news_list(page=1, size=5).status_code == 401
