"""mp 文章详情 / 上下架 - 参数与异常用例。

写操作一律使用不存在的 id，避免污染真实教学环境数据。
"""
import os

import pytest

from common.assertion import assert_biz_code, assert_no_server_error, assert_response_json
from common.utils.data_reader import load_data

cases = load_data("mp/api/article_cases.yaml")
RUN_REAL = os.getenv("RUN_REAL") == "1"


@pytest.mark.api
@pytest.mark.mp
@pytest.mark.skipif(not RUN_REAL, reason="设置 RUN_REAL=1 才跑真实接口")
@pytest.mark.parametrize("case", cases, ids=[c["case_id"] for c in cases])
def test_mp_article_params(mp_api, case):
    """详情与上下架：接口必须活着，且不得对非法 id 返回有效业务数据。"""
    mp_api.api.login()
    api = mp_api.api
    kind = case["kind"]

    if kind.startswith("detail"):
        resp = api.news_one(case["article_id"])
    else:
        resp = api.down_or_up(case["article_id"], case["enable"])

    assert_no_server_error(resp)
    assert resp.status_code not in (404, 405), (
        f"接口路径失效 HTTP {resp.status_code}: {resp.text[:120]}"
    )
    body = assert_response_json(resp, require_code=False)

    if kind == "detail_exist":
        assert_biz_code(resp)
        assert body.get("data"), "查询已存在的文章却返回空数据"
    else:
        data = body.get("data")
        assert not (isinstance(data, (dict, list)) and data), (
            f"非法/不存在的 id 竟返回了业务数据: {resp.text[:200]}"
        )


@pytest.mark.api
@pytest.mark.mp
def test_article_case_contract():
    """离线守卫：写操作用例不得使用真实文章 id，防止误改教学环境数据。"""
    for c in cases:
        assert isinstance(c.get("article_id"), int), f"{c['case_id']} 缺少 article_id"
        if c["kind"] == "toggle_missing":
            assert c["article_id"] >= 99999999, (
                f"{c['case_id']} 写操作必须使用不存在的 id"
            )
            assert c["enable"] in (0, 1), f"{c['case_id']} enable 取值非法"
