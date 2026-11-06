"""mp 文章列表 - 分页 / 状态 / 关键词 参数用例（18 组数据驱动）。

实测依据：该后端真正的搜索字段是 keyword，title/name/search 会被忽略；
分页 size 生效。用例对「生效的参数」做强断言，对「非法参数」做鲁棒性断言。
"""
import os

import pytest

from common.assertion import (
    assert_fields,
    assert_list_data,
    assert_paging,
    assert_rejected_or_json,
)
from common.utils.data_reader import load_data

cases = load_data("mp/api/news_list_cases.yaml")
RUN_REAL = os.getenv("RUN_REAL") == "1"


@pytest.mark.api
@pytest.mark.mp
@pytest.mark.skipif(not RUN_REAL, reason="设置 RUN_REAL=1 才跑真实接口")
@pytest.mark.parametrize("case", cases, ids=[c["case_id"] for c in cases])
def test_mp_news_list_params(mp_api, case):
    """按 check 分支执行对应断言。"""
    mp_api.api.login()  # 每条用例独立登录，避免用例间共享登录态
    api = mp_api.api
    resp = api.post_raw(api.url_news_list, case["payload"])
    check = case["check"]

    if check == "paging":
        assert_paging(resp, case["size"])
    elif check == "contract":
        assert_fields(resp, ["title"])
    elif check == "keyword_hit":
        data = assert_list_data(resp)
        assert data, f"关键词「{case['keyword']}」应命中至少 1 条，实际 0 条"
        assert any(
            case["keyword"] in (item.get("title") or "") for item in data
        ), f"命中结果的标题均不含「{case['keyword']}」，过滤未生效"
    elif check == "keyword_miss":
        data = assert_list_data(resp)
        assert data == [], f"不存在的关键词竟返回 {len(data)} 条，过滤未生效"
    else:  # robust：非法参数不得打垮服务；WAF 拦截(405)与合法 JSON 都算通过
        body = assert_rejected_or_json(resp, require_code=False)
        if body is not None:
            assert body, f"异常参数返回空响应体: {resp.text[:200]}"


@pytest.mark.api
@pytest.mark.mp
@pytest.mark.skipif(not RUN_REAL, reason="设置 RUN_REAL=1 才跑真实接口")
def test_keyword_roundtrip(mp_api):
    """动态关键词：从列表首条标题取片段回查，不依赖硬编码数据。"""
    mp_api.api.login()
    full = assert_list_data(mp_api.api.news_list(page=1, size=10))
    assert full, "文章列表无数据，无法做关键词回查"
    title = full[0].get("title") or ""
    keyword = title[:2]
    assert keyword, f"首条文章没有标题: {full[0]}"

    hit = assert_list_data(mp_api.api.search_articles(keyword))
    assert hit, f"用真实标题片段「{keyword}」搜索却无结果"
    assert any(keyword in (i.get("title") or "") for i in hit), (
        f"搜索「{keyword}」返回的结果标题均不含该片段"
    )


@pytest.mark.api
@pytest.mark.mp
@pytest.mark.skipif(not RUN_REAL, reason="设置 RUN_REAL=1 才跑真实接口")
def test_paging_no_duplicate(mp_api):
    """分页边界：相邻两页的文章 id 不应重复（数据足够时才校验）。"""
    mp_api.api.login()
    page1 = assert_list_data(mp_api.api.news_list(page=1, size=2))
    page2 = assert_list_data(mp_api.api.news_list(page=2, size=2))
    if len(page1) < 2 or not page2:
        pytest.skip("环境数据不足 2 页，无法校验分页去重")
    ids1 = {i.get("id") for i in page1}
    ids2 = {i.get("id") for i in page2}
    assert not (ids1 & ids2), f"相邻页出现重复文章 id: {ids1 & ids2}"


@pytest.mark.api
@pytest.mark.mp
def test_news_list_case_design_coverage():
    """离线守卫：分页/状态/关键词三类场景都必须有数据覆盖。"""
    kinds = {c["case_id"].split("_")[2][0] for c in cases}
    assert {"P", "S", "K"} <= kinds, f"列表用例覆盖不全: {kinds}"
    assert len(cases) >= 15, f"列表用例只有 {len(cases)} 条"
    for c in cases:
        assert c["check"] in {"paging", "contract", "robust", "keyword_hit", "keyword_miss"}, (
            f"{c['case_id']} check 取值非法: {c['check']}"
        )
        assert isinstance(c.get("payload"), dict), f"{c['case_id']} 缺少 payload"
