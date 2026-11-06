"""mis 后台审核端 - 审核接口用例（数据驱动）。

安全约定：审核是写操作，用例只用「不存在的 id」验证接口的存在性校验，
不改动真实待审核数据，避免污染被测环境。
"""
import os

import pytest

from common.assertion import assert_biz_code
from common.utils.data_reader import load_data

cases = load_data("mis/api/audit_cases.yaml")
RUN_REAL = os.getenv("RUN_REAL") == "1"


@pytest.mark.api
@pytest.mark.mis
@pytest.mark.skipif(not RUN_REAL, reason="设置 RUN_REAL=1 才跑真实接口")
@pytest.mark.parametrize("case", cases)
def test_mis_audit_article_not_exist(mis_api, case):
    """审核不存在的文章：接口应拒绝并返回 1002（数据不存在）。

    该断言能同时验证两件事：接口可达，且后端做了存在性校验。
    """
    mis_api.api.login()
    if case["action"] == "pass":
        resp = mis_api.api.audit_article_pass(case["article_id"])
    else:
        resp = mis_api.api.audit_article_fail(case["article_id"])

    body = resp.json()
    assert body.get("code") == case["expect_code"], (
        f"审核「{case['desc']}」期望 code={case['expect_code']}，"
        f"实际 {body.get('code')}，提示={body.get('errorMessage')}"
    )


@pytest.mark.api
@pytest.mark.mis
@pytest.mark.skipif(not RUN_REAL, reason="设置 RUN_REAL=1 才跑真实接口")
def test_mis_auth_list(mis_api):
    """实名认证审核列表：应返回列表结构且字段完整。"""
    mis_api.api.login()
    body = assert_biz_code(mis_api.api.auth_list(page=1, size=10), 200)
    data = body.get("data")
    assert isinstance(data, list), f"data 应为列表，实际 {type(data)}"
    if data:  # 有数据时校验关键字段，无数据则只验证结构
        assert {"id", "userId", "status"} <= set(data[0]), (
            f"列表字段缺失: {list(data[0])}"
        )


@pytest.mark.api
@pytest.mark.mis
@pytest.mark.skipif(not RUN_REAL, reason="设置 RUN_REAL=1 才跑真实接口")
def test_mis_news_list(mis_api):
    """后台视角文章列表：应返回分页结构。"""
    mis_api.api.login()
    body = assert_biz_code(mis_api.api.news_list(page=1, size=5), 200)
    assert isinstance(body.get("data"), list)
    assert "total" in body or "size" in body, "响应缺少分页字段"
