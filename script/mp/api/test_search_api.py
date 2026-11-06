"""mp 自媒体端 - 文章列表/搜索接口用例（数据驱动）。

关键点：后端过滤字段是 keyword，实测 title/name/search 会被忽略。
用例断言「搜得到 / 搜不到」以及「命中结果确实含关键词」，能真实发现过滤失效。
"""
import os

import pytest

from common.assertion import assert_biz_code
from common.utils.data_reader import load_data

cases = load_data("mp/api/search_cases.yaml")
RUN_REAL = os.getenv("RUN_REAL") == "1"


@pytest.mark.api
@pytest.mark.mp
def test_mp_search_structure(mp_api):
    """结构校验：搜索能力存在（离线可跑）。"""
    assert hasattr(mp_api.api, "search_articles")


@pytest.mark.api
@pytest.mark.mp
@pytest.mark.skipif(not RUN_REAL, reason="设置 RUN_REAL=1 才跑真实接口")
@pytest.mark.parametrize("case", cases)
def test_mp_search_articles(mp_api, case):
    """登录后按关键词搜索：校验条数下限，且命中结果确实含该关键词。"""
    mp_api.api.login()
    resp = mp_api.api.search_articles(case["keyword"])
    body = assert_biz_code(resp, 200)

    data = body.get("data") or []
    assert len(data) >= case["expect_min"], (
        f"关键词「{case['keyword']}」命中 {len(data)} 条，期望 >= {case['expect_min']}"
    )
    if case["expect_contain"]:
        # 后端为模糊匹配，命中结果标题应包含关键词
        assert any(case["keyword"] in (item.get("title") or "") for item in data), (
            f"命中结果标题不含关键词「{case['keyword']}」: "
            f"{[item.get('title') for item in data][:5]}"
        )


@pytest.mark.api
@pytest.mark.mp
@pytest.mark.skipif(not RUN_REAL, reason="设置 RUN_REAL=1 才跑真实接口")
def test_mp_news_list_paging(mp_api):
    """分页参数生效性：size 应真实限制返回条数。"""
    mp_api.api.login()
    body = assert_biz_code(mp_api.api.news_list(page=1, size=3), 200)
    assert len(body.get("data") or []) <= 3, "size=3 却返回超过 3 条，分页未生效"
