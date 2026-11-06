"""mp 接口用例 fixture：按端构造 ApiClient，组装 MpEntry。

覆盖全局 api_client，确保拿到 mp 端自己的域名与网关前缀。
"""
import pytest

from base.api_base import ApiClient
from page.mp.entry import MpEntry


@pytest.fixture
def api_client():
    """覆盖全局同名 fixture：按 mp 端取 base_url + api_prefix。"""
    yield ApiClient(end="mp")


@pytest.fixture
def mp_api(api_client):
    """业务入口（注入了接口客户端），用例只跟它打交道。"""
    return MpEntry(client=api_client)
