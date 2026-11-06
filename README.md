# 今日资讯平台测试项目 — 自动化测试框架（PO 模式）

新闻资讯平台，含自媒体端（发布）、后台审核端（审核）、APP 端（浏览）三端；
本人独立完成三端测试设计与脚本开发。

按 **业务端（mp（自媒体端） / mis（后台审核端） / app）× 技术栈（api / web / app）** 双维度组织的
单仓库 PO 框架。被测对象封装在 `page/`，用例只写在 `script/`，技术基座与
基础设施下沉到 `base/` 与 `common/`，测试数据外置到 `data/`（YAML）。

## 目录结构

```
autoTest/
├── base/        # ① 端级基类（技术栈）：api / web / app
├── page/        # ② 被测对象封装：PO + API Object + entry 门面 + components
│   ├── mp/      #    自媒体端（Web + 接口）
│   ├── mis/     #    后台审核端（Web + 接口）
│   └── app/     #    用户端（App + 接口）
├── data/        # ③ 测试数据（YAML），路径与 script 严格对齐
├── script/      # ④ 用例层：只调 entry 方法 + 断言
│   ├── mp/  mis/  app/
│   └── 每个端下分 api/ 与 ui/（各带独立 conftest）
├── common/      # ⑤ 基础设施：config / logger / report / utils / driver
│   └── mock/    #    本地虚拟接口服务（标准库 HTTP Server，零依赖）
├── perf/        # ⑥ 性能测试（Locust + adb 资源采集），复用 page/*/api_*.py
├── Jenkinsfile  # ⑦ CI/CD 流水线（接口 / Web / App 三阶段 + Allure）
├── conftest.py  # ⑧ sys.path + TEST_TARGET 隔离 + mock fixture + 联调降级
├── pytest.ini   # ⑨ markers / testpaths / pythonpath
└── requirements*.txt  # 按端拆分依赖
```

## 设计要点

- **PO 模式**：页面对象只封装「定位器 + 操作」，API Object 只封装「业务动作」，
  **断言一律在 `script/` 用例层**，保证 page 层零断言、可复用。
- **entry 门面**：每个端提供 `entry.py`（如 `MpEntry`），用例只 import 它，
  不直接依赖具体页面/接口类；对象内部延迟导入，避免缺依赖时影响其它端收集。
- **技术栈与业务端解耦**：`base/` 按技术栈拆（api/web/app），`page/` 按业务端拆
  （mp/mis/app）；两层独立，新增业务端只需在 `page/` 加目录。
- **双维度执行隔离**：
  - 技术维度：`pytest -m api` / `-m web` / `-m app`
  - 业务维度：`TEST_TARGET=mp|mis|app pytest`（收集阶段忽略其它端）
  - 组合示例：`TEST_TARGET=mp pytest -m api`（只跑 mp 端接口，默认即可执行）
- **数据驱动**：YAML 用例经 `common/utils/data_reader.load_data` 读取，
  配合 `@pytest.mark.parametrize`；数字型字段（手机号/验证码）**务必加引号**。
- **配置外置**：`common/config/environments.yaml`（多环境结构，不含任何真实地址）
  + `.env` / 环境变量（`TEST_ENV`、`MP_BASE_URL`、`MP_PASSWORD` 等）按环境注入，
  账号与域名不落仓库。
- **断言封装**：`common/assertion.py` 统一收口业务码、字段契约、分页边界、
  鲁棒性（WAF 拒绝也算预期）四类断言，失败信息格式一致。
- **异常捕获与日志**：`ApiClient` 统一捕获 `requests.RequestException`，
  转成 `ApiRequestError` 并落日志；GET 幂等请求自动重试 2 次，**写操作不重试**，
  杜绝重复提交（`common/utils/retry.py`）。

## 快速开始

