"""mp 自媒体端 - 接口发布文章用例（数据驱动）。

环境现状：news/submit 当前返回 code=900001「当前系统正在维护」，
即发布能力在该被测环境被禁用。用例对此显式处理——
维护中则 skip 并说明原因（不算「通过」），环境恢复后自动转为真实断言。
"""
import os

import pytest

from common.utils.data_reader import load_data

cases = load_data("mp/api/publish_cases.yaml")
RUN_REAL = os.getenv("RUN_REAL") == "1"

MAINTENANCE_CODE = 900001   # 环境维护中


@pytest.mark.api
@pytest.mark.mp
@pytest.mark.parametrize("case", cases)
def test_mp_publish_structure(mp_api, case):
    """结构校验：发布用例数据字段完整（离线可跑）。"""
    assert {"title", "content", "channel_id"} <= set(case)


@pytest.mark.api
@pytest.mark.mp
@pytest.mark.skipif(not RUN_REAL, reason="设置 RUN_REAL=1 才跑真实接口")
@pytest.mark.parametrize("case", cases)
def test_mp_publish_real(mp_api, case):
    """真实发布：维护中则跳过，可用时断言发布成功。"""
    mp_api.api.login()
    resp = mp_api.api.publish_article(
        case["title"], case["content"], case["channel_id"], case.get("labels", "自动化")
    )
    body = resp.json()
    code = body.get("code")

    if code == MAINTENANCE_CODE:
        pytest.skip(
            f"发布接口维护中（code={MAINTENANCE_CODE}：{body.get('errorMessage')}），"
            f"环境恢复后本用例会自动转为真实断言"
        )

    assert code in (0, 200), (
        f"发布失败: code={code}, 提示={body.get('errorMessage')}, body={resp.text[:200]}"
    )
