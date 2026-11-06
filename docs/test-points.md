# 今日资讯平台测试项目 — 测试点矩阵

按「业务模块 × 用例设计方法 × 自动化覆盖」拆解。用例路径均为本仓库相对路径，可直接点开核对。

覆盖状态：

- ✅ **已覆盖**：有可运行用例（虚拟接口或离线单测）
- ⚠️ **部分覆盖**：有代码，但依赖外部地址 / 真实环境，默认 skip
- 📋 **仅设计**：未实现为用例，属面试口述内容

> 边界说明：简历中「业务活动 4 个时间节点 / 5 种状态 / 多级赛程链路」
> 属于泽芯未来实习项目（无人机竞速模拟器），**不在本表范围内**。

## 1. 登录与鉴权

| 测试点 | 设计方法 | 覆盖 | 用例 |
| --- | --- | --- | --- |
| 正确账号 / 错误密码 / 用户不存在 | 等价类 | ✅ | `script/mp/api/test_login_param_api.py`、`script/mis/api/test_login_param_api.py` |
| 空用户名、空密码、双空组合、缺字段 | 判定表 / 边界值 | ✅ | 同上（YAML `method` 字段标注） |
| 超长、纯空格、SQL 注入 / XSS 样式 | 边界值 / 安全性 | ✅ | 同上；WAF 直接拦截也计入预期结果 |
| 未登录、空 token、伪造 token、误用 Bearer、跨端 token | 等价类 / 权限矩阵 | ✅ | `script/mp/api/test_auth_api.py`、`script/app/api/test_app_mock_api.py` |
| 登录跳转、用户名展示、错误码 `code=2` | 场景法 | ⚠️ | `script/mp/ui/test_login_ui.py`、`test_login_negative_ui.py`（需注入地址） |

## 2. 发布文章

| 测试点 | 设计方法 | 覆盖 | 用例 |
| --- | --- | --- | --- |
| 标题空 / <4 字符 / 4 字符边界 / 超长 / 特殊字符 | 边界值 | ✅ | `data/mp/api/publish_mock_cases.yaml` → `script/mp/api/test_publish_mock_api.py` |
| 内容空；标题×内容必填组合 | 判定表 | ✅ | 同上 |
| payload 字段齐全、token 注入、服务端确实新增一条 | 契约 / 状态 | ✅ | 同上（`state.articles` 断言） |
| 表单必填校验提示（5 类） | 判定表 | ⚠️ | `script/mp/ui/test_publish_ui.py`（需注入地址） |
| 发布 → 审核 → APP 可见的业务闭环 | 场景法 | ✅ | `script/mp/api/test_article_flow_mock_api.py` |
| 真实发布接口 `code=900001` 维护中 | 异常分支 | ⚠️ | `script/mp/api/test_publish_api.py` skip 并注明原因 |

## 3. 文章审核

| 测试点 | 设计方法 | 覆盖 | 用例 |
| --- | --- | --- | --- |
| 通过 / 驳回（原因透传）/ 重复审核 | 判定表 | ✅ | `script/mis/api/test_audit_mock_api.py` |
| 不存在 id / 缺 id / 字符串 id / id=0 | 边界值 / 等价类 | ✅ | `script/mis/api/test_audit_param_api.py` |
| 状态迁移 `待审核1 → 通过4 / 驳回2 → 已发布9`、审核日志 | 状态迁移 | ✅ | `common/mock/mock_server.py` + 上述用例断言 `state.audit_log` |
| mp 账号越权访问 mis 审核接口 | 权限矩阵 | ✅ | `script/mp/api/test_article_flow_mock_api.py`（跨端 token 返回 403） |
| 后台审核列表、行内按钮、进详情页点「通过」 | 场景法 | 📋 | 列表有 `script/mis/ui/test_audit_ui.py`（⚠️ 需地址）；详情页动作未实现 |

## 4. 列表 / 搜索 / 分页

| 测试点 | 设计方法 | 覆盖 | 用例 |
| --- | --- | --- | --- |
| `page=0/-1/超大`、`size=0/1/超大/负数` | 边界值 | ✅ | `data/mp/api/news_list_cases.yaml` → `script/mp/api/test_news_list_api.py` |
| `status=0/1/9/999`、缺分页字段 | 等价类 / 判定表 | ✅ | 同上、`data/mis/api/auth_list_cases.yaml` |
| `keyword` 命中 / 不命中 / 超长 / 特殊字符 | 等价类 / 安全性 | ✅ | 同上；另有动态关键词回查用例（不依赖硬编码数据） |
| 相邻页文章 id 不重复、返回条数 ≤ size | 契约 | ✅ | 同上 |
| 字段契约：`code`、`data` 为列表、含指定字段 | 契约 | ✅ | `common/assertion.py::assert_fields` |
| **抓包发现**：过滤字段是 `keyword`，`title` / `name` 会被后端忽略 | 探索性测试 | ✅ | `page/mp/api_mp.py` 注释 + 关键词回查用例 |

## 5. 详情与上下架

