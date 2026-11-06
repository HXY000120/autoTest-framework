"""Locust 性能测试入口：复用 page/mp/api_mp.py 的 API Object，不另起炉灶。

运行（无 UI 模式，10 并发跑 30 秒）：
    locust -f perf/locustfile.py --headless -u 10 -r 2 -t 30s \
        --host https://<your-host>

设计要点：
    - 把 Locust 的 HttpSession 注入 ApiClient.session，请求既走 API Object
      封装，又能被 Locust 自动统计（响应时间 / RPS / 失败率）。
    - 只压「读」接口：被测环境的 news/submit 处于维护中，且压测写操作
      会污染数据、触发重复提交，属于性能测试大忌。
    - 每个虚拟用户 on_start 登录一次并复用 token，避免把登录接口打爆。
"""

from locust import HttpUser, between, task

from base.api_base import ApiClient
from common.config.settings import get_credentials, get_endpoint
from page.mp.api_mp import ApiMp

EP = get_endpoint("mp")
HOST = EP["base_url"]


class MpUser(HttpUser):
    wait_time = between(1, 3)
    host = HOST

    def on_start(self):
        client = ApiClient(end="mp")
        client.session = self.client  # 关键：让压测请求被 Locust 统计
        self.api = ApiMp(client)
        name, password = get_credentials("mp")
        resp = self.api.login(name, password)
        token = ((resp.json().get("data") or {}).get("token"))
        if not token:
            raise RuntimeError(f"压测前置登录失败: {resp.text[:200]}")
        self.api.client.set_token(token)

    @task(3)
    def list_articles(self):
        self.api.news_list(page=1, size=10)

    @task(2)
    def search_articles(self):
        self.api.search_articles("华山", page=1, size=10)

    @task(1)
    def article_detail(self):
        self.api.news_one(6468)
