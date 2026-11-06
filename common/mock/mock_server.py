"""本地虚拟接口服务（Mock Server）。

解决的真实问题：被测环境里部分接口不存在或维护中——
    - mp  news/submit      -> code=900001「系统维护中」，发布链路跑不通
    - mis 审核动作          -> 无待审核数据，只能验到列表，验不到状态流转
    - app 端               -> 根本没有自有接口服务（UI 改用示例新闻 App）

做法：起一个真实的本地 HTTP 服务，模拟这些接口。用例只把 ApiClient 的
base_url 指向它，**PO 层与用例代码零改动**，请求仍走完整的
URL 拼接 / headers / token 注入 / JSON 解析链路。

特性：
    - 标准库 ThreadingHTTPServer，零第三方依赖
    - 有状态：文章可从「待审核 -> 审核通过/驳回 -> 已发布」流转
    - token 鉴权：除登录外必须带合法 token，否则 HTTP 401
    - 记录每次请求的 path / payload / headers，供用例做契约断言
    - 端口自动分配（port=0），多用例并行不冲突
"""
import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse

MP_PREFIX = "/wemedia/MEDIA"
MIS_PREFIX = "/service_6001"

MOCK_USERS = {
    "mp": {"name": "demo", "password": "mock_pwd_123"},
    "mis": {"name": "demo", "password": "mock_admin_pwd_123"},
    "app": {"mobile": "13800138000", "code": "246810"},
}

# 文章状态码与真实环境保持一致
DRAFT, PENDING, REJECTED, APPROVED, PUBLISHED = 0, 1, 2, 4, 9


class MockState:
    """服务内存状态。主线程可直接读取，用于断言服务端确实发生了状态变化。"""

    def __init__(self):
        self.reset()

    def reset(self):
        self.tokens = {}          # end -> 最近签发的 token
        self.valid_tokens = set()
        self.token_ends = {}      # token -> 签发它的业务端（用于跨端越权校验）
        self.articles = []
        self.next_id = 9001
        self.requests = []        # 所有请求记录
        self.audit_log = []       # 审核动作记录

    def add_article(self, **fields):
        article = {
            "id": self.next_id,
            "title": "",
            "content": "",
            "status": PENDING,
            "channelId": 1,
            "labels": "",
            "enable": 1,
        }
        article.update(fields)
        self.articles.append(article)
        self.next_id += 1
        return article

    def find_article(self, article_id):
        for a in self.articles:
            if a["id"] == article_id:
                return a
        return None

    def snapshot(self):
        return {
            "articles": [dict(a) for a in self.articles],
            "requests": list(self.requests),
            "audit_log": list(self.audit_log),
            "token_count": len(self.valid_tokens),
        }


