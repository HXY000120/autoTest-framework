"""app 端内公共组件：频道滑动辅助。

解决移动端「滑动查找元素」的痛点：
    - 基于屏幕尺寸计算滑动坐标（不写死像素）
    - 支持循环滑动直到找到目标或达到最大次数
    - 支持在指定区域内查找元素
"""


from base.app_base import AppBase


class ScrollHelper(AppBase):
    def __init__(self, driver, timeout: int = 10):
        super().__init__(driver, timeout)
        size = driver.get_window_size()
        self.width = size["width"]
        self.height = size["height"]

    def _swipe_span(self, ratio: float):
        """按屏幕比例算滑动区间，围绕屏幕中心对称展开。

        旧实现用 (ratio, 1-ratio) 当起止点，ratio=0.5 时两点重合、
        位移为 0（等于没滑）；且 ratio>0.5 时坐标可能落在屏外。
        这里改为「distance = 屏高 * ratio」并向两侧均分，保证：
            - 任意 ratio 都有非零位移
            - 起止点始终在屏幕范围内
        """
        cx = self.width // 2
        center = self.height // 2
        distance = int(self.height * ratio)
        low = max(0, center - distance // 2)
        high = min(self.height - 1, center + distance // 2)
        return cx, low, high

    def swipe_up(self, ratio: float = 0.75):
        """从屏幕中部向上滑动（ratio 为滑动距离占屏高比例）。"""
        cx, low, high = self._swipe_span(ratio)
        self.swipe(cx, high, cx, low)

    def swipe_down(self, ratio: float = 0.75):
        cx, low, high = self._swipe_span(ratio)
        self.swipe(cx, low, cx, high)

    def find_in_scroll(self, loc, max_swipes: int = 5, direction: str = "up"):
        """循环滑动查找元素，找到即返回，否则返回 None。

        direction: "up" 上滑 / "down" 下滑
        """
        for _ in range(max_swipes):
            if self.exists(loc):
                return self.find(loc)
            if direction == "up":
                self.swipe_up()
            else:
                self.swipe_down()
        return None

    def find_in_region(self, region_loc, target_loc):
        """在 region 区域内查找 target（Appium 支持在父元素内查找）。"""
        region = self.find(region_loc)
        return region.find_element(*target_loc) if region else None
