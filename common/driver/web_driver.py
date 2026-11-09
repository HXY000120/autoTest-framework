"""Selenium 驱动管理：支持本地与 Grid 两种模式。

有三个「踩过坑才知道」的必要配置，缺一个都会跑不起来：

1. **no_proxy 环境变量**：若系统设置了 http_proxy，urllib 会把连 chromedriver 的
   localhost 请求也发往代理，代理无法处理该路径，返回 400「unhandled request」，
   表现为 `driver.get()` 一律失败（连 about:blank 都不行）。必须让 localhost 直连。
2. **--window-size**：headless 默认窗口过小，登录框位于视口外，
   send_keys 会报 ElementNotInteractable。
3. **--user-agent**：站点部署在 WAF 之后，headless 默认 UA 会被拦截返回 405。
"""
import os

# 必须在 import selenium 之前设置，否则 urllib 已按代理初始化
os.environ.setdefault("no_proxy", "localhost,127.0.0.1")
os.environ.setdefault("NO_PROXY", "localhost,127.0.0.1")

from selenium import webdriver  # noqa: E402
from selenium.webdriver.chrome.options import Options as ChromeOptions  # noqa: E402
from selenium.webdriver.edge.options import Options as EdgeOptions  # noqa: E402

# 伪装成正常浏览器，避免被 WAF 拦截（headless 默认 UA 会返回 405）
DEFAULT_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36"
)


def get_web_driver(
    browser: str = None,
    headless: bool = None,
    grid: bool = False,
    grid_url: str = "http://127.0.0.1:4444/wd/hub",
):
    """创建 WebDriver。

    browser / headless 可由环境变量控制，便于本地联调时观察浏览器：
        BROWSER=edge|chrome   默认 edge
        HEADLESS=0            本地有头运行（默认无头，CI 用）
    """
    browser = (browser or os.getenv("BROWSER", "edge")).lower()
    if headless is None:
        headless = os.getenv("HEADLESS", "1") != "0"

    options = EdgeOptions() if browser == "edge" else ChromeOptions()
    if headless:
        options.add_argument("--headless=new")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_argument(f"--user-agent={DEFAULT_UA}")
    if not grid:
        # 浏览器直连被测站点；若你的网络必须走代理，改用 WEB_DIRECT=0 关闭
        if os.getenv("WEB_DIRECT", "1") == "1":
            options.add_argument("--no-proxy-server")

    if grid:
        return webdriver.Remote(command_executor=grid_url, options=options)
    if browser == "edge":
        return webdriver.Edge(options=options)
    return webdriver.Chrome(options=options)


def quit_web_driver(driver):
    if driver:
        driver.quit()
