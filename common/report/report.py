"""Allure 报告：运行前清理旧结果，运行后聚合 HTML。

用法：
    from common.report.report import clean_results, generate_report
    clean_results()                       # 运行 pytest 前
    generate_report()                     # 运行 pytest 后（需本机安装 allure 命令行）
"""
import os
import shutil
import subprocess

from common.config.settings import BASE_DIR

RESULT_DIR = os.path.join(BASE_DIR, "reports", "raw")
REPORT_DIR = os.path.join(BASE_DIR, "reports", "html")


def clean_results():
    """清理上一次的 allure 原始结果，避免历史数据污染。"""
    if os.path.exists(RESULT_DIR):
        shutil.rmtree(RESULT_DIR)
    os.makedirs(RESULT_DIR, exist_ok=True)


def generate_report():
    """聚合生成 allure HTML 报告（需要本机安装 allure 命令行）。"""
    cmd = f"allure generate {RESULT_DIR} -o {REPORT_DIR} --clean"
    print("执行:", cmd)
    subprocess.run(cmd, shell=True, check=False)


def open_report():
    if os.path.exists(os.path.join(REPORT_DIR, "index.html")):
        subprocess.run(f"allure open {REPORT_DIR}", shell=True, check=False)


def main(argv=None):
    """命令行入口，供 CI / Jenkins 调用，避免这三个函数成为死代码。

        python -m common.report.report clean      # pytest 前清理旧结果
        python -m common.report.report generate   # pytest 后聚合 HTML
        python -m common.report.report open       # 本地打开报告

    allure 命令行未安装时 generate 会明确报错，而不是静默产出空目录。
    """
    import argparse
    import shutil as _shutil

    parser = argparse.ArgumentParser(description="Allure 报告工具")
    parser.add_argument("action", choices=["clean", "generate", "open"])
    args = parser.parse_args(argv)

    if args.action == "clean":
        clean_results()
        print(f"已清理: {RESULT_DIR}")
    elif args.action == "generate":
        if not _shutil.which("allure"):
            raise SystemExit(
                "未找到 allure 命令行；请先安装 Allure CLI，"
                "或直接把 reports/raw 交给 Jenkins Allure 插件 / CI 报告 action"
            )
        generate_report()
    else:
        open_report()


if __name__ == "__main__":
    main()
