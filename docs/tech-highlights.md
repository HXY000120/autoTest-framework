# 技术难点与解决方案

这一节把调试过程中真实遇到的问题、定位过程和代码里的落点集中列出。
每条都能在仓库里点开对应文件核对，也是面试时最能体现「解决过问题」而非「照着敲」的部分。

## 1. 接口层

| 问题 | 现象 | 解决 | 代码位置 |
| --- | --- | --- | --- |
| 网关 WAF 拦截默认 UA | `python-requests/x.x` 直接返回 **405 + HTML 拦截页**，不是 JSON | `ApiClient` 默认伪装浏览器 User-Agent；断言层把 WAF 拒绝（401/403/405）计入**预期结果** | `base/api_base.py`、`common/assertion.py::assert_rejected_or_json` |
| 鉴权头不通用 | `Authorization: Bearer` 返回 401，只有 `token` 头生效 | 登录成功后自动 `set_token()` 注入后续请求，用例不手工取 token | `page/mp/api_mp.py::login`、`base/api_base.py::set_token` |
| 成功业务码不统一 | 登录类 `code=0`，查询类 `code=200` | `assert_biz_code` 同时接受 0/200，失败信息统一格式 | `common/assertion.py` |
| 搜索字段不是直觉值 | 传 `title` / `name` 被后端忽略，仍返回全量；实测只有 `keyword` 生效 | API Object 里写明坑位；另写「从列表首条标题动态取片段回查」用例，不依赖硬编码数据 | `page/mp/api_mp.py`、`script/mp/api/test_news_list_api.py` |
| 异常参数直接返回 HTML | 含 SQL 注入 / XSS 特征的请求被 WAF 拦在网关，响应不是 JSON | 断言分两类：网关拒绝直接通过；否则校验合法 JSON 且**不得下发 token** | `common/assertion.py::assert_login_failed` |
| 写操作重试会重复提交 | POST 重试可能造成重复发文 | `retry_on_fail` 只允许 GET 幂等请求重试，POST/PUT/DELETE 一律不重试 | `common/utils/retry.py`、`base/api_base.py::_send` |

## 2. 环境依赖

| 问题 | 现象 | 解决 | 代码位置 |
| --- | --- | --- | --- |
| 本机代理劫持 localhost | `http_proxy` 无 `no_proxy` 时，Selenium 连 chromedriver 的本地请求返回 400，连 `about:blank` 都打不开 | Web driver 显式设置 no_proxy；Mock Server 的 `ApiClient` 设 `session.trust_env = False` | `common/driver/web_driver.py`、`common/mock/mock_server.py::MockServer.client` |
| 发布接口维护中、APP 端无接口服务 | 真实链路跑不通，用例只能 skip | 起**本地有状态 HTTP 服务**：真实 URL / headers / JSON 往返，只把 `base_url` 指过去，PO 零改动 | `common/mock/mock_server.py` |
| 真实地址与账号不适合进仓库 | 密钥落版本库有风险，且换环境要改代码 | 配置结构外置，地址/账号由 `MP_BASE_URL`、`MP_PASSWORD` 等环境变量注入；未注入时真实用例自动跳过 | `common/config/settings.py`、`conftest.py::pytest_collection_modifyitems` |
| 收集阶段依赖 selenium | 只装基础依赖时，pytest 收集 UI 测试模块就报 ImportError | selenium 改为延迟导入 / `importorskip`，缺依赖时跳过而非报错 | `base/web_base.py::find`、`script/app/ui/test_scroll_helper.py` |

## 3. UI 与组件

| 问题 | 现象 | 解决 | 代码位置 |
| --- | --- | --- | --- |
| 滑动组件零位移 | 旧实现用 `(ratio, 1-ratio)` 当起止点，`ratio=0.5` 时两点重合，等于没滑 | 改为「屏高 × ratio」围绕屏幕中心对称展开，任意 ratio 都有非零位移且不出屏 | `page/app/components/scroll_helper.py::_swipe_span` |
| 组件逻辑无法离线验证 | 真机 / Appium 不可用时整条链路全 skip | 用 FakeDriver 写 15 条单元测试，真实验证坐标计算、循环滑动停止条件、指定区域查找 | `script/app/ui/test_scroll_helper.py` |
| App PO 覆盖不全 | 仅登录 + 列表，缺首页频道 / 详情 | 新增 `HomeScreen`（频道切换 / 文章流 / 刷新 / 搜索）与 `DetailScreen`（标题 / 正文 / 评论 / 点赞 / 返回），用例只调 entry 门面，真机缺失时自动 skip | `page/app/app_home_screen.py`、`page/app/app_detail_screen.py` |
| 页面元素变动 | 改版后定位器易失效 | PO 集中管理 + 显式等待 + 失败截图/日志；再用 AST 静态扫描守护定位器合法性 | `script/mp/ui/test_locator_health.py`、README「页面元素变动的应对」 |
| headless 窗口过小 | 登录框落在视口外，`send_keys` 报 `ElementNotInteractable` | 固定 `--window-size`；表格异步加载用 `wait_rows()` 兜底 | `common/driver/web_driver.py`、`page/mp/web_search_page.py` |

## 4. 有意做出的设计取舍

| 取舍 | 选择 | 理由 |
| --- | --- | --- |
| Mock 方式 | 本地真实 HTTP 服务，**不用** `unittest.mock` 打桩 | 要验证 URL 拼接、headers、token 注入、JSON 解析的完整链路，打桩测不到 |
| 定位器管理 | 集中放在 PO 类属性，**未**外置成 YAML | 适合页面频繁改版、多环境并存的团队；当前规模下外置只多一层间接性 |
| 压测目标 | 只压读接口，**不压**发布 | 避免重复提交与数据污染；压测写操作是高频事故源 |
| 用例跳过 | 写清原因的 skip，**不改**断言去迎合结果 | 环境维护中、真机缺失、地址未配置都如实标注，保证报告可信 |
| 虚拟用户数据 | 写操作一律用不存在的 id | 绝不污染任何真实数据 |

## 5. 可核对的数字

| 指标 | 值 |
| --- | --- |
| 收集用例 | 190 |
| 默认离线结果 | 73 passed / 117 skipped / **0 failed** |
| 不依赖外部服务的用例 | 34 条虚拟接口 + 15 条 App 组件单测 + 5 条定位器守护 |
| AST 守护覆盖 | 12 个 PO 文件 / 42 个定位器（含 App 端登录 / 首页 / 详情屏） |
| 业务状态流转 | `待审核(1) → 通过(4) / 驳回(2) → 已发布(9)` |

> 详细测试点拆解见 [test-points.md](test-points.md)，真实运行输出见 [evidence/](evidence/)。
