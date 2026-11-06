"""app 接口用例 fixture：只提供门面，不主动构造会发请求的 ApiClient。

APP 端当前无自有接口服务（见 page/app/api_app.py 说明），用例分两类：
    - 契约/单测：注入 FakeClient，不联网
    - 真实联调：仅在配置了 endpoints.app.base_url 后启用
"""
import pytest

from page.app.entry import AppEntry


@pytest.fixture
def app_api():
    return AppEntry()
