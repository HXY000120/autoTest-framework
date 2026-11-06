# 运行证据

本目录是**真实 pytest 输出**，不是手写摘要。三个文件均在仓库根目录、默认离线模式下生成，
不含任何外部请求。

| 文件 | 复现命令 | 关键结果 |
| --- | --- | --- |
| `collect.txt` | `pytest --collect-only -q` | **184 tests collected** |
| `offline.txt` | `pytest -q` | **73 passed / 111 skipped / 0 failed** |
| `mock.txt` | `pytest -m mock -q` | **34 passed**（虚拟接口维度） |

## 本地复现

```bash
pip install -r requirements.txt
pytest -q
```

## 为什么有 skipped

默认不配置任何被测系统地址，因此以下三类用例自动跳过，且每条都写明原因：

1. 真实环境联调用例（需 `RUN_REAL=1` 并注入 `MP_BASE_URL` 等环境变量）
2. Web UI 用例（需注入 `MP_BASE_URL` / `MIS_BASE_URL`，会在启动浏览器**之前**判断）
3. App 真机用例（需 Appium 服务与真机 / 模拟器）

跳过不影响构建结果：**默认离线 0 失败**，虚拟接口用例、App 组件离线单测、
定位器静态守护用例均真实执行。这也是 CI 不依赖任何外部服务可用性的原因。
