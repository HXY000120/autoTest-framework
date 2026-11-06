"""mis 后台审核端 - 文章详情离线用例（虚拟接口，CI 可稳定执行）。

真实环境同样提供 /wemedia/api/v1/news/one/{id}（后台视角），但之前缺少针对它的
独立用例。这里用 Mock Server 补齐：
    - 有效 id：返回 code=0 且数据完整（与 mp 发布的数据一致）
    - 无效 id：返回 code=1002 数据不存在
    - 状态过滤：审核通过后，status=4 的列表能查到、status=1 的查不到

所有请求仍走 MisEntry -> ApiMis -> ApiClient 完整链路，base_url 指向本地虚拟服务。
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
def pending_article(mock_server):
    """前置：用 mp 端发布一篇待审核文章，供 mis 查看与审核。"""
    mp = MpEntry(client=mock_server.client("mp"))
    mp.api.login(*MP_USER)
    aid = mp.api.publish_article("详情接口验证文章", "正文内容").json()["data"]["id"]
    return aid


@pytest.mark.api
@pytest.mark.mis
@pytest.mark.mock
def test_mis_news_detail_valid(mis_mock, pending_article):
    """有效 id：后台视角能读到文章详情，且与发布端数据一致。"""
    entry, _ = mis_mock
    aid = pending_article
    body = entry.api.news_one(aid).json()
    assert body["code"] == 0, f"有效 id 详情竟失败: {body}"
    data = body["data"]
    assert data["id"] == aid
    assert data["title"] == "详情接口验证文章"
    assert data["status"] == 1, "待审核文章详情状态应为 1"


@pytest.mark.api
@pytest.mark.mis
@pytest.mark.mock
def test_mis_news_detail_invalid(mis_mock):
    """无效 id：必须返回业务错误 1002，不得把错误包装成成功。"""
    entry, _ = mis_mock
    body = entry.api.news_one(99999999).json()
    assert body["code"] == 1002, f"无效 id 应返回 1002，实际 {body}"
    assert body["data"] is None


@pytest.mark.api
@pytest.mark.mis
@pytest.mark.mock
def test_mis_news_detail_no_token(mock_server):
    """未登录查看详情应被拒（真实 HTTP 401），不得泄露数据。"""
    from page.mis.api_mis import ApiMis

    api = ApiMis(mock_server.client("mis"))
    resp = api.news_one(9001)
    assert resp.status_code == 401
    assert resp.json()["code"] == 401


@pytest.mark.api
@pytest.mark.mis
@pytest.mark.mock
def test_mis_news_list_status_after_audit(mis_mock, pending_article, mock_server):
    """审核通过后：status=4 列表查得到，status=1 查不到（状态流转真实生效）。"""
    entry, _ = mis_mock
    aid = pending_article
    entry.api.audit_article_pass(aid)

    approved = entry.api.news_list(page=1, size=10, status=4).json()["data"]
    assert any(a["id"] == aid for a in approved), "审核通过后 status=4 过滤不到"
    pending = entry.api.news_list(page=1, size=10, status=1).json()["data"]
    assert not any(a["id"] == aid for a in pending), "审核通过后 status=1 仍出现"


@pytest.mark.api
@pytest.mark.mis
@pytest.mark.mock
def test_mis_news_detail_contract(mis_mock):
    """PO 契约：news_one 请求只带 id 且带 mis 端 token。"""
    entry, server = mis_mock
    entry.api.news_one(9001)
    reqs = [r for r in server.state.requests if r["path"].endswith("/news/one/9001")]
    assert len(reqs) == 1
    assert reqs[0]["headers"].get("token") == entry.api.client.token


@pytest.mark.api
@pytest.mark.mis
@pytest.mark.mock
def test_mis_news_detail_design_coverage():
    """离线守卫：有效/无效/鉴权/状态流转四类场景都要覆盖。"""
    # 名称即文档：本文件必须同时存在以上四类测试
    names = {
        "test_mis_news_detail_valid",
        "test_mis_news_detail_invalid",
        "test_mis_news_detail_no_token",
        "test_mis_news_list_status_after_audit",
    }
    import inspect
    import os

    src = inspect.getsource(inspect.getmodule(inspect.currentframe()))
    missing = [n for n in names if f"def {n}" not in src]
    assert not missing, f"缺少场景用例: {missing}"
