"""PO 定位器静态守护：页面元素变动后，让构建先告诉你哪里坏了。

设计要点：
    - 用 AST 直接解析 page/ 源码，**不 import selenium、不启动浏览器**，
      因此 CI 只装 requirements.txt 也能稳定执行。
    - 守护四类高频问题：非法 by、空 value、绝对 XPath、同文件重复定位器。
    - 页面改版时，定位器仍集中在各 PO 文件；本用例保证它们至少是合法、
      可维护的，避免"改到一半写错却没人发现"。

对应面试问题「页面元素变动怎么办」里的「主动守护」一环。
"""
import ast
import os
from collections import Counter

import pytest

from common.config.settings import BASE_DIR

PAGE_DIR = os.path.join(BASE_DIR, "page")

# selenium / appium 支持的定位方式
VALID_BY = {
    "ID", "XPATH", "NAME", "TAG_NAME", "CLASS_NAME", "CSS_SELECTOR",
    "LINK_TEXT", "PARTIAL_LINK_TEXT", "CSS", "ACCESSIBILITY_ID",
    "ANDROID_UIAUTOMATOR", "IOS_PREDICATE",
}


def _stringify(node):
    """把常量字符串或 f-string 还原成可检查的文本。

    App 端 PO 常用 `f"{PKG}:id/xxx"` 拼 resource-id，属于 JoinedStr；
    保留 `{PKG}` 占位即可做非空 / 重复 / 绝对 XPath 校验。
    """
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    if isinstance(node, ast.JoinedStr):
        parts = []
        for part in node.values:
            if isinstance(part, ast.Constant) and isinstance(part.value, str):
                parts.append(part.value)
            elif isinstance(part, ast.FormattedValue):
                inner = part.value
                parts.append("{" + inner.id + "}" if isinstance(inner, ast.Name) else "{expr}")
        return "".join(parts)
    return None


def _collect_locators():
    """扫描 page/ 下形如 `_xxx = (By.CSS_SELECTOR, "value")` 的类属性。"""
    found = []
    for dirpath, dirnames, filenames in os.walk(PAGE_DIR):
        dirnames[:] = [d for d in dirnames if d != "__pycache__"]
        for name in filenames:
            if not name.endswith(".py") or name == "__init__.py":
                continue
            path = os.path.join(dirpath, name)
            with open(path, "r", encoding="utf-8") as f:
                tree = ast.parse(f.read(), filename=path)
            for node in ast.walk(tree):
                if not isinstance(node, ast.Assign):
                    continue
                value = node.value
                if not isinstance(value, ast.Tuple) or len(value.elts) != 2:
                    continue
                by_node, val_node = value.elts
                if not isinstance(by_node, ast.Attribute):
                    continue
                locator_value = _stringify(val_node)
                if locator_value is None:
                    continue
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id.startswith("_"):
                        found.append({
                            "file": os.path.relpath(path, BASE_DIR).replace("\\", "/"),
                            "name": target.id,
                            "by": by_node.attr,
                            "value": locator_value,
                        })
    return found


@pytest.fixture(scope="module")
def locators():
    return _collect_locators()


@pytest.mark.web
@pytest.mark.mp
def test_locator_pool_not_empty(locators):
    """定位器被整批删掉/解析规则失效时立即失败，防止守护用例变成摆设。"""
    assert len(locators) >= 10, f"只解析到 {len(locators)} 个定位器，page/ 可能被清空"
    files = {x["file"] for x in locators}
    assert len(files) >= 4, f"只有 {len(files)} 个 PO 文件含定位器，覆盖面不足"


@pytest.mark.web
@pytest.mark.mp
def test_locator_by_is_valid(locators):
    for x in locators:
        assert x["by"] in VALID_BY, (
            f"{x['file']}::{x['name']} 使用了非法定位方式 By.{x['by']}"
        )


@pytest.mark.web
@pytest.mark.mp
def test_locator_value_not_empty(locators):
    for x in locators:
        assert x["value"].strip(), f"{x['file']}::{x['name']} 定位表达式为空"


@pytest.mark.web
@pytest.mark.mp
def test_no_absolute_xpath(locators):
    """绝对 XPath 会随页面结构微调整体失效，属于最脆弱的写法。"""
    bad = [
        x for x in locators
        if x["by"] in ("XPATH", "ANDROID_UIAUTOMATOR")
        and x["value"].lstrip().startswith("/html")
    ]
    assert not bad, f"存在绝对 XPath: {[(x['file'], x['name']) for x in bad]}"


@pytest.mark.web
@pytest.mark.mp
def test_no_duplicate_locator_in_same_file(locators):
    """同一 PO 文件里重复的 (by, value) 通常是复制粘贴残留，改版时容易漏改。"""
    for file, group in _group_by_file(locators).items():
        pairs = Counter((x["by"], x["value"]) for x in group)
        dup = [k for k, n in pairs.items() if n > 1]
        assert not dup, f"{file} 存在重复定位器: {dup}"


def _group_by_file(locators):
    grouped = {}
    for x in locators:
        grouped.setdefault(x["file"], []).append(x)
    return grouped