| 测试点 | 设计方法 | 覆盖 | 用例 |
| --- | --- | --- | --- |
| 存在的 id 返回正确文章 | 等价类 | ✅ | `script/mp/api/test_article_api.py`、`test_article_flow_mock_api.py` |
| 不存在 id / id=0 / 负数 | 边界值 | ✅ | `data/mp/api/article_cases.yaml` |
| 上架 / 下架改 `enable`、不存在 id 返回 `501` | 判定表 | ✅ | 同上 |
| 写操作一律使用不存在的 id，避免污染数据 | 安全性 | ✅ | `test_article_api.py::test_article_case_contract` 守卫 |

## 6. APP 内容浏览

| 测试点 | 设计方法 | 覆盖 | 用例 |
| --- | --- | --- | --- |
| 文章流只显示已通过 / 已发布，待审核不泄漏 | 状态 / 安全性 | ✅ | `script/app/api/test_app_mock_api.py` |
| APP 登录、验证码错误 / 空手机号、手机号字符串化 | 等价类 / 边界值 | ✅ | 同上 + `script/app/api/test_app_api.py` |
| 未登录拉取文章流返回 401 | 权限 | ✅ | 同上 |
| 频道不在可视区：坐标计算 / 循环滑动 / 指定区域查找 | 算法单测 | ✅ | `script/app/ui/test_scroll_helper.py`（15 条，无需真机） |
| 首页频道切换、文章流计数、下拉刷新 | 场景法 | ⚠️ | `script/app/ui/test_home_ui.py`（需 Appium + 真机，默认 skip） |
| 文章详情：标题 / 正文 / 评论 / 点赞 / 返回 | 场景法 | ⚠️ | `script/app/ui/test_detail_ui.py`（需 Appium + 真机，默认 skip） |
| 登录反向：空手机号 / 空密码仍停留在登录页 | 等价类 | ⚠️ | `script/app/ui/test_login_ui.py`（需 Appium + 真机，默认 skip） |
| 真机登录与查找文章 | 场景法 | ⚠️ | `script/app/ui/test_login_ui.py`、`test_article_ui.py`（需 Appium + 真机，默认 skip） |

## 7. 接口专项

| 类别 | 测试点 | 覆盖 |
| --- | --- | --- |
| 参数 | 必填、类型、长度、边界、非法值、空 body | ✅ |
| 业务码 | `0/200` 成功、`2` 密码错误、`1002` 数据不存在、`501` 未发布、`900001` 维护中；成功码不统一由 `assert_biz_code` 兼容 | ✅ |
| 鉴权 | HTTP `401/403`、`token` 头而非 Bearer、跨端拒绝、WAF 拦截计入预期 | ✅ |
| 契约 | 响应含 `code`、`data` 类型、字段集合、分页条数 | ✅ |
| 幂等 | GET 自动重试 2 次，POST/PUT/DELETE **绝不重试**（防重复发文） | ✅ |

## 8. 非功能

| 类型 | 测试点 | 覆盖 |
| --- | --- | --- |
| 性能 | Locust 只读接口压测（列表 3 : 搜索 2 : 详情 1）、RPS / 响应时间 / 失败率；adb 采集 CPU / 内存 / 流量 / 电量 4 类 | ✅ `perf/`（需注入 `MP_BASE_URL` 后复现） |
| 稳定性 | 显式等待防 stale、表格异步兜底、失败自动截图、日志记录定位器 | ✅ |
| 安全 | 注入 / XSS 样式参数、WAF 拦截、token 越权、写操作不污染数据 | ✅ |
| 维护 | PO 定位器静态守护（非法 by / 空值 / 绝对 XPath / 重复） | ✅ `script/mp/ui/test_locator_health.py` |
| 兼容 / 弱网 / 抓包 | 多分辨率、多浏览器、Charles 弱网、HTTPS 抓包 | 📋 实习中实践，仓库无产物 |

## 9. 用例设计方法落点

| 方法 | 用在哪些模块 | 数据文件 |
| --- | --- | --- |
| 等价类划分 | 登录、列表状态、关键词、APP 验证码 | `login_param_cases.yaml`、`news_list_cases.yaml` |
| 边界值分析 | 标题长度、分页 size/page、超长字段、id=0/负数 | `publish_mock_cases.yaml`、`article_cases.yaml` |
| 判定表 | 登录必填组合、发布必填组合、审核动作组合 | 同上，YAML 的 `method` 字段逐条标注 |
| 场景法 | 发布 → 审核 → APP 可见性业务闭环 | `test_article_flow_mock_api.py` |
| 探索性测试 | 抓包逆接口、WAF / 代理问题定位 | README「接口层适配点」 |

> 多条「契约守卫」用例会在 YAML 被误删、字段写错或方法覆盖不全时直接失败，
> 防止用例清单悄悄缩水。

## 10. 未覆盖 / 受限项（如实标注）

| 项 | 原因 |
| --- | --- |
| 真实 UI 审核动作（进详情页点「通过」） | 行内按钮初始 disabled，需先点「查看」，未实现 |
| 真实发布接口与真实 Web UI 执行 | 发布接口维护中；Web 用例需注入 `MP_BASE_URL` 才会跑，默认 skip |
| 真机 App 用例 | 无 Appium 服务与真机 / 模拟器 |
| 禅道缺陷记录、JMeter 脚本、弱网与兼容测试 | 属实习实践或口述内容，本仓库不含产物 |

**统计**：190 条收集用例；默认离线 73 passed / 117 skipped，0 失败；
34 条虚拟接口用例 + 15 条 App 组件单测 + 5 条定位器守护用例不依赖任何外部服务。