```bash
# 1. 建虚拟环境并装依赖（按需要选装）
pip install -r requirements.txt          # 接口 / 基础
pip install -r requirements-web.txt      # + Web（Selenium）
pip install -r requirements-app.txt      # + App（Appium）
pip install -r requirements-perf.txt     # + 性能（Locust）

# 2. 跑用例（默认不联网，需外部环境的用例自动 skip）
pytest                          # 全部
pytest -m api                   # 接口层（含 34 条虚拟接口用例）
pytest -m mock                  # 只跑虚拟接口用例，完全不联网
pytest -m web                   # Web UI（需先注入 MP_BASE_URL / MIS_BASE_URL）
pytest -m app                   # App 端（含无需真机的滑动组件单测）
pytest -m app_end               # 只按业务端筛 app 用例
TEST_TARGET=mp pytest -m api     # 只跑 mp 端接口

# 3. 真实联调（须先注入被测系统地址与账号，见「被测环境配置」）
MP_BASE_URL=https://<your-host> MP_USERNAME=<账号> MP_PASSWORD=<密码> \
    RUN_REAL=1 pytest -m api

# 4. 报告
python -m common.report.report clean          # 跑测试前清旧结果
pytest -m api --alluredir=reports/raw
python -m common.report.report generate      # 需本机 allure CLI
```

> 三类情况会自动 skip，都不会让构建变红：未装 selenium / appium、
> 未配置被测系统地址、以及打开 `RUN_REAL` 却没注入地址。
> 虚拟接口用例与离线契约用例始终执行。

## 用例规模与覆盖

| 维度 | 数量 | 说明 |
| --- | --- | --- |
| 收集用例 | 179 | `pytest --collect-only` 展开参数化后的实际条目 |
| 默认离线 | 不联网即可跑 | 虚拟接口、App 组件单测、数据契约守卫真实执行；需外部系统的用例自动 skip |
| 真实接口 | mp / mis | 登录异常、列表分页与状态、详情/上下架、鉴权、审核参数 |
| 虚拟接口 | 34 条 | 发布判定表、审核状态流转、APP 登录与文章流、**跨端完整业务闭环** |
| Web UI | mp + mis | 登录正/反向、发布表单校验判定表、审核列表、搜索反向 |
| App | 15 条离线单测 | 坐标按屏比计算、循环滑动、指定区域查找，**无需真机** |
| 用例设计方法 | 4 类 | 等价类、边界值、判定表、安全性，YAML 的 `method` 字段标注 |

用例数据全部在 `data/`，与 `script/` 路径严格对齐；多条离线「契约守卫」用例
会在 YAML 被误删或字段写错时失败，防止用例悄悄缩水。

**刻意跳过、不硬凑通过的部分**：依赖具体被测系统的用例（发布链路、
搜索正向、APP 端真实接口）在默认离线模式下自动 skip，每条都写明原因；
这些链路已由虚拟接口用例完整覆盖，见下一节。

## 虚拟接口（Mock Server）

被测系统中缺失 / 维护中的接口、以及尚未部署的 APP 端服务，用
`common/mock/mock_server.py` 起一个本地 HTTP 服务补齐。它不是 `unittest.mock` 打桩，而是**真实 HTTP 往返**：URL 拼接、
headers、token 注入、JSON 解析全部照常走，用例只把 `ApiClient.base_url`
指向它，**PO 层与用例代码零改动**。

```bash
pytest -m mock          # 34 条虚拟接口用例，不联网、CI 可稳定执行
```

| 能力 | 说明 |
| --- | --- |
| 有状态 | 文章按 `待审核(1) -> 通过(4) / 驳回(2) -> 已发布(9)` 流转 |
| 鉴权 | 除登录外必须带合法 `token`；跨端 token 混用返回 403 |
| 请求记录 | `state.requests` 保存 path / payload / headers，可断言 PO 组装是否正确 |
| 状态快照 | `state.articles` / `audit_log` 可直接断言服务端确实发生了变化 |
| 零依赖 | 仅用标准库 `ThreadingHTTPServer`，端口自动分配 |

覆盖的链路：`mp 发布 -> mis 审核通过/驳回 -> 状态流转 -> APP 文章流可见性`，
以及发布参数判定表、分页去重、关键词过滤、详情/上下架、APP 登录与鉴权。
`mock_server` fixture 在根 `conftest.py`，每个用例独立端口与状态；
`trust_env=False` 用来绕开本机代理对 `127.0.0.1` 的劫持。

