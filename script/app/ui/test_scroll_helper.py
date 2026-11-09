"""App 频道滑动组件 - 离线单元测试（无需真机 / Appium）。

简历里「坐标点计算 + 循环滑动 + 指定区域查找」这三件事，用 FakeDriver
就能真实验证算法，不必依赖设备和 Appium 服务：
    - 坐标按屏幕比例算，不写死像素
    - 循环滑动直到找到目标或达到上限
    - 在父容器区域内查找子元素
"""
import pytest

# 缺 selenium 时整个模块跳过（而不是收集报错），保证 CI 只装基础依赖也能收集
pytest.importorskip(
    "selenium.common.exceptions",
    reason="滑动组件单测依赖 selenium 的 WebDriverWait",
)
from selenium.common.exceptions import NoSuchElementException  # noqa: E402
from selenium.webdriver.common.by import By  # noqa: E402

from page.app.components.scroll_helper import ScrollHelper  # noqa: E402

TARGET = (By.NAME, "目标频道")
REGION = (By.ID, "channel_container")


class FakeElement:
    def __init__(self, text="目标频道"):
        self._text = text

    def is_displayed(self):
        return True

    @property
    def text(self):
        return self._text

    def find_element(self, by, value):
        return FakeElement("区域内元素")


class FakeDriver:
    """记录 swipe 调用。

    visible_after_swipes: 元素在滑动 N 次后进入可视区域（None 表示永不出现）。
    按「滑动次数」而非「查找次数」判定，避免受 WebDriverWait 内部轮询次数影响。
    """

    def __init__(self, width=1080, height=1920, visible_after_swipes=None):
        self.size = {"width": width, "height": height}
        self.swipes = []
        self.visible_after_swipes = visible_after_swipes

    def get_window_size(self):
        return self.size

    def swipe(self, sx, sy, ex, ey, duration=800):
        self.swipes.append((sx, sy, ex, ey, duration))

    def find_element(self, by, value):
        if (
            self.visible_after_swipes is not None
            and len(self.swipes) >= self.visible_after_swipes
        ):
            return FakeElement()
        raise NoSuchElementException("元素尚未出现在可视区域")


def make_helper(driver):
    # timeout 极小：元素不存在时不必真等，单元测试要快
    return ScrollHelper(driver, timeout=0.1)


@pytest.mark.app
@pytest.mark.app_end
@pytest.mark.parametrize("width,height", [(1080, 1920), (720, 1280), (1440, 2560)])
def test_swipe_up_uses_screen_ratio(width, height):
    """上滑坐标必须按屏幕比例计算，且始终在屏幕范围内。"""
    d = FakeDriver(width, height)
    helper = make_helper(d)
    helper.swipe_up()
    sx, sy, ex, ey, _ = d.swipes[0]
    assert sx == width // 2
    assert 0 <= sy < height and 0 <= ey < height
    assert ey < sy, "上滑终点应在起点之上"
    assert sy - ey == int(height * 0.75), "滑动距离应等于屏高 * ratio"


@pytest.mark.app
@pytest.mark.app_end
@pytest.mark.parametrize("ratio", [0.5, 0.6, 0.75, 0.9])
def test_swipe_ratio_changes_distance(ratio):
    """ratio 越大滑动距离越长，方向保持不变。"""
    d = FakeDriver()
    helper = make_helper(d)
    helper.swipe_up(ratio)
    _, sy, _, ey, _ = d.swipes[0]
    assert sy - ey == int(1920 * ratio), (
        f"ratio={ratio} 时滑动距离应为 {int(1920 * ratio)}，实际 {sy - ey}"
    )
    assert sy > ey, f"ratio={ratio} 时发生了零位移（旧实现缺陷）"


@pytest.mark.app
@pytest.mark.app_end
def test_swipe_down_is_reverse_of_up():
    d = FakeDriver()
    helper = make_helper(d)
    helper.swipe_up()
    helper.swipe_down()
    up, down = d.swipes
    assert up[1] == down[3] and up[3] == down[1], "下滑应为上滑的反向路径"


@pytest.mark.app
@pytest.mark.app_end
@pytest.mark.parametrize("visible_after,expect_swipes", [(0, 0), (1, 1), (2, 2), (4, 4)])
def test_find_in_scroll_stops_when_found(visible_after, expect_swipes):
    """循环滑动：目标一出现立即停止，不得多滑一次。"""
    d = FakeDriver(visible_after_swipes=visible_after)
    helper = make_helper(d)
    found = helper.find_in_scroll(TARGET, max_swipes=6)
    assert found is not None, f"目标在滑动 {visible_after} 次后出现，却未找到"
    assert len(d.swipes) == expect_swipes, (
        f"期望滑动 {expect_swipes} 次，实际 {len(d.swipes)} 次"
    )


@pytest.mark.app
@pytest.mark.app_end
def test_find_in_scroll_gives_up_at_limit():
    """始终找不到时应按 max_swipes 上限收手，不能无限滑。"""
    d = FakeDriver(visible_after_swipes=None)
    helper = make_helper(d)
    assert helper.find_in_scroll(TARGET, max_swipes=3) is None
    assert len(d.swipes) == 3


@pytest.mark.app
@pytest.mark.app_end
def test_find_in_scroll_direction_down():
    """direction=down 时每次滑动应为下滑路径。"""
    d = FakeDriver(visible_after_swipes=2)
    helper = make_helper(d)
    helper.find_in_scroll(TARGET, max_swipes=5, direction="down")
    assert len(d.swipes) == 2
    for _, sy, _, ey, _ in d.swipes:
        assert ey > sy, "direction=down 却执行了上滑"


@pytest.mark.app
@pytest.mark.app_end
def test_find_in_region():
    """指定区域查找：在父容器内定位子元素，而不是全局查找。"""
    d = FakeDriver(visible_after_swipes=0)
    helper = make_helper(d)
    el = helper.find_in_region(REGION, TARGET)
    assert el is not None
    assert el.text == "区域内元素"
