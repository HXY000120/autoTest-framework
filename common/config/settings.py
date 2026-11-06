"""配置中心：多环境隔离，无模块级副作用（懒加载）。

环境选择优先级：
    1. 环境变量 TEST_ENV
    2. environments.yaml 中的 default
"""
import os
from datetime import datetime
from functools import lru_cache

import yaml

try:
    from dotenv import load_dotenv
    load_dotenv()   # 自动读取项目根目录 .env，使 TEST_ENV 真正生效
except ImportError:
    pass

# autoTest 根目录（common/config -> common -> autoTest）
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CONFIG_PATH = os.path.join(BASE_DIR, "common", "config", "environments.yaml")
ENV_NAME = os.getenv("TEST_ENV", "test")


@lru_cache(maxsize=1)
def load_config(env: str = None) -> dict:
    """加载指定环境配置（lru_cache 保证只解析一次）。"""
    env = env or ENV_NAME
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    envs = data.get("environments", {})
    if env not in envs:
        raise KeyError(f"未找到环境配置: {env}，可选: {list(envs)}")
    cfg = dict(envs[env])
    cfg["env"] = env
    cfg.setdefault("endpoints", {})
    cfg.setdefault("credentials", {})
    cfg.setdefault("headers", {"Content-Type": "application/json"})
    cfg.setdefault("appium_server", "http://127.0.0.1:4723/wd/hub")
    cfg.setdefault("app_caps", {})
    # 兼容字段：单端场景（如 locust）默认取 mp 端域名
    cfg.setdefault("base_url", cfg["endpoints"].get("mp", {}).get("base_url", ""))
    cfg.setdefault("api_prefix", cfg["endpoints"].get("mp", {}).get("api_prefix", ""))
    return cfg


def get_endpoint(end_name: str, env: str = None) -> dict:
    """按业务端取配置：{"base_url": ..., "api_prefix": ...}。

    end_name 取值：mp / mis / app
    """
    cfg = load_config(env)
    eps = cfg.get("endpoints", {})
    if end_name not in eps:
        raise KeyError(f"未找到端配置: {end_name}，可选: {list(eps)}")
    ep = dict(eps[end_name])
    ep.setdefault("base_url", "")
    ep.setdefault("api_prefix", "")
    return ep


def get_credentials(end_name: str, env: str = None):
    """取该端登录账号，密码按「当天日期」动态生成。

    该教学环境的密码每天变化：password_pattern 中的 {date} 会被替换为
    形如 20261101 的当天日期。返回 (username, password)。
    """
    cfg = load_config(env)
    creds = cfg.get("credentials", {}).get(end_name)
    if not creds:
        raise KeyError(
            f"未找到端 {end_name} 的账号配置，可选: {list(cfg.get('credentials', {}))}"
        )
    username = creds.get("username", "")
    pattern = creds.get("password_pattern", "")
    password = pattern.replace("{date}", datetime.now().strftime("%Y%m%d"))
    return username, password


def set_env(env: str):
    """运行时切换环境（会清空缓存）。"""
    global ENV_NAME
    ENV_NAME = env
    load_config.cache_clear()