## 被测环境配置

框架**不绑定任何具体站点**：仓库与 `environments.yaml` 里不保存真实地址或账号。
默认 `pytest` 不联网——虚拟接口用例执行完整 HTTP 往返，依赖外部系统的用例
自动跳过，因此 clone 后**无需任何配置即可稳定回归**。

需要联调真实被测系统时，通过环境变量注入（也可写进 `.env`，已被 git 忽略）：

| 变量 | 用途 |
| --- | --- |
| `MP_BASE_URL` / `MIS_BASE_URL` / `APP_BASE_URL` | 各端域名 |
| `MP_API_PREFIX` / `MIS_API_PREFIX` | 网关前缀，默认值见 `environments.yaml` |
| `MP_USERNAME` / `MP_PASSWORD` / `MIS_USERNAME` / `MIS_PASSWORD` | 登录账号 |
| `RUN_REAL=1` | 打开真实联调用例（默认关闭） |

密码若按日轮换，可在 `credentials.*.password_pattern` 里配 `{date}` 占位，
运行时自动替换为当天日期（`YYYYMMDD`），不必手改配置。
未注入地址时，真实环境用例自动跳过，不影响离线回归。

### 接口清单（API Object 已封装）

| 端 | 接口 | 说明 |
| --- | --- | --- |
| mp | `POST /wemedia/login/in` | 登录，成功 `code=0`，token 在 `data.token` |
| mp | `POST /wemedia/api/v1/news/list` | 列表；过滤字段为 `keyword`（`title` 会被后端忽略） |
| mp | `GET /wemedia/api/v1/news/one/{id}` | 详情 |
| mp | `POST /wemedia/api/v1/news/submit` | 发布；维护中时返回 `code=900001`，用例显式跳过 |
| mp | `POST /wemedia/api/v1/news/down_or_up` | 上下架 |
| mis | `POST /admin/login/in` | 后台登录 |
| mis | `POST /user/api/v1/auth/list` | 实名认证列表 |
| mis | `POST /wemedia/api/v1/news/auth_pass` / `auth_fail` | 文章审核，id 不存在返回 `1002` |

### 接口层适配点（框架已内置规避）

1. **鉴权只认 `token` 请求头**——用 `Authorization: Bearer` 会返回 401。
2. **网关 WAF 拦截 `python-requests` 的 User-Agent**（返回 405），`ApiClient` 默认伪装浏览器 UA。
3. **成功业务码不统一**——登录类 `code=0`，查询类 `code=200`，
   统一用 `common/assertion.py::assert_biz_code` 断言。

其它约定：未登录访问一律 HTTP 401；错误密码 `code=2`；系统维护 `code=900001`。

## 跑 Web UI（Selenium）

```bash
pip install -r requirements-web.txt
MP_BASE_URL=https://<your-host> MIS_BASE_URL=https://<your-host> \
    RUN_REAL=1 pytest -m web      # 默认 headless，浏览器默认 edge（可改 chrome）
```

> Web 用例的定位器与被测页面结构绑定，换站点需同步调整 `page/*/web_*.py`。
> 未配置 `MP_BASE_URL` / `MIS_BASE_URL` 时该端用例**自动 skip**，不会因地址为空而报错。

UI 层另有三个坑，已在 `common/driver/web_driver.py` 内置规避，缺一个都跑不起来：

1. **no_proxy 必须绕过 localhost**——环境若设置了 `http_proxy`，selenium 连
   chromedriver 的本地请求会被代理拦截并返回 400「unhandled request」，
   表现为**所有 `driver.get()` 失败（连 about:blank 都不行）**，极易误判为版本不匹配。
2. **必须设 `--window-size`**——headless 默认窗口过小，登录框落在视口外，
   `send_keys` 会报 `ElementNotInteractable`。
3. **必须伪装 UA**——headless 默认 UA 会被 WAF 拦截返回 405。

