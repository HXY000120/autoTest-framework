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

    # 环境变量覆盖：真实地址不落仓库，需要联调时按需注入。
    # 未注入则 base_url 为空，默认全部走本地虚拟接口。
    eps = dict(cfg.get("endpoints", {}))
    for end_name in ("mp", "mis", "app"):
        ep = dict(eps.get(end_name, {}))
        prefix = end_name.upper()
        if os.getenv(f"{prefix}_BASE_URL"):
            ep["base_url"] = os.environ[f"{prefix}_BASE_URL"].rstrip("/")
        if os.getenv(f"{prefix}_API_PREFIX"):
            ep["api_prefix"] = os.environ[f"{prefix}_API_PREFIX"]
        eps[end_name] = ep
    cfg["endpoints"] = eps

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
    """取该端登录账号，返回 (username, password)。

    优先级：
        1. 环境变量 <END>_USERNAME / <END>_PASSWORD（推荐，账号不落仓库）
        2. environments.yaml 的 username / password_pattern
           password_pattern 支持 {date} 占位，运行时替换为当天日期（YYYYMMDD），
           适用于密码按日轮换的被测系统。
    """
    cfg = load_config(env)
    creds = cfg.get("credentials", {}).get(end_name)
    if not creds:
        raise KeyError(
            f"未找到端 {end_name} 的账号配置，可选: {list(cfg.get('credentials', {}))}"
        )
    prefix = end_name.upper()
    username = os.getenv(f"{prefix}_USERNAME") or creds.get("username", "")
    if os.getenv(f"{prefix}_PASSWORD") is not None:
        return username, os.environ[f"{prefix}_PASSWORD"]
    pattern = creds.get("password_pattern", "")
    return username, pattern.replace("{date}", datetime.now().strftime("%Y%m%d"))


def set_env(env: str):
    """运行时切换环境（会清空缓存）。"""
    global ENV_NAME
    ENV_NAME = env
    load_config.cache_clear()
