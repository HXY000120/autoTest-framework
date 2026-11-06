"""真机资源采集：在 Locust/UI 压测期间采集 App 的 CPU / 内存 / 流量 / 电量。

依赖：本地已连接 adb 设备（USB 或模拟器）。
用法：
    python perf/adb_monitor.py --pkg com.netease.newsreader.activity --duration 60
输出：
    采样结果以 CSV 写入 reports/perf/<timestamp>.csv，便于后续绘图对比。
"""
import argparse
import csv
import os
import subprocess
import time

from common.config.settings import BASE_DIR


def _adb(args: list) -> str:
    return subprocess.run(
        ["adb"] + args, capture_output=True, text=True, check=False
    ).stdout.strip()


def sample_cpu(pkg: str) -> float:
    """CPU 占用。

    注意：subprocess 不经 shell，写成 ["...", "|", "grep", pkg] 时管道符
    只会被当成普通参数，永远拿不到结果（旧实现的死代码）。这里改为在
    Python 侧过滤 dumpsys cpuinfo 输出，跨平台且不依赖 shell。
    """
    total = _adb(["shell", "dumpsys", "cpuinfo"])
    for line in total.splitlines():
        if pkg in line or "TOTAL" in line:
            try:
                return float(line.split("%")[0].strip().split()[-1])
            except (ValueError, IndexError):
                continue
    return 0.0


def sample_mem(pkg: str) -> int:
    out = _adb(["shell", "dumpsys", "meminfo", pkg])
    for line in out.splitlines():
        if "TOTAL" in line:
            try:
                return int(line.split()[1])
            except (ValueError, IndexError):
                return 0
    return 0


def sample_traffic(pkg: str) -> int:
    # 读取 /proc/net/xt_qtaguid/stats 中该 uid 的接收+发送字节
    out = _adb(["shell", "cat", "/proc/net/xt_qtaguid/stats"])
    total = 0
    for line in out.splitlines()[1:]:
        cols = line.split()
        if len(cols) >= 8 and pkg in line:
            try:
                total += int(cols[5]) + int(cols[7])
            except (ValueError, IndexError):
                continue
    return total


def sample_battery() -> int:
    out = _adb(["shell", "dumpsys", "battery"])
    for line in out.splitlines():
        if "level" in line:
            try:
                return int(line.split(":")[1].strip())
            except (ValueError, IndexError):
                return -1
    return -1


def monitor(pkg: str, duration: int, interval: int = 2):
    out_dir = os.path.join(BASE_DIR, "reports", "perf")
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, f"perf_{int(time.time())}.csv")
    rows = []
    start = time.time()
    print(f"开始采集 {pkg}，时长 {duration}s，间隔 {interval}s")
    while time.time() - start < duration:
        row = {
            "ts": round(time.time() - start, 1),
            "cpu_pct": sample_cpu(pkg),
            "mem_kb": sample_mem(pkg),
            "traffic_bytes": sample_traffic(pkg),
            "battery_level": sample_battery(),
        }
        rows.append(row)
        print(row)
        time.sleep(interval)

    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    print(f"采集完成，结果写入: {path}")
    return path


def main():
    parser = argparse.ArgumentParser(description="adb 真机资源采集")
    parser.add_argument(
        "--pkg", default="com.netease.newsreader.activity", help="被测 App 包名（默认网易新闻）"
    )
    parser.add_argument("--duration", type=int, default=60, help="采集总时长(秒)")
    parser.add_argument("--interval", type=int, default=2, help="采样间隔(秒)")
    args = parser.parse_args()
    monitor(args.pkg, args.duration, args.interval)


if __name__ == "__main__":
    main()
