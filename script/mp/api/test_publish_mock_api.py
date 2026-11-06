"""mp 发布文章 - 虚拟接口用例（不依赖外部环境，CI 可稳定执行）。

真实环境的 news/submit 返回 code=900001「系统维护中」，因此这条业务链路
原先只能 skip。这里用 common/mock 的本地 HTTP 服务补齐接口：
    - 请求仍经过 MpEntry -> ApiMp -> ApiClient 的完整 URL/headers/JSON 链路
    - 只把 base_url 换成 Mock Server 地址，PO 代码零改动
    - 服务端有状态，可断言「文章确实被创建」而不只是看返回码
"""
import pytest

from common.assertion import assert_biz_code
from common.utils.data_reader import load_data
from page.mp.api_mp import ApiMp
from page.mp.entry import MpEntry

cases = load_data("mp/api/publish_mock_cases.yaml")
MOCK_USER = ("demo", "mock_pwd_123")


@pytest.fixture
def mock_mp(mock_server):
    """通过 entry 门面登录，后续用例统一走 entry.api，符合框架分层约定。"""
    entry = MpEntry(client=mock_server.client("mp"))
    entry.api.login(*MOCK_USER)
    return entry, mock_server


@pytest.mark.api
@pytest.mark.mp
@pytest.mark.mock
@pytest.mark.parametrize("case", cases, ids=[c["case_id"] for c in cases])
def test_publish_validation_mock(mock_mp, case):
    """判定表：校验失败不得创建文章，成功必须真的落一条数据。"""
    entry, server = mock_mp
    api = entry.api
    before = len(server.state.articles)

    body = api.publish_article(case["title"], case["content"]).json()
    assert body.get("code") == case["expect_code"], (
        f"「{case['desc']}」业务码期望 {case['expect_code']}，实际 {body}"
    )
    assert len(server.state.articles) - before == case["expect_delta"], (
        f"「{case['desc']}」服务端文章数变化与预期不符"
    )
    if case["expect_code"] == 0:
        created = server.state.articles[-1]
        assert created["title"] == case["title"]
        assert created["status"] == 1, "新发布文章应为待审核状态"


@pytest.mark.api
@pytest.mark.mp
@pytest.mark.mock
def test_publish_payload_contract_mock(mock_mp):
    """PO 契约：发布的 payload 字段齐全，且登录 token 已注入请求头。"""
    entry, server = mock_mp
    api = entry.api
    assert_biz_code(api.publish_article("契约校验文章", "正文"), 0)

    submits = [r for r in server.state.requests if r["path"].endswith("news/submit")]
    assert len(submits) == 1
    payload = submits[0]["payload"]
    assert {"title", "content", "channelId", "labels", "type", "images"} <= set(payload)
    assert payload["title"] == "契约校验文章"
    assert submits[0]["headers"].get("token") == api.client.token


@pytest.mark.api
@pytest.mark.mp
@pytest.mark.mock
def test_publish_without_token_mock(mock_server):
    """未登录直接发布应被拒（真实 HTTP 401）。"""
    api = ApiMp(mock_server.client("mp"))
    resp = api.publish_article("未登录文章", "正文")
    assert resp.status_code == 401
    assert not mock_server.state.articles, "未登录请求竟创建了文章"


@pytest.mark.api
@pytest.mark.mp
@pytest.mark.mock
def test_publish_then_list_mock(mock_mp):
    """业务闭环第一段：发布后必须能在文章列表查到。"""
    entry, _ = mock_mp
    api = entry.api
    article_id = api.publish_article("发布后可见性验证", "正文").json()["data"]["id"]

    data = api.news_list(page=1, size=10).json()["data"]
    assert any(a["id"] == article_id for a in data), "发布成功但列表查不到"
    hit = api.search_articles("可见性", page=1, size=10).json()["data"]
    assert any(a["id"] == article_id for a in hit), "按关键词搜索不到刚发布的文章"


@pytest.mark.api
@pytest.mark.mp
@pytest.mark.mock
def test_publish_mock_case_contract():
    """离线守卫：判定表与边界值都要覆盖，且成功/失败场景均有数据。"""
    methods = {c["method"] for c in cases}
    assert {"判定表", "边界值"} <= methods
    assert any(c["expect_delta"] == 1 for c in cases)
    assert any(c["expect_delta"] == 0 for c in cases)
