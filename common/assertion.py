"""通用断言工具：集中断言逻辑，用例与 PO 均可调用。

设计原则：断言不进 PO（页面对象只封装操作），统一收口到本模块，便于
统一失败信息格式与后续扩展（如自动截图、DB 二次校验）。
"""


def assert_status(resp, expected: int = 200):
    assert resp.status_code == expected, (
        f"状态码期望 {expected}, 实际 {resp.status_code}, body={resp.text[:200]}"
    )


def assert_biz_code(resp, expected=(0, 200)):
    """断言业务返回码。

    服务端 HTTP 状态码恒为 200，成败体现在响应体的 code 字段上：
        0 / 200  成功（登录类为 0，查询类为 200）
        1002     数据不存在    501   文章未发布
        900001   系统维护中（该教学环境部分接口被禁用）
    返回解析后的响应体，便于用例继续取数据。
    """
    codes = expected if isinstance(expected, (tuple, list)) else (expected,)
    assert resp.status_code == 200, (
        f"HTTP 期望 200, 实际 {resp.status_code}, body={resp.text[:200]}"
    )
    body = resp.json()
    code = body.get("code")
    assert code in codes, (
        f"业务码期望 {codes}, 实际 {code}, 提示={body.get('errorMessage')}, "
        f"body={resp.text[:200]}"
    )
    return body


def assert_json_path(resp, path: str, expected):
    data = resp.json()
    actual = _get_path(data, path)
    assert actual == expected, f"字段 {path} 期望 {expected}, 实际 {actual}"


def assert_contains(resp, text: str):
    assert text in resp.text, f"响应未包含: {text}"


def assert_no_server_error(resp):
    """鲁棒性断言：服务端不得 5xx。异常参数场景下这是最基础的红线。"""
    assert resp.status_code < 500, (
        f"服务端异常 HTTP {resp.status_code}, body={resp.text[:200]}"
    )
    return resp


def assert_response_json(resp, require_code: bool = True):
    """契约断言：响应必须是合法 JSON 对象，且不能是 5xx。

    :param require_code: 是否强制包含业务码 code。异常参数可能被网关/框架
        直接拦下，返回 Spring 标准错误结构（无 code），此时应设为 False。
    """
    assert_no_server_error(resp)
    try:
        body = resp.json()
    except ValueError:
        raise AssertionError(f"响应不是合法 JSON: {resp.text[:200]}")
    assert isinstance(body, dict), f"响应体应为对象，实际 {type(body)}"
    if require_code:
        assert "code" in body, f"响应缺少业务码 code 字段: {resp.text[:200]}"
    return body


def assert_rejected_or_json(resp, require_code: bool = True):
    """异常参数专用：网关/WAF 直接拒绝（401/403/405）或返回合法 JSON 均可。

    教学环境部署在阿里云 WAF 之后，含 SQL 注入 / XSS 特征的参数会被
    直接拦下并返回 405 HTML 拦截页。这属于安全测试的**预期结果**，
    不能当成用例失败；但服务端 5xx 仍然一律不允许。
    """
    assert_no_server_error(resp)
    if resp.status_code in (401, 403, 405):
        return None  # 网关/WAF 已拒绝
    return assert_response_json(resp, require_code)


def assert_login_failed(resp):
    """登录失败断言：不得下发 token，且不得 5xx。

    用「未下发 token」而不是写死错误码，既能抓出「非法参数竟然登录成功」
    这类越权缺陷，也不受各环境错误码不统一的影响；WAF 拦截视为拒绝成功。
    """
    body = assert_rejected_or_json(resp, require_code=False)
    if body is None:
        return {"code": resp.status_code, "errorMessage": "WAF/网关已拒绝"}
    data = body.get("data") or {}
    token = data.get("token") if isinstance(data, dict) else None
    assert not token, (
        f"异常参数登录竟下发了 token，存在越权风险: {resp.text[:200]}"
    )
    return body


def assert_list_data(resp, key="data"):
    """列表契约：业务成功且 data 是列表。返回列表供用例继续校验。"""
    body = assert_biz_code(resp)
    data = body.get(key)
    assert isinstance(data, list), (
        f"字段 {key} 应为列表，实际 {type(data)}, body={resp.text[:200]}"
    )
    return data


def assert_fields(resp, fields, key="data"):
    """字段契约：data 列表的首条记录必须包含指定字段集合。"""
    data = assert_list_data(resp, key)
    if data:
        assert isinstance(data[0], dict), f"列表元素应为对象，实际 {type(data[0])}"
        assert set(fields) <= set(data[0]), (
            f"响应缺少字段 {set(fields) - set(data[0])}, 实际字段={list(data[0])}"
        )
    return data


def assert_paging(resp, size, key="data"):
    """分页边界：返回的记录数不得超过请求的 size。"""
    data = assert_list_data(resp, key)
    assert len(data) <= size, (
        f"size={size} 却返回 {len(data)} 条，分页参数未生效"
    )
    return data


def _get_path(d: dict, path: str):
    cur = d
    for key in path.strip(".").split("."):
        cur = cur[key]
    return cur
