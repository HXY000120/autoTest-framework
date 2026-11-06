"""失败截图工具：Web / App 通用。"""


import os
import re
import time

from common.config.settings import BASE_DIR

# 失败截图统一存放目录：reports/screenshots/
SCREENSHOT_DIR = os.path.join(BASE_DIR, "reports", "screenshots")


def _safe_name(name: str) -> str:
    """把含 :: / [] / 路径分隔符 的 nodeid 转成合法文件名。"""
    return re.sub(r"[^A-Za-z0-9_.\-]", "_", name)[:120]


def take_screenshot(driver, name: str = None) -> str:
    os.makedirs(SCREENSHOT_DIR, exist_ok=True)
    name = _safe_name(name) if name else f"shot_{int(time.time())}"
    path = os.path.join(SCREENSHOT_DIR, f"{name}.png")
    driver.save_screenshot(path)
    return path
