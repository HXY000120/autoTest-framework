"""mp 自媒体端接口对象(API Object)。只封装业务动作，不含断言。

真实环境：heima-leadnews（黑马头条 Java 版）
    完整地址 = base_url + api_prefix = https://heima-wemedia-java.itheima.net/wemedia/MEDIA

接口可用性（2026-11 实测）：
    可用     login/in        POST  登录，成功码 code=0，token 在 data.token
    可用     news/list       POST  文章列表，成功码 code=200
    可用     news/one/{id}   GET   文章详情，成功码 code=0
    可用     news/down_or_up POST  上下架（业务码 501 表示文章未发布，接口本身正常）
    维护中   news/submit     POST  发布文章，环境返回 code=900001「系统维护中」
    维护中   material/list   POST  素材列表，环境返回 code=900001

注意：
    - 该环境鉴权只认 `token` 请求头，Authorization: Bearer 会返回 401
    - 成功业务码不统一：登录类为 0，查询类为 200，用例断言需兼容
"""

import json

from base.api_base import ApiClient
from common.config.settings import get_credentials


class ApiMp:
    def __init__(self, client: ApiClient = None):
        self.client = client or ApiClient(end="mp")
        self.url_login = "/wemedia/login/in"
        self.url_news_list = "/wemedia/api/v1/news/list"
        self.url_news_one = "/wemedia/api/v1/news/one"
        self.url_news_submit = "/wemedia/api/v1/news/submit"
        self.url_down_or_up = "/wemedia/api/v1/news/down_or_up"

    def login(self, name: str = None, password: str = None):
        """登录自媒体端。账号密码缺省时从配置读取（密码按当天日期动态生成）。

        登录成功后自动把 token 注入 client 的后续请求头。
        """
        if name is None or password is None:
            name, password = get_credentials("mp")
        resp = self.client.post(
            self.url_login, json={"name": name, "password": password}
        )
        # 自动续接登录态，避免每条用例手工取 token
        try:
            body = resp.json()
            if body.get("code") == 0:
                token = (body.get("data") or {}).get("token")
                if token:
                    self.client.set_token(token)
        except ValueError:
            pass
        return resp

    def post_raw(self, path: str, payload: dict):
        """原样发送业务 payload。

        专供异常参数 / 边界值用例：news_list() 会过滤空值，无法表达
        「size=0」「缺字段」「非法状态」这类必须原样送达的请求。
        """
        return self.client.post(path, json=payload)

    def news_list(self, page: int = 1, size: int = 10, status=None, keyword: str = None):
        """文章列表。status: None 全部 / 0 草稿 / 1 待审核 / 9 已发布

        注意：后端真正的过滤字段是 ``keyword``。
        实测 title / name / search 传了会被忽略（仍返回全量），勿用。
        """
        payload = {"page": page, "size": size}
        if status is not None:
            payload["status"] = status
        if keyword:
            payload["keyword"] = keyword
        return self.client.post(self.url_news_list, json=payload)

    def search_articles(self, keyword: str, page: int = 1, size: int = 10):
        """按关键词搜索文章（复用列表接口的 keyword 过滤，实测生效）。"""
        return self.news_list(page=page, size=size, keyword=keyword)

    def news_one(self, article_id):
        """文章详情"""
        return self.client.get(f"{self.url_news_one}/{article_id}")

    def publish_article(self, title, content, channel_id=1, labels="自动化", article_type=0):
        """发布/提交文章。

        注意：当前教学环境该接口维护中，返回 code=900001「当前系统正在维护」。
        方法保留以便环境恢复后直接可用；用例层应对该码做显式处理。
        """
        if not isinstance(content, str):
            content = json.dumps(content, ensure_ascii=False)
        payload = {
            "title": title,
            "content": content,
            "channelId": channel_id,
            "labels": labels,
            "type": article_type,
            "images": [],
        }
        return self.client.post(self.url_news_submit, json=payload)

    def down_or_up(self, article_id, enable: int = 1):
        """文章上下架。enable: 1 上架 / 0 下架"""
        return self.client.post(
            self.url_down_or_up, json={"id": article_id, "enable": enable}
        )
