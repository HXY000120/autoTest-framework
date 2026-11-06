"""mis 接口用例 fixture：按端构造 ApiClient，组装 MisEntry。

覆盖全局 api_client，确保拿到 mis 端自己的域名与网关前缀（/service_6001）。
"""
import pytest

from base.api_base import ApiClient
from page.mis.entry import MisEntry


@pytest.fixture
def api_client():
    """覆盖全局同名 fixture：按 mis 端取 base_url + api_prefix。"""
    yield ApiClient(end="mis")


@pytest.fixture
def mis_api(api_client):
    """业务入口（注入了接口客户端），用例只跟它打交道。"""
    return MisEntry(client=api_client)