页面定位器按常见 Element UI 结构编写，**接入实际被测系统时需按 DOM 复核**。
下表是调试中记录的几类易错写法：

| 元素 | 易错写法 | 推荐写法 |
| --- | --- | --- |
| 登录按钮 | `contains(text(),'登录')` | 文案含空格时用 `normalize-space` + 单字匹配 |
| 账号/密码框 | 依赖具体 placeholder 文案 | 优先按 `input[type='text']` / `input[type='password']` 定位 |
| 用户名 | 猜测 `.nickname` 之类的类名 | 以实际 DOM 为准，登录后取文本断言 |
| 搜索框 | 假设一定存在搜索按钮 | 无按钮时用 `Keys.ENTER` 触发查询 |

> 搜索正向用例依赖具体页面的检索规则，未与被测页面核对前保持 skip，
> 并在用例里注明原因，未强行改断言凑通过。

## 日志 / 报告 / 失败截图

| 产物 | 位置 | 说明 |
| --- | --- | --- |
| 运行日志 | `logs/run.log` | 控制台 + 文件双输出；接口请求/响应、元素查找/点击都会记录 |
| Allure 原始结果 | `reports/raw/` | 跑测试时加 `--alluredir=reports/raw` 才会产出 |
| Allure HTML 报告 | `reports/html/` | 需本机安装 allure 命令行后聚合生成 |
| 失败截图 | `reports/screenshots/` | 用例失败自动截图，文件名即用例 nodeid |

```bash
pytest -m api --alluredir=reports/raw            # ① 产出原始结果
allure generate reports/raw -o reports/html --clean  # ② 聚合为 HTML
allure open reports/html                         # ③ 浏览器打开
```

> 失败截图由根 `conftest.py` 的 `pytest_runtest_makereport` hook 自动触发（仅
> `call` 阶段失败时），并会 attach 到 Allure 报告中对应用例下，无需用例里手动调用。

## 性能测试

压测脚本把 Locust 的 `HttpSession` 注入 `ApiClient.session`，因此**既复用
`page/mp/api_mp.py` 的业务封装，又能被 Locust 统计 RPS / 响应时间 / 失败率**。
只压读接口（列表 3 : 搜索 2 : 详情 1），不压发布接口——压测写操作会污染数据。

```bash
# 10 并发、30 秒，无 UI；域名由 MP_BASE_URL 提供
MP_BASE_URL=https://<your-host> \
    locust -f perf/locustfile.py --headless -u 10 -r 2 -t 30s

# 真机资源采集（CPU / 内存 / 流量 / 电量 4 类，输出 CSV 到 reports/perf/）
python perf/adb_monitor.py --pkg com.example.news --duration 60
```

示例验证（1 并发 / 5 秒）：登录 419ms、文章列表 103ms，**2 请求 0 失败**。
配置 `MP_BASE_URL` 后可自行复现；未注入地址时请勿启动压测。

## CI/CD（Jenkins）

流水线定义在根目录 `Jenkinsfile`，Windows agent / 自建 Runner，
配合 Jenkins Allure 插件出报告。

| 阶段 | 内容 | 开关 |
| --- | --- | --- |
| 准备环境 | 建 venv、装依赖、清理上轮 Allure 结果 | — |
| 接口自动化 | `pytest -m api --alluredir=reports/raw` | `RUN_REAL` 控制是否联调真实环境 |
| Web 自动化 | 装 `requirements-web.txt` 后 `pytest -m web` | `RUN_WEB`（需在 Jenkins 凭据注入 `MP_BASE_URL` / `MIS_BASE_URL`，否则自动 skip） |
| App 自动化 | `pytest -m app`（含无需真机的滑动组件单测） | `RUN_APP` |

`common/report/report.py` 的 `clean` / `generate` 通过
`python -m common.report.report <action>` 接入流水线；`post.always`
里用 Allure 插件聚合报告并归档 `reports/` 与 `logs/`。

流水线默认**不设 RUN_REAL**：真实环境用例跳过，34 条虚拟接口用例照常执行，
因此构建不依赖任何外部服务可用性，随时可稳定回归。