class _Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        pass  # 静默，避免污染 pytest 输出

    # ---------- 基础响应 ----------
    def _json(self, obj, http_status=200):
        body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(http_status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    @staticmethod
    def _ok(data=None, code=200):
        return {"host": "mock", "code": code, "errorMessage": None, "data": data}

    @staticmethod
    def _fail(code, message):
        return {"host": "mock", "code": code, "errorMessage": message, "data": None}

    def _read_payload(self):
        length = int(self.headers.get("Content-Length", 0))
        raw = self.rfile.read(length) if length else b""
        try:
            return json.loads(raw or b"{}")
        except ValueError:
            return {}

    def _record(self, path, payload):
        self.server.state.requests.append({
            "method": self.command,
            "path": path,
            "payload": payload,
            "headers": {k.lower(): v for k, v in self.headers.items()},
        })

    # ---------- 请求入口 ----------
    def do_GET(self):
        self._handle({})

    def do_POST(self):
        self._handle(self._read_payload())

    def _handle(self, payload):
        full_path = urlparse(self.path).path
        state = self.server.state
        self._record(full_path, payload)

        # 管理端点：不鉴权
        if full_path == "/__mock__/state":
            return self._json(self._ok(state.snapshot()))
        if full_path == "/__mock__/reset":
            state.reset()
            return self._json(self._ok({"reset": True}, code=0))

        # 按网关前缀还原业务路径，同时识别业务端
        if full_path.startswith(MP_PREFIX):
            end, path = "mp", full_path[len(MP_PREFIX):]
        elif full_path.startswith(MIS_PREFIX):
            end, path = "mis", full_path[len(MIS_PREFIX):]
        elif full_path.startswith("/app/"):
            end, path = "app", full_path
        else:
            return self._json(self._fail(1004, f"未知路径: {full_path}"), 404)

        # 登录类端点免鉴权
        login_paths = {
            "mp": "/wemedia/login/in",
            "mis": "/admin/login/in",
            "app": "/app/v1_0/authorizations",
        }
        if path != login_paths[end]:
            token = self.headers.get("token")
            if token not in state.valid_tokens:
                return self._json(self._fail(401, "未登录或 token 无效"), 401)
            if state.token_ends.get(token) != end:
                return self._json(self._fail(403, "跨端 token 不可混用"), 403)

        obj, status = self._dispatch(end, path, payload)
        self._json(obj, status)

    # ---------- 业务分派 ----------
    def _dispatch(self, end, path, payload):
        state = self.server.state

        # ===== 登录 =====
        if path in ("/wemedia/login/in", "/admin/login/in"):
            expected = MOCK_USERS[end]
            if (payload.get("name") == expected["name"]
                    and payload.get("password") == expected["password"]):
                token = f"mock-{end}-token-{len(state.valid_tokens) + 1}"
                state.tokens[end] = token
                state.valid_tokens.add(token)
                state.token_ends[token] = end
                data = {"token": token, "user": {"name": "demo", "nickname": "管理"}}
                return self._ok(data, code=0), 200
            return self._fail(2, "密码错误"), 200

        if path == "/app/v1_0/authorizations":
            expected = MOCK_USERS["app"]
            if (payload.get("mobile") == expected["mobile"]
                    and payload.get("code") == expected["code"]):
                token = f"mock-app-token-{len(state.valid_tokens) + 1}"
                state.tokens["app"] = token
                state.valid_tokens.add(token)
                state.token_ends[token] = "app"
                return self._ok({"token": token, "user": {"phone": "13800138000"}}, code=0), 200
            return self._fail(2, "验证码错误"), 200

        # ===== mp 发布 =====
        if path == "/wemedia/api/v1/news/submit":
            title = (payload.get("title") or "").strip()
            content = payload.get("content") or ""
            if len(title) < 4:
                return self._fail(1001, "文章标题不能小于4个字符"), 200
            if not content:
                return self._fail(1002, "文章内容不能为空"), 200
            article = state.add_article(
                title=title,
                content=content,
                status=PENDING,
                channelId=payload.get("channelId", 1),
                labels=payload.get("labels", ""),
            )
            return self._ok({"id": article["id"], "status": PENDING}, code=0), 200

        # ===== 文章列表（mp / mis 共用，后台视角同一份数据）=====
        if path == "/wemedia/api/v1/news/list":
            items = list(state.articles)
            keyword = payload.get("keyword")
            if keyword:
                items = [a for a in items if keyword in a["title"]]
            status = payload.get("status")
            if status is not None:
                items = [a for a in items if a["status"] == status]
            size = payload.get("size", 10)
            page = payload.get("page", 1)
            try:
                start = max(0, (int(page) - 1) * int(size))
                items = items[start:start + max(0, int(size))]
            except (ValueError, TypeError):
                return self._fail(1003, "分页参数非法"), 200
            return self._ok(items, code=200), 200

        # ===== 文章详情 =====
        if path.startswith("/wemedia/api/v1/news/one/"):
            try:
                article_id = int(path.rsplit("/", 1)[-1])
            except ValueError:
                return self._fail(1002, "数据不存在"), 200
            article = state.find_article(article_id)
            if not article:
                return self._fail(1002, "数据不存在"), 200
            return self._ok(dict(article), code=0), 200

        # ===== 上下架 =====
        if path == "/wemedia/api/v1/news/down_or_up":
            article = state.find_article(payload.get("id"))
            if not article:
                return self._fail(501, "当前文章未发布"), 200
            article["enable"] = payload.get("enable", 1)
            return self._ok({"id": article["id"], "enable": article["enable"]}, code=0), 200

        # ===== 文章审核（真实环境维护中/无数据的部分）=====
        if path in ("/wemedia/api/v1/news/auth_pass", "/wemedia/api/v1/news/auth_fail"):
            article = state.find_article(payload.get("id"))
            if not article:
                return self._fail(1002, "数据不存在"), 200
            action = "pass" if path.endswith("auth_pass") else "fail"
            from_status = article["status"]
            article["status"] = APPROVED if action == "pass" else REJECTED
            state.audit_log.append({
                "id": article["id"],
                "action": action,
                "msg": payload.get("msg", ""),
                "from_status": from_status,
                "to_status": article["status"],
            })
            return self._ok({"id": article["id"], "status": article["status"]}, code=0), 200

        # ===== mis 用户实名认证列表 =====
        if path == "/user/api/v1/auth/list":
            rows = [
                {"id": 7001, "userId": 2001, "status": 0, "name": "张三"},
                {"id": 7002, "userId": 2002, "status": 1, "name": "李四"},
            ]
            status = payload.get("status")
            if status is not None:
                rows = [r for r in rows if r["status"] == status]
            return self._ok(rows, code=200), 200

        if path in ("/user/api/v1/auth/authPass", "/user/api/v1/auth/authFail"):
            return self._ok({"id": payload.get("id")}, code=0), 200

        # ===== APP 用户端文章流 =====
        if path in ("/app/v1_0/articles", "/app/v1_0/article/load"):
            items = [dict(a) for a in state.articles if a["status"] in (APPROVED, PUBLISHED)]
            return self._ok(items, code=200), 200

        return self._fail(1004, f"未实现的虚拟接口: {path}"), 404


class MockServer:
    """对 ThreadingHTTPServer 的轻量封装。"""

    def __init__(self, httpd, thread, state):
        self.httpd = httpd
        self._thread = thread
        self.state = state
        self.url = f"http://127.0.0.1:{httpd.server_address[1]}"

    def client(self, end: str = "mp"):
        """按业务端构造 ApiClient，只换域名，保留原有 api_prefix / headers。

        trust_env=False 很关键：本机环境设了 http_proxy，若走代理，
        连 127.0.0.1 的请求会被代理拦下（与之前 Selenium 遇到的坑同源）。
        """
        from base.api_base import ApiClient

        c = ApiClient(end=end)
        c.base_url = self.url
        c.session.trust_env = False
        return c

    def reset(self):
        self.state.reset()

    def shutdown(self):
        self.httpd.shutdown()
        self.httpd.server_close()
        self._thread.join(timeout=3)


def start_server() -> MockServer:
    """启动虚拟接口服务，返回封装对象。用完必须调用 shutdown()。"""
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), _Handler)
    httpd.daemon_threads = True
    state = MockState()
    httpd.state = state
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    return MockServer(httpd, thread, state)
