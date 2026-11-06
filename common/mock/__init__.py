"""虚拟接口（Mock Server）基础设施：仅用 Python 标准库，零第三方依赖。"""

from common.mock.mock_server import MockServer, start_server

__all__ = ["MockServer", "start_server"]
