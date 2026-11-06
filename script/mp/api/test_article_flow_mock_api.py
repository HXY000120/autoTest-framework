"""跨端完整业务闭环 - 虚拟接口用例。

真实环境跑不通的链路（发布接口维护中、mis 无待审核数据、APP 无接口服务）
在这里用同一个有状态的 Mock Server 串起来：

    mp 发布文章 -> mis 审核通过/驳回 -> 文章状态流转 -> APP 文章流可见性

所有请求仍走 entry 门面 + PO 封装，只是 base_url 指向本地虚拟服务。
"""
import pytest

from page.app.entry import AppEntry
from page.mis.entry import MisEntry
from page.mp.entry import MpEntry

MP_USER = ("demo", "mock_pwd_123")
MIS_USER = ("demo", "mock_admin_pwd_123")
APP_USER = ("13800138000", "246810")


@pytest.fixture
def flow(mock_server):
    """三端 entry 共享同一个有状态虚拟服务。"""
    mp = MpEntry(client=mock_server.client("mp"))
    mis = MisEntry(client=mock_server.client("mis"))
    app = AppEntry(client=mock_server.client("app"))
    mp.api.login(*MP_USER)
    mis.api.login(*MIS_USER)
    app.api.login(*APP_USER)
    return mp, mis, app, mock_server


@pytest.mark.api
@pytest.mark.mp
@pytest.mark.mock
def test_full_flow_publish_audit_visible(flow):
    """主流程：发布 -> 待审核 -> 审核通过 -> APP 可见。"""
    mp, mis, app, server = flow
    aid = mp.api.publish_article("闭环验证文章", "正文内容").json()["data"]["id"]
    assert server.state.find_article(aid)["status"] == 1

    before = app.api.article_list().json()["data"]
    assert not any(a["id"] == aid for a in before), "待审核文章不应出现在 APP 文章流"

    body = mis.api.audit_article_pass(aid).json()
    assert body["code"] == 0 and body["data"]["status"] == 4
    assert server.state.audit_log[-1]["to_status"] == 4

    after = app.api.article_list().json()["data"]
    assert any(a["id"] == aid for a in after), "审核通过后 APP 文章流仍看不到该文章"
    approved = mp.api.news_list(page=1, size=10, status=4).json()["data"]
    assert any(a["id"] == aid for a in approved), "按 status=4 过滤不到已通过文章"


@pytest.mark.api
@pytest.mark.mp
@pytest.mark.mock
def test_audit_reject_flow(flow):
    """驳回分支：记录原因、状态=2、APP 流不可见。"""
    mp, mis, app, server = flow
    aid = mp.api.publish_article("驳回分支验证", "正文").json()["data"]["id"]

    body = mis.api.audit_article_fail(aid, "内容不符合规范").json()
    assert body["code"] == 0 and body["data"]["status"] == 2
    log = server.state.audit_log[-1]
    assert log["action"] == "fail" and log["from_status"] == 1
    assert log["msg"] == "内容不符合规范", "驳回原因未透传到服务端"
    assert not any(a["id"] == aid for a in app.api.article_list().json()["data"])


@pytest.mark.api
@pytest.mark.mp
@pytest.mark.mock
def test_audit_missing_id_rejected(flow):
    """审核不存在的 id 必须返回业务错误，且不得产生审核日志。"""
    _, mis, _, server = flow
    body = mis.api.audit_article_pass(99999999).json()
    assert body["code"] == 1002
    assert not server.state.audit_log


@pytest.mark.api
@pytest.mark.mp
@pytest.mark.mock
def test_paging_and_keyword(flow):
    """发布 3 篇后校验分页与关键词过滤真的生效。"""
    mp, _, _, _ = flow
    for title in ("华山游记一", "华山游记二", "西湖游记"):
        assert mp.api.publish_article(title, "正文").json()["code"] == 0

    page1 = mp.api.news_list(page=1, size=2).json()["data"]
    page2 = mp.api.news_list(page=2, size=2).json()["data"]
    assert len(page1) == 2 and len(page2) == 1
    assert not ({a["id"] for a in page1} & {a["id"] for a in page2}), "相邻页出现重复文章"

    hits = mp.api.search_articles("华山", page=1, size=10).json()["data"]
    assert len(hits) == 2 and all("华山" in a["title"] for a in hits)


@pytest.mark.api
@pytest.mark.mp
@pytest.mark.mock
def test_article_detail_and_toggle(flow):
    """详情读取、上下架状态修改、非法 id 处理。"""
    mp, _, _, server = flow
    aid = mp.api.publish_article("详情与上下架验证", "正文").json()["data"]["id"]

    detail = mp.api.news_one(aid).json()
    assert detail["code"] == 0 and detail["data"]["title"] == "详情与上下架验证"
    assert mp.api.news_one(99999999).json()["code"] == 1002

    assert mp.api.down_or_up(aid, 0).json()["code"] == 0
    assert server.state.find_article(aid)["enable"] == 0
    assert mp.api.down_or_up(99999999, 1).json()["code"] == 501


@pytest.mark.api
@pytest.mark.mp
@pytest.mark.mock
def test_cross_end_token_isolated(flow):
    """跨端越权：mp 的 token 打到 mis 网关路径应被拒（403）。"""
    mp, _, _, server = flow
    from base.api_base import ApiClient

    mixed = ApiClient(end="mis")
    mixed.base_url = server.url
    mixed.session.trust_env = False
    mixed.set_token(mp.api.client.token)
    resp = mixed.post("/admin/api/v1/whatever", json={})
    assert resp.status_code == 403, "跨端 token 混用未被拦截"
