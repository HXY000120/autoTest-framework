"""mis Web UI 用例 fixture：组装 MisEntry + WebDriver。

未配置被测系统地址时自动跳过，且**在启动浏览器之前**判断，避免无谓开销。
"""
import pytest

from common.config.settings import get_endpoint
from page.mis.entry import MisEntry


@pytest.fixture
def mis_web(request):
    if not get_endpoint("mis")["base_url"]:
        pytest.skip("未配置 MIS_BASE_URL，跳过 Web UI 用例（见 README「被测环境配置」）")
    return MisEntry(driver=request.getfixturevalue("web_driver"))
