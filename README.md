# 免费 LLM API 状态清单

自动巡检各大平台免费大模型接口的可用性，每 8 小时更新一次。
密钥只存放在 GitHub Secrets 中，脚本不落地、不外传，仓库里只留下状态结果。

---

## ⚠️ 先读这段，能帮你省钱

**这些免费额度适合「轻量调用」，不适合「驱动 AI 编程工具」。**

2026-10-01 实测结论：把免费模型接到 **DSH / Cline / Roo Code** 这类 agent 工具上，
**8B 到 72B 全线失败**。它们能通过「能调用工具」的单次测试，但撑不住真实的 agent 场景
（几万 token 的系统提示词 + 反复多轮工具调用）。典型表现：输出格式跑偏、中途吐空、
被限速截断、或直接报工具错误。

| 用途 | 免费额度够吗 |
| --- | --- |
| 单独问问题、看段代码、翻译、写小片段 | ✅ **完全够用** |
| 让 agent 自主读写文件、跑命令、多步完成任务 | ❌ **请用付费 API** |

**别为了省这点钱，花一整天去试错。** 这份清单的价值是告诉你
「谁还有免费额度、额度多少、怎么申请、卡在哪」，**不是承诺它们能干重活**。

> 我们踩过的坑，你不用再踩一遍：清单上标着「免费」的模型，实测可能是
> 「账户余额不足」「只对特定用户开放」「不支持工具调用」——
> 这些只有真调用才知道，本仓库的巡检就是在做这件事。

---

- **最后更新**：2026-10-03 20:52:43 (北京时间 UTC+8)
- **本次耗时**：87.5 秒　|　**巡检频率**：`0 */8 * * *`
- **实测可用**：**24 / 96**（未配密钥但目录已确认存在 🔵 22 个）　|　**已配置平台**：5 / 24
- **接口探活**：23 个平台已探活（🟢 在线 21，❌ 失效 0，📡 不通 0）　|　**可读目录**：8 个平台（其中 3 个无需密钥）

> 这套清单是**自己维护自己**的：平台接口死活靠「匿名探活」（用一个无效密钥试，
> 401 说明服务活着），模型增删靠拉平台公开的 `/models` 目录，
> 能被机器确证免费的模型会自动纳入 `models.auto.json`，连续 3 轮实测失败会自动剔除。

| 状态 | 数量 | 说明 |
| --- | ---: | --- |
| ✅ 正常可用 | 24 | 用你的密钥实测返回 200 |
| 🔵 目录已确认 | 22 | 未配密钥，但平台公开目录中确认该模型存在 |
| ⚠️ 限流/额度耗尽 | 2 | 返回 429 或提示配额/余额不足 |
| 🟠 请求被拒 | 3 | 返回 400，参数或模型不被支持 |
| 🔑 密钥失效/无权限 | 2 | 返回 401/403，密钥无效或权限变更 |
| ⚪ 目录中已消失 | 1 | 公开目录里查不到它了，疑似已下架 |
| ❌ 模型已下架 | 0 | 返回 404，模型 ID 不存在 |
| 🌐 服务端异常 | 0 | 返回 5xx，平台侧故障 |
| 📡 网络超时/不可达 | 0 | 连接失败或超时 |
| ❔ 未知状态 | 0 | 其他返回码 |
| ⏭️ 无法判断 | 42 | 未配密钥，且平台目录不公开，无从判断 |

**平台级「接口探活」**（不需要任何密钥，用无效密钥试出来的）：

| 探活结果 | 平台数 | 说明 |
| --- | ---: | --- |
| 🟢 接口在线 | 21 | 鉴权层正常拒绝了无效密钥，说明服务活着、地址没变 |
| 🔓 无需密钥 | 1 | 无效密钥竟然返回 200，接口可能不校验密钥 |
| 🟠 接口异常 | 1 | 能连上，但返回 5xx / 410 等服务端错误 |
| ❌ 接口已失效 | 0 | 返回 404，路径变更或服务已下线 |
| 📡 域名不通 | 0 | 连接失败或超时 |
| ❔ 探活异常 | 0 | 返回码无法归类 |
| ⏭️ 未探活 | 1 | 缺少必要环境变量，或本次关闭了探活 |

## 本次状态变化

| 平台 | 模型 | 变化 |
| --- | --- | --- |
| OpenRouter | `thinkingmachines/inkling-small:free` | 🔵 目录已确认 → 🔑 密钥失效/无权限 |
| OpenRouter | `thinkingmachines/inkling:free` | 🔵 目录已确认 → 🔑 密钥失效/无权限 |
| OpenRouter | `apodex/apodex-1.1-mini:free` | 🔵 目录已确认 → ✅ 正常可用 |

## 平台总览

| 平台 | 接口探活 | 模型状态 | 免费性质 | 大陆可用性 | 密钥变量 | 目录 | 申请地址 |
| --- | --- | --- | --- | --- | --- | ---: | --- |
| 智谱 AI (BigModel) | 🟢 接口在线 | ✅ 正常可用 4/4 | 长期免费 | 🟢 容易 | `ZHIPU_KEY` | 11 | [控制台](https://open.bigmodel.cn/usercenter/apikeys) |
| 月之暗面 Kimi | 🟢 接口在线 | 🟠 请求被拒 0/3 | 一次性赠送 | 🟡 要点技巧 | `MOONSHOT_KEY` | 2 | [控制台](https://platform.kimi.com/console/api-keys) |
| 阿里云百炼 DashScope | 🟢 接口在线 | ⏭️ 无法判断 0/5 | 一次性赠送 | 🟢 容易 | `DASHSCOPE_KEY` | - | [控制台](https://bailian.console.aliyun.com/) |
| 硅基流动 SiliconFlow | 🟢 接口在线 | ✅ 正常可用 9/9 | 长期免费 | 🟢 容易 | `SILICONFLOW_KEY` | 97（公开） | [控制台](https://cloud.siliconflow.cn/account/ak) |
| 魔搭 ModelScope | 🟢 接口在线 | ✅ 正常可用 4/4 | 长期免费 | 🟡 要点技巧 | `MODELSCOPE_KEY` | 35 | [控制台](https://modelscope.cn/my/myaccesstoken) |
| 腾讯混元 / TokenHub | 🟢 接口在线 | ⏭️ 无法判断 0/2 | 一次性赠送 | 🟢 容易 | `HUNYUAN_KEY` | - | [控制台](https://console.cloud.tencent.com/hunyuan/api-key) |
| 百度千帆 Qianfan | 🟢 接口在线 | ⏭️ 无法判断 0/4 | 一次性赠送 | 🟢 容易 | `QIANFAN_KEY` | - | [控制台](https://console.bce.baidu.com/iam/) |
| 火山方舟 Volcengine Ark | 🟢 接口在线 | ⏭️ 无法判断 0/3 | 一次性赠送 | 🟢 容易 | `VOLC_ARK_KEY` | - | [控制台](https://console.volcengine.com/ark) |
| 讯飞星火 Spark | 🟢 接口在线 | ⏭️ 无法判断 0/1 | 长期免费 | 🟢 容易 | `SPARK_KEY` | - | [控制台](https://console.xfyun.cn/services/bmx1) |
| MiniMax | 🟢 接口在线 | ⏭️ 无法判断 0/3 | 一次性赠送 | 🟡 要点技巧 | `MINIMAX_KEY` | - | [控制台](https://platform.minimaxi.com/) |
| 阶跃星辰 StepFun | 🟢 接口在线 | ⏭️ 无法判断 0/1 | 长期免费 | 🟢 容易 | `STEPFUN_KEY` | - | [控制台](https://platform.stepfun.com/interface-key) |
| 零一万物 Yi | 🟠 接口异常 | ⏭️ 无法判断 0/2 | 未知 | ⛔ 不可用 | `YI_KEY` | - | [控制台](https://platform.lingyiwanwu.com/apikeys) |
| 百川智能 Baichuan | 🟢 接口在线 | ⏭️ 无法判断 0/2 | 一次性赠送 | 🟢 容易 | `BAICHUAN_KEY` | - | [控制台](https://platform.baichuan-ai.com/console/apikey) |
| OpenRouter | 🟢 接口在线 | ✅ 正常可用 7/19 | 长期免费 | 🟡 要点技巧 | `OPENROUTER_KEY` | 466 | [控制台](https://openrouter.ai/keys) |
| Groq | 🟢 接口在线 | ⏭️ 无法判断 0/3 | 长期免费 | 🟠 较难 | `GROQ_KEY` | - | [控制台](https://console.groq.com/keys) |
| Google Gemini | 🟢 接口在线 | ⏭️ 无法判断 0/4 | 长期免费 | ⛔ 不可用 | `GEMINI_KEY` | - | [控制台](https://aistudio.google.com/app/apikey) |
| Cerebras | 🟢 接口在线 | ⏭️ 无法判断 0/2 | 一次性赠送 | ⛔ 不可用 | `CEREBRAS_KEY` | - | [控制台](https://cloud.cerebras.ai/) |
| Mistral AI | 🟢 接口在线 | ⏭️ 无法判断 0/2 | 长期免费 | 🟠 较难 | `MISTRAL_KEY` | - | [控制台](https://console.mistral.ai/api-keys/) |
| Together AI | 🔓 无需密钥 | ⏭️ 无法判断 0/2 | 长期免费 | 🟠 较难 | `TOGETHER_KEY` | - | [控制台](https://api.together.xyz/settings/api-keys) |
| NVIDIA NIM | 🟢 接口在线 | 🔵 目录已确认 0/5 | 长期免费 | 🟠 较难 | `NVIDIA_KEY` | 80（公开） | [控制台](https://build.nvidia.com/settings/api-keys) |
| SambaNova (SambaCloud) | 🟢 接口在线 | 🔵 目录已确认 0/4 | 长期免费 | 🟢 容易 | `SAMBANOVA_KEY` | 6（公开） | [控制台](https://cloud.sambanova.ai/apis) |
| Nebius Token Factory | 🟢 接口在线 | ⏭️ 无法判断 0/2 | 一次性赠送 | 🟠 较难 | `NEBIUS_KEY` | - | [控制台](https://tokenfactory.nebius.com/) |
| Novita AI | 🟢 接口在线 | 🔵 目录已确认 0/6 | 长期免费 | 🟢 容易 | `NOVITA_KEY` | 121（公开） | [控制台](https://novita.ai/settings/key-management) |
| Cloudflare Workers AI | ⏭️ 未探活 | ⏭️ 无法判断 0/4 | 长期免费 | 🟡 要点技巧 | `CLOUDFLARE_API_TOKEN` | - | [控制台](https://dash.cloudflare.com/profile/api-tokens) |

## 免费政策与限流

这一节是**人工核实的官方数据**，不是实测值 —— 全部来自研究员实际读到的官方页面，
查不到的一律写「未公布」。核实日期见末列，来源链接在 `providers.json` 里。

| 平台 | 免费性质 | RPM | RPD | TPM | TPD | 并发 | 重置 | 闲时/忙时 | 手机号 | 实名 | 外币卡 | 置信度 | 核实日 |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- | --- | :-: | :-: | :-: | :-: | --- |
| 月之暗面 Kimi | 一次性赠送 | 3 | 未公布 | 500000 | 1500000 | 1 | 未公布 | 无 | ✅ | ✅ | — | partial | 2026-09-30 |
| 阿里云百炼 DashScope | 一次性赠送 | 1200（qwen-turbo、qwen-long，华北2北京）；30000（qwen-plus，华北2北京） | 未公布 | 5000000（qwen-plus、qwen-turbo，华北2北京）；3000000（qwen-long，华北2北京） | 未公布 | 未公布 | 未公布（免费额度有效期为 90 天、官方明确不支持补发/延期/重置；OAuth 免费额度为每天 2000 次，重置时刻未公布） | 官方未公布免费额度层面的闲时/忙时差异；但模型价格页显示部分模型改按峰谷定价：忙时为北京时间 8:00-22:00、闲时为北京时间 22:00-次日 8:00（如 deepseek-v4.1-flash、deepseek-v4-pro-0813、deepseek-v4-flash-0731），只影响单价、不影响免费额度是否存在 | ✅ | — | — | verified | 2026-09-30 |
| 腾讯混元 / TokenHub | 一次性赠送 | 未公布 | 未公布 | 未公布 | 未公布 | 未公布 | 未公布（非按日重置：免费额度为一次性资源包，自开通服务之日起 1 年内有效，过期作废） | 无 | ? | ✅ | ? | verified | 2026-09-30 |
| 百度千帆 Qianfan | 一次性赠送 | 未公布 | 未公布 | 未公布 | 未公布 | 未公布 | 未公布（免费额度非按日重置：自开通起 3 个月内有效；速率配额按分钟窗口，官方文档仅说明剩余配额「如果配额用完，将会在 0-60s 后刷新」） | 无（免费额度不区分闲忙时；但按量后付费价格区分忙时 8:00-22:00 与闲时 22:00-次日 8:00，闲时更便宜） | ? | ✅ | ? | partial | 2026-09-30 |
| 火山方舟 Volcengine Ark | 一次性赠送 | 未公布 | 未公布 | 未公布 | 未公布 | 未公布 | 不重置（一次性免费额度，用尽后服务暂停/需开通付费） | 无 | ? | ✅ | ? | partial | 2026-09-30 |
| MiniMax | 一次性赠送 | 20 | 未公布 | 1000000 | 未公布 | 未公布 | 未公布 | 无 | ✅ | ? | ? | partial | 2026-09-30 |
| 百川智能 Baichuan | 一次性赠送 | 120 | 300 | 未公布 | 未公布 | 未公布 | 未公布 | 无 | ✅ | ✅ | ? | verified | 2026-09-30 |
| Cerebras | 一次性赠送 | 5 | 未公布 | 30000（uncached TPM）/ 90000（total TPM） | 1000000 | 未公布 | 无固定重置时刻：官方 Quota Replenishment 说明额度用 token bucketing 算法连续补充（Available quota = min(Rate limit, Rate limit + replenished tokens by time − current usage)），不按固定间隔清零 | 无 | ? | ? | ✅ | verified | 2026-09-30 |
| Nebius Token Factory | 一次性赠送 | 60 | 未公布 | 400000 | 未公布 | 未公布 | 未公布（配额持续补充；动态限流按滚动 15 分钟窗口评估并调整） | 无 | ? | ? | ✅ | partial | 2026-09-30 |
| 零一万物 Yi | 未知 | 4 | 未公布 | 32000 | 未公布 | 未公布 | 未公布 | 无 | ✅ | ✅ | ? | partial | 2026-09-30 |
| 智谱 AI (BigModel) | 长期免费 | 未公布 | 未公布 | 未公布 | 未公布 | 数值未公布，需登录控制台查看。官方速率限制页明确「不同模型设有独立的并发限制」，且并发上限与「用户权益等级」相关，请到控制台「速率限制」页查看本账号各模型的可调用速率；并发定义为同一时刻正在处理中的请求数量。GLM Coding Plan 用户按套餐等级（Lite/Pro/Max）统一并发，低峰期动态提升。 | 未公布 | 有（但无数值）。官方说明：高峰期若账户短时间发起大量并发请求并超出该模型并发上限，平台按账户维度限流；此外平台级过载（某模型访问量激增、底层算力高负载、维护/扩容/异常恢复）会触发全局保护，与单一账户行为无关。错误码 1308 提示限额会在 next_flush_time 重置，但未公布具体时刻与时区。 | ✅ | — | ? | verified | 2026-09-30 |
| 硅基流动 SiliconFlow | 长期免费 | 未公布 | 未公布 | 未公布 | 未公布 | 未公布 | 未公布 | 无 | — | ✅ | ? | partial | 2026-09-30 |
| 魔搭 ModelScope | 长期免费 | 未公布 | 未公布 | 未公布 | 未公布 | 未公布 | 未公布 | 无 | ✅ | ✅ | ? | partial | 2026-09-30 |
| 讯飞星火 Spark | 长期免费 | 未公布 | 未公布 | 未公布 | 未公布 | 未公布 | 未公布 | 无 | ? | ✅ | ? | partial | 2026-09-30 |
| 阶跃星辰 StepFun | 长期免费 | 100 | 未公布 | 500000 | 未公布 | 5 | 未公布 | 无 | ✅ | ✅ | ? | verified | 2026-09-30 |
| OpenRouter | 长期免费 | 未公布 | 50 | 未公布 | 未公布 | 未公布 | 每日按 UTC 自然日重置（官方 docs 原文：free_model_daily_requests 统计 current UTC day；usage_weekly 为 current UTC week, starting Monday） | 无 | ? | ? | — | partial | 2026-09-30 |
| Groq | 长期免费 | 30 | 1000 | 8000 | 200000 | 未公布 | 未公布 | 无 | ? | ? | — | verified | 2026-09-30 |
| Google Gemini | 长期免费 | 未公布 | 未公布 | 未公布 | 未公布 | 未公布 | RPD（每日请求数）额度在太平洋时间午夜重置（原文：Requests per day (RPD) quotas reset at midnight Pacific time） | 无 | ? | ? | ? | partial | 2026-09-30 |
| Mistral AI | 长期免费 | 未公布 | 未公布 | 未公布 | 未公布 | 未公布 | 未公布 | 无 | ? | ? | — | partial | 2026-09-30 |
| Together AI | 长期免费 | 未公布 | 未公布 | 未公布 | 未公布 | 未公布 | 未公布 | 无 | ? | ? | ✅ | partial | 2026-09-30 |
| NVIDIA NIM | 长期免费 | 40 | 10000 | 未公布 | 未公布 | 未公布 | 未公布 | 无 | ? | ? | ? | partial | 2026-09-30 |
| SambaNova (SambaCloud) | 长期免费 | 20 | 20 | 未公布 | 200000 | 未公布 | 未公布 | 无 | ? | ? | — | verified | 2026-09-30 |
| Novita AI | 长期免费 | 30 | 未公布 | 50000000 | 未公布 | 未公布 | 未公布 | 无 | — | ? | ? | partial | 2026-09-30 |
| Cloudflare Workers AI | 长期免费 | 300 | 未公布 | 未公布 | 未公布 | 未公布 | 每日 00:00 UTC | 无 | ? | ? | — | verified | 2026-09-30 |

> 门槛列：✅ = 需要，— = 不需要，? = 官方页面未说明。
> 「未公布」不代表没有限制 —— 大部分平台的限速数字只在登录后的控制台可见。

## 中国大陆可用性

这一节回答的是「**身在墙内能不能拿到并调用它**」，数据来自官方条款与实测。
对我们来说，**地区封锁和非中国出口往往比外币卡更早成为障碍**。

| 平台 | 拿到密钥的难度 | 原因 | 封锁大陆 | 需非中国出口 | 拿免费额度要绑卡 |
| --- | --- | --- | :-: | :-: | :-: |
| 智谱 AI (BigModel) | 🟢 容易 | 中国大陆用户用手机号+短信验证码注册（官方称也支持海外号码并可选国家区号）即可创建 API Key，免费模型在官方定价… | — | — | — |
| 阿里云百炼 DashScope | 🟢 容易 | 只需一个能收短信的手机号注册阿里云账号、同意协议并开通百炼，即可拿到 API Key 使用免费额度，无需实名认证、无需… | — | — | — |
| 硅基流动 SiliconFlow | 🟢 容易 | 用 +86 手机号（或邮箱/微信）注册 + 支付宝扫码人脸实名认证即可创建 API Key 并使用免费模型，全程无需银… | — | — | — |
| 腾讯混元 / TokenHub | 🟢 容易 | 虽然硬性要求实名认证，但整套要求（+86 大陆手机号、大陆身份证、微信/QQ 扫码或人脸）对身在大陆的普通开发者都是现… | — | — | — |
| 百度千帆 Qianfan | 🟢 容易 | 中国大陆开发者只需要一个能收短信的手机号注册百度账号、完成个人实名认证（大陆身份证刷脸或银联卡二选一），阅读并同意用户… | — | — | — |
| 火山方舟 Volcengine Ark | 🟢 容易 | 中国大陆开发者用一个 +86 手机号短信注册火山引擎账号，创建 API Key，注册即得免费推理额度，个人实名认证可用… | — | — | — |
| 讯飞星火 Spark | 🟢 容易 | 中国大陆开发者用手机号快捷登录或微信扫码即可注册，充值走支付宝/微信/银行汇款（人民币、无需外币卡），门槛只在必须用身… | — | — | — |
| 阶跃星辰 StepFun | 🟢 容易 | 中国大陆用户用 +86 手机号即可注册，实名认证（证件号）后即可在控制台创建 API Key，充值走微信/支付宝、不需… | — | — | — |
| 百川智能 Baichuan | 🟢 容易 | 面向中国大陆开发者的境内平台：用 +86 手机号+短信验证码即可注册，需完成实名认证（个人为姓名+证件类型+证件号码，… | — | — | — |
| SambaNova (SambaCloud) | 🟢 容易 | 官方把免费额度定义为「账户没有关联任何支付方式」时的档位，并且 cloud.sambanova.ai/plans 的官… | ? | ? | — |
| Novita AI | 🟢 容易 | 邮箱或 Google/GitHub/HuggingFace 即可注册，不要手机号、不要实名、领免费额度也不要银行卡，且… | — | — | — |
| 月之暗面 Kimi | 🟡 要点技巧 | 中国大陆用户可用 +86 手机号注册、充值只用微信/支付宝、不需要外币卡或非中国 IP，但必须先完成实名认证（个人认证… | — | — | — |
| 魔搭 ModelScope | 🟡 要点技巧 | 对大陆开发者来说卡点和钱、卡都无关：手机号与身份证人皆有之，难在「不是注册即用」——注册完只能拿到 Access To… | — | — | — |
| MiniMax | 🟡 要点技巧 | 中国大陆用户可以直接注册（境内平台、人民币计价、微信充值，不需要外币卡），但按官方协议必须完成实名认证，且官方文档里找… | — | — | ? |
| OpenRouter | 🟡 要点技巧 | 官方对免费层不要手机号、不要实名、也不要绑卡（定价表 Free 计划 Payment options = No，免费模… | — | ? | — |
| Cloudflare Workers AI | 🟡 要点技巧 | 免费额度（每天 10,000 Neurons）不需要手机号、实名或银行卡，注册只要邮箱+密码；难点在于从大陆网络实测打… | ? | ? | — |
| Groq | 🟠 较难 | 中国大陆 IP 直连 console.groq.com（注册/取 key）与 api.groq.com 均返回 403… | ? | ? | ? |
| Mistral AI | 🟠 较难 | 拿 key 本身门槛很低（官方写明 Free mode 无需信用卡、注册只要邮箱，且条款未要求手机号/实名），真正卡住… | ? | ⛔ 是 | — |
| Together AI | 🟠 较难 | Together AI 现已没有免费额度：注册后必须绑定一张支持周期性扣款的 Visa/Mastercard/Amex… | ? | ? | ⛔ 是 |
| NVIDIA NIM | 🟠 较难 | 服务本身对中国大陆不封（build.nvidia.com 在国内可打开，中英文官方论坛都在运行），免费额度也不需要付费… | ? | ? | ? |
| Nebius Token Factory | 🟠 较难 | 官方注册只支持 Google/GitHub/Microsoft 账号或邮箱+onboarding 表单，不需要手机号也… | ? | ? | ⛔ 是 |
| 零一万物 Yi | ⛔ 不可用 | 官方 API 端点已直接返回 HTTP 410 model_service_closed『Model service … | — | — | ? |
| Google Gemini | ⛔ 不可用 | 官方口径是中国大陆不在 Google AI Studio / Gemini API 的支持地区内，且 aistudio… | ⛔ 是 | ⛔ 是 | ? |
| Cerebras | ⛔ 不可用 | 官方在 Cloudflare 上按国家/地区封禁 CN：中国大陆 IP 连控制台 cloud.cerebras.ai … | ⛔ 是 | ⛔ 是 | ⛔ 是 |

> ⛔ **官方按国家/地区封锁中国大陆**：零一万物 Yi、Google Gemini、Cerebras。这不是「难申请」，是根本进不去。

## 平台打分

**打分原则：只用能确证的维度。** 缺数据的维度不计入总分，权重会自动重新归一化，
并在末列标出缺了什么 —— 我们没有用「未知」去冒充中位数。

权重：免费性质 30 / 大陆门槛 25 / 限速 20 / 上下文 15 / 模型数 10（满分 10）

| # | 平台 | 综合分 | 评价 | 免费性质 | 大陆门槛 | 限速 | 上下文 | 模型数 | 缺数据 |
| ---: | --- | ---: | --- | ---: | ---: | ---: | ---: | ---: | --- |
| 1 | 硅基流动 SiliconFlow | **9.6** | 🟢 推荐 | 10.0 | 10.0 | — | 8.0 | 10.0 | 限速 |
| 2 | 智谱 AI (BigModel) | **9.2** | 🟢 推荐 | 10.0 | 10.0 | — | 7.0 | 8.0 | 限速 |
| 3 | 阶跃星辰 StepFun | **8.6** | 🟢 推荐 | 10.0 | 10.0 | 8.0 | — | 2.0 | 上下文 |
| 4 | 阿里云百炼 DashScope | **8.5** | 🟢 推荐 | 6.0 | 10.0 | — | 10.0 | 10.0 | 限速 |
| 5 | 魔搭 ModelScope | **8.5** | 🟢 推荐 | 10.0 | 7.0 | — | — | 8.0 | 限速、上下文 |
| 6 | Novita AI | **8.5** | 🟢 推荐 | 10.0 | 10.0 | 4.0 | 8.0 | 10.0 | - |
| 7 | Cloudflare Workers AI | **8.4** | 🟢 推荐 | 10.0 | 7.0 | 8.0 | — | 8.0 | 上下文 |
| 8 | SambaNova (SambaCloud) | **8.3** | 🟢 推荐 | 10.0 | 10.0 | 5.0 | 7.0 | 8.0 | - |
| 9 | NVIDIA NIM | **7.9** | 🟢 推荐 | 10.0 | 3.0 | 10.0 | — | 10.0 | 上下文 |
| 10 | 百度千帆 Qianfan | **7.7** | 🟢 推荐 | 6.0 | 10.0 | — | 7.0 | 8.0 | 限速 |
| 11 | 讯飞星火 Spark | **7.7** | 🟢 推荐 | 10.0 | 10.0 | — | 3.0 | 2.0 | 限速 |
| 12 | OpenRouter | **7.7** | 🟢 推荐 | 10.0 | 7.0 | 2.0 | 10.0 | 10.0 | - |
| 13 | 火山方舟 Volcengine Ark | **7.5** | 🟢 推荐 | 6.0 | 10.0 | — | — | 6.0 | 限速、上下文 |
| 14 | 腾讯混元 / TokenHub | **7.2** | 🟡 可用 | 6.0 | 10.0 | — | — | 4.0 | 限速、上下文 |
| 15 | 百川智能 Baichuan | **7.0** | 🟡 可用 | 6.0 | 10.0 | 8.0 | 5.0 | 4.0 | - |
| 16 | Groq | **7.0** | 🟡 可用 | 10.0 | 3.0 | 8.0 | 7.0 | 6.0 | - |
| 17 | 月之暗面 Kimi | **6.8** | 🟡 可用 | 6.0 | 7.0 | 8.0 | — | 6.0 | 上下文 |
| 18 | Mistral AI | **6.4** | 🟡 可用 | 10.0 | 3.0 | — | — | 4.0 | 限速、上下文 |
| 19 | Together AI | **6.4** | 🟡 可用 | 10.0 | 3.0 | — | — | 4.0 | 限速、上下文 |
| 20 | MiniMax | **5.8** | 🟡 可用 | 6.0 | 7.0 | 4.0 | — | 6.0 | 上下文 |
| 21 | Nebius Token Factory | **4.9** | 🟠 一般 | 6.0 | 3.0 | 6.0 | — | 4.0 | 上下文 |
| 22 | Google Gemini | **3.0** | ⛔ 不可用 | 10.0 | 0.0 | — | 10.0 | 8.0 | 限速 |
| 23 | Cerebras | **3.0** | ⛔ 不可用 | 6.0 | 0.0 | 8.0 | 7.0 | 4.0 | - |
| 24 | 零一万物 Yi | **2.1** | ⛔ 不可用 | 3.0 | 0.0 | 2.0 | 3.0 | 4.0 | - |

> **这个分数衡量的是「白嫖的性价比」，不是模型有多聪明。**
> 「限速」和「上下文」两列出现 `—` 是因为官方没有公布数值或没登记上下文，
> 不是它们不重要 —— 只是我们拒绝用猜的数字打分。

## 自动发现

这一节的内容**全部由脚本自动产生**，不需要人工维护：

- **自动纳入**：从平台公开目录里读到、且能被机器确证免费的模型 → 自动进 `models.auto.json`
- **候选**：名字看起来免费但无法确证的 → 只列在这里，等你确认后才进池子
- **目录中消失**：我们登记了、但平台目录里已经查不到 → 大概率被下架了

> 当前自动纳入模式：**safe**（`safe` = 只收机器确证免费的；`aggressive` = 名字像的也收；`off` = 只记候选）

### 候选（未自动纳入，共 43 个）

名字看起来是免费档、但平台没给出可机器核对的定价信息，所以只列在这里。
想收进来就把对应 `id` 加到 `models.custom.json`，或者手动跑 `--adopt aggressive`。

| 平台 | 模型 | 依据 | 上下文 |
| --- | --- | --- | ---: |
| NVIDIA NIM | `adept/fuyu-8b` | 疑似免费 |  |
| NVIDIA NIM | `aisingapore/sea-lion-7b-instruct` | 疑似免费 |  |
| NVIDIA NIM | `deepseek-ai/deepseek-coder-6.7b-instruct` | 疑似免费 |  |
| NVIDIA NIM | `google/codegemma-1.1-7b` | 疑似免费 |  |
| NVIDIA NIM | `google/codegemma-7b` | 疑似免费 |  |
| NVIDIA NIM | `google/diffusiongemma-26b-a4b-it` | 疑似免费 |  |
| NVIDIA NIM | `google/gemma-3-4b-it` | 疑似免费 |  |
| NVIDIA NIM | `ibm/granite-3.0-3b-a800m-instruct` | 疑似免费 |  |
| Novita AI | `Sao10K/L3-8B-Stheno-v3.2` | 疑似免费 | 8K |
| Novita AI | `baidu/ernie-4.5-21B-a3b` | 疑似免费 | 120K |
| Novita AI | `baidu/ernie-4.5-vl-424b-a47b` | 疑似免费 | 123K |
| Novita AI | `deepseek/deepseek-r1-0528-qwen3-8b` | 疑似免费 | 128K |
| Novita AI | `deepseek/deepseek-r1-turbo` | 疑似免费 | 64K |
| Novita AI | `deepseek/deepseek-v4-flash` | 疑似免费 | 1M |
| Novita AI | `deepseek/deepseek-v4-flash-0731` | 疑似免费 | 1M |
| Novita AI | `deepseek/deepseek-v4-flash-0731-p` | 疑似免费 | 1M |
| OpenRouter | `aion-labs/aion-rp-llama-3.1-8b` | 疑似免费 | 32K |
| OpenRouter | `amazon/nova-2-lite-v1` | 疑似免费 | 1M |
| OpenRouter | `amazon/nova-lite-v1` | 疑似免费 | 300K |
| OpenRouter | `baidu/ernie-4.5-vl-424b-a47b` | 疑似免费 | 123K |
| OpenRouter | `bytedance-seed/seed-1.6-flash` | 疑似免费 | 262K |
| OpenRouter | `bytedance-seed/seed-2-1-turbo` | 疑似免费 | 262K |
| OpenRouter | `bytedance-seed/seed-2.0-lite` | 疑似免费 | 262K |
| OpenRouter | `bytedance/ui-tars-1.5-7b` | 疑似免费 | 128K |
| 智谱 AI (BigModel) | `glm-5-turbo` | 疑似免费 |  |
| 智谱 AI (BigModel) | `glm-5.3-flash` | 疑似免费 |  |
| 智谱 AI (BigModel) | `glm-5.3-flashx` | 疑似免费 |  |
| 硅基流动 SiliconFlow | `Kev-4B` | 疑似免费 |  |
| 硅基流动 SiliconFlow | `LoRA/Qwen/Qwen2.5-14B-Instruct` | 疑似免费 |  |
| 硅基流动 SiliconFlow | `LoRA/Qwen/Qwen2.5-7B-Instruct` | 疑似免费 |  |
| … | 其余 13 个已截断 | | |

## 外部清单与官方文档变更

政策数字很难自动解析，但**「页面变了」很容易检测**。这一节只做变更提醒，不做解读。

### 别家清单的变化

| 来源 | 模型数 | 本轮变化 |
| --- | ---: | --- |
| Cline 模型目录 | 466 | 无变化 |
| HuggingFace Router 目录 | 135 | ➕ 2 个、➖ 2 个：`nvidia/NVIDIA-Nemotron-3.5-Lightning-30B-A3B-BF16`、`zai-org/GLM-4.6-FP8`；🟢 0 元组合 2 个 |
| 社区免费清单 (jtig37) | 21 | 无变化 |

**HuggingFace Router 目录当前的 0 元（live）组合**（✅=该供应商标注支持工具调用）：

- ✅ `prism-ml/Ternary-Bonsai-27B-AWQ-4bit@together`
- ✅ `prism-ml/Ternary-Bonsai-27B-gguf@together`

> Cline 模型目录：Cline 用量计费通道的目录；实测与 OpenRouter 一致（464 个），用来交叉验证
> HuggingFace Router 目录：HF 聚合 15+ 家供应商的实时路由目录，匿名即可读，每个「模型×供应商」组合自带定价、supports_tools、上下文。is_free 或定价 0/0 的 live 组合记为「0 元组合」，是发现「谁家又上新免费模型」最灵敏的传感器；调用本身走 HF 免费账号每月 $0.10 额度
> 社区免费清单 (jtig37)：社区人肉整理的免费 API 汇总（jtig37/free-llm-api-resources），新平台往往先在这里被人发现。解析 HTML 表格中的平台名，监控增删变化

### 官方文档页变更提醒

本轮 16 个官方页面都没有变化。

> 有 11 个页面是第一次抓取，本轮只建立基线，不算变更。
> 有 2 个页面本轮抓取失败（SambaNova 限流, 阶跃星辰定价），不影响其他检测。

共监控 16 个页面，摘要存放在 `sources.json`。

## 可用性时间线（自动累积）

已累积 **25** 次巡检（2026-09-30 19:57 起）。这一节是为了回答文档回答不了的问题：**哪个平台在哪个时段容易被限流**。

| 平台 | 巡检轮次 | 实测成功累计 | 限流(429)累计 | 探活异常 | 最容易限流的时段 |
| --- | ---: | ---: | ---: | ---: | --- |
| 硅基流动 SiliconFlow | 22 | 60 | 25 | 0 | 20:00 前后 |
| OpenRouter | 22 | 63 | 18 | 0 | 20:00 前后 |
| 月之暗面 Kimi | 23 | 0 | 6 | 0 | 13:00 前后 |
| 魔搭 ModelScope | 24 | 49 | 0 | 0 | - |
| 智谱 AI (BigModel) | 22 | 18 | 0 | 0 | - |
| CHUTES_KEY | 2 | 0 | 0 | 0 | - |
| Cerebras | 22 | 0 | 0 | 0 | - |
| Cloudflare Workers AI | 22 | 0 | 0 | 0 | - |
| DEEPSEEK_KEY | 2 | 0 | 0 | 0 | - |
| GITHUB_MODELS_TOKEN | 2 | 0 | 0 | 2 | - |
| Google Gemini | 22 | 0 | 0 | 0 | - |
| Groq | 22 | 0 | 0 | 0 | - |
| HYPERBOLIC_KEY | 2 | 0 | 0 | 2 | - |
| MiniMax | 22 | 0 | 0 | 0 | - |
| Mistral AI | 22 | 0 | 0 | 0 | - |
| NVIDIA NIM | 22 | 0 | 0 | 2 | - |
| Nebius Token Factory | 22 | 0 | 0 | 0 | - |
| Novita AI | 22 | 0 | 0 | 0 | - |
| SambaNova (SambaCloud) | 22 | 0 | 0 | 0 | - |
| Together AI | 22 | 0 | 0 | 0 | - |

> **没配密钥的平台，限流列会一直是 0** —— 429 只有真正调用时才会出现，
> 匿名探活看不到它。想让这一节有数据，配一个密钥就行。
> 时段按北京时间（UTC+8）统计，每 8 小时一个采样点，数据越攒越准。

## 模型明细

### 🔧 单次工具调用测试通过的免费模型（15 个）

**注意：通过这项测试 ≠ 能驱动 agent。** 它只证明模型「会在被问天气时吐出 `tool_calls`」——这是一道最低门槛的能力筛查。2026-10-01/02 两轮真实场景实测（DSH / Cline / Roo Code，几万 token 系统提示词 + 多轮工具循环）：下表中所有免费模型**全部跑不动**，典型表现是输出格式跑偏、中途吐空、被限速截断。

所以这个表的正确用法是：**快速排除**（连这关都过不了的 〽️/— 模型肯定没戏），而不是「这些能用来干活」。想正经用 agent，请用付费 API：

| 平台 | 模型 ID | 上下文 |
| --- | --- | ---: |
| 智谱 AI (BigModel) | `glm-4.7-flash` | 200K |
| 智谱 AI (BigModel) | `glm-4-flash-250414` | 128K |
| 硅基流动 SiliconFlow | `Qwen/Qwen3-8B` |  |
| 硅基流动 SiliconFlow | `Qwen/Qwen3.5-4B` |  |
| 硅基流动 SiliconFlow | `Qwen/Qwen2.5-72B-Instruct` | 32K |
| 硅基流动 SiliconFlow | `Qwen/Qwen2.5-7B-Instruct` | 32K |
| 硅基流动 SiliconFlow | `THUDM/GLM-4-9B-0414` | 32K |
| 魔搭 ModelScope | `deepseek-ai/DeepSeek-V4.1-Flash` |  |
| 魔搭 ModelScope | `ZhipuAI/GLM-4.7-Flash` |  |
| 魔搭 ModelScope | `stepfun-ai/Step-3.7-Flash` |  |
| OpenRouter | `nvidia/nemotron-3-super-120b-a12b:free` | 262K |
| OpenRouter | `nvidia/nemotron-3.5-lightning:free` | 1M |
| OpenRouter | `poolside/laguna-s-2.1:free` | 262K |
| OpenRouter | `stealth/space-bunny-alpha` | 1M |
| OpenRouter | `apodex/apodex-1.1-mini:free` | 262K |

> 判定方法：带 `tools` + `tool_choice=required` 发真实请求，返回里必须带原生 `tool_calls`。`〽️ 收参不吐调用` 和 `— 不支持工具` 的模型连单次调用都过不了；
> 🔧 的模型过了单次调用，但 2026-10-02 实测在 Cline / Roo / DSH 真实任务里依然全部失败。

| 平台 | 模型 ID | 来源 | 上下文 | 状态 | 工具调用 | HTTP | 延迟 | 备注 |
| --- | --- | --- | ---: | --- | --- | ---: | ---: | --- |
| 智谱 AI (BigModel) | `glm-4.7-flash` | 人工登记 | 200K | ✅ 正常可用 | 🔧 原生工具调用 | 200 | 630 ms |  |
| 智谱 AI (BigModel) | `glm-4-flash-250414` | 人工登记 | 128K | ✅ 正常可用 | 🔧 原生工具调用 | 200 | 403 ms |  |
| 智谱 AI (BigModel) | `glm-z1-flash` | 人工登记 | 128K | ✅ 正常可用 | 〽️ 收参不吐调用 | 200 | 378 ms |  |
| 智谱 AI (BigModel) | `glm-4v-flash` | 人工登记 | 16K | ✅ 正常可用 | 未测 | 200 | 328 ms | （轮换中，沿用上轮结果） |
| 月之暗面 Kimi | `kimi-k3` | 人工登记 |  | 🟠 请求被拒 | 未测 | 400 | 861 ms | invalid temperature: only 1 is allowed for this model |
| 月之暗面 Kimi | `kimi-k2.5` | 人工登记 |  | 🟠 请求被拒 | 未测 | 400 | 836 ms | invalid temperature: only 1 is allowed for this model |
| 月之暗面 Kimi | `kimi-k2.7-code` | 人工登记 |  | 🟠 请求被拒 | 未测 | 400 | 1299 ms | invalid temperature: only 1 is allowed for this model |
| 阿里云百炼 DashScope | `qwen3.8-max` | 人工登记 |  | ⏭️ 无法判断 | 未测 | - | - | 缺少环境变量 DASHSCOPE_KEY |
| 阿里云百炼 DashScope | `qwen3.8-flash` | 人工登记 |  | ⏭️ 无法判断 | 未测 | - | - | 缺少环境变量 DASHSCOPE_KEY |
| 阿里云百炼 DashScope | `qwen-plus` | 人工登记 |  | ⏭️ 无法判断 | 未测 | - | - | 缺少环境变量 DASHSCOPE_KEY |
| 阿里云百炼 DashScope | `qwen-turbo` | 人工登记 |  | ⏭️ 无法判断 | 未测 | - | - | 缺少环境变量 DASHSCOPE_KEY |
| 阿里云百炼 DashScope | `qwen-long` | 人工登记 | 10M | ⏭️ 无法判断 | 未测 | - | - | 缺少环境变量 DASHSCOPE_KEY |
| 硅基流动 SiliconFlow | `Qwen/Qwen3-8B` | 人工登记 |  | ✅ 正常可用 | 🔧 原生工具调用 | 200 | 4814 ms |  |
| 硅基流动 SiliconFlow | `Qwen/Qwen3.5-4B` | 人工登记 |  | ✅ 正常可用 | 🔧 原生工具调用 | 200 | 55262 ms |  |
| 硅基流动 SiliconFlow | `deepseek-ai/DeepSeek-R1-0528-Qwen3-8B` | 人工登记 |  | ✅ 正常可用 | — 不支持工具 | 200 | 8036 ms |  |
| 硅基流动 SiliconFlow | `THUDM/GLM-Z1-9B-0414` | 人工登记 |  | ✅ 正常可用 | 〽️ 收参不吐调用 | 200 | 3429 ms | （轮换中，沿用上轮结果） |
| 硅基流动 SiliconFlow | `Qwen/Qwen2.5-72B-Instruct` | 自动发现 | 32K | ✅ 正常可用 | 🔧 原生工具调用 | 200 | 975 ms | （轮换中，沿用上轮结果） |
| 硅基流动 SiliconFlow | `Qwen/Qwen2.5-7B-Instruct` | 自动发现 | 32K | ✅ 正常可用 | 🔧 原生工具调用 | 200 | 979 ms | （轮换中，沿用上轮结果） |
| 硅基流动 SiliconFlow | `THUDM/GLM-4-9B-0414` | 自动发现 | 32K | ✅ 正常可用 | 🔧 原生工具调用 | 200 | 2034 ms | （轮换中，沿用上轮结果） |
| 硅基流动 SiliconFlow | `XingChenAGI/Xing4.0-29B` | 自动发现 | 262K | ✅ 正常可用 | 〽️ 收参不吐调用 | 200 | 1371 ms | （轮换中，沿用上轮结果） |
| 硅基流动 SiliconFlow | `tencent/Hunyuan-MT-7B` | 自动发现 | 32K | ✅ 正常可用 | — 不支持工具 | 200 | 1108 ms | （轮换中，沿用上轮结果） |
| 魔搭 ModelScope | `Qwen/Qwen3.8-27B` | 人工登记 |  | ✅ 正常可用 | 〽️ 收参不吐调用 | 200 | 1964 ms |  |
| 魔搭 ModelScope | `deepseek-ai/DeepSeek-V4.1-Flash` | 人工登记 |  | ✅ 正常可用 | 🔧 原生工具调用 | 200 | 1394 ms |  |
| 魔搭 ModelScope | `ZhipuAI/GLM-4.7-Flash` | 人工登记 |  | ✅ 正常可用 | 🔧 原生工具调用 | 200 | 40896 ms |  |
| 魔搭 ModelScope | `stepfun-ai/Step-3.7-Flash` | 人工登记 |  | ✅ 正常可用 | 🔧 原生工具调用 | 200 | 1838 ms | （轮换中，沿用上轮结果） |
| 腾讯混元 / TokenHub | `hy4-preview` | 人工登记 |  | ⏭️ 无法判断 | 未测 | - | - | 缺少环境变量 HUNYUAN_KEY |
| 腾讯混元 / TokenHub | `hy3-preview` | 人工登记 |  | ⏭️ 无法判断 | 未测 | - | - | 缺少环境变量 HUNYUAN_KEY |
| 百度千帆 Qianfan | `ERNIE-4.5-Turbo-128K` | 人工登记 | 131K | ⏭️ 无法判断 | 未测 | - | - | 缺少环境变量 QIANFAN_KEY |
| 百度千帆 Qianfan | `ERNIE-4.5-Turbo-32K` | 人工登记 | 32K | ⏭️ 无法判断 | 未测 | - | - | 缺少环境变量 QIANFAN_KEY |
| 百度千帆 Qianfan | `DeepSeek-R1` | 人工登记 |  | ⏭️ 无法判断 | 未测 | - | - | 缺少环境变量 QIANFAN_KEY |
| 百度千帆 Qianfan | `Kimi-K2-Instruct` | 人工登记 |  | ⏭️ 无法判断 | 未测 | - | - | 缺少环境变量 QIANFAN_KEY |
| 火山方舟 Volcengine Ark | `doubao-seed-2-1-pro-260628` | 人工登记 |  | ⏭️ 无法判断 | 未测 | - | - | 缺少环境变量 VOLC_ARK_KEY |
| 火山方舟 Volcengine Ark | `doubao-seed-2-1-lite-260915` | 人工登记 |  | ⏭️ 无法判断 | 未测 | - | - | 缺少环境变量 VOLC_ARK_KEY |
| 火山方舟 Volcengine Ark | `doubao-seed-2-1-turbo-260628` | 人工登记 |  | ⏭️ 无法判断 | 未测 | - | - | 缺少环境变量 VOLC_ARK_KEY |
| 讯飞星火 Spark | `lite` | 人工登记 | 8K | ⏭️ 无法判断 | 未测 | - | - | 缺少环境变量 SPARK_KEY |
| MiniMax | `MiniMax-M3` | 人工登记 |  | ⏭️ 无法判断 | 未测 | - | - | 缺少环境变量 MINIMAX_KEY |
| MiniMax | `MiniMax-M2.7` | 人工登记 |  | ⏭️ 无法判断 | 未测 | - | - | 缺少环境变量 MINIMAX_KEY |
| MiniMax | `MiniMax-M2.5` | 人工登记 |  | ⏭️ 无法判断 | 未测 | - | - | 缺少环境变量 MINIMAX_KEY |
| 阶跃星辰 StepFun | `step-gui` | 人工登记 |  | ⏭️ 无法判断 | 未测 | - | - | 缺少环境变量 STEPFUN_KEY |
| 零一万物 Yi | `yi-lightning` | 人工登记 | 16K | ⏭️ 无法判断 | 未测 | - | - | 缺少环境变量 YI_KEY |
| 零一万物 Yi | `yi-vision-v2` | 人工登记 |  | ⏭️ 无法判断 | 未测 | - | - | 缺少环境变量 YI_KEY |
| 百川智能 Baichuan | `Baichuan4-Turbo` | 人工登记 | 32K | ⏭️ 无法判断 | 未测 | - | - | 缺少环境变量 BAICHUAN_KEY |
| 百川智能 Baichuan | `Baichuan-M3-Plus` | 人工登记 |  | ⏭️ 无法判断 | 未测 | - | - | 缺少环境变量 BAICHUAN_KEY |
| OpenRouter | `openrouter/free` | 人工登记 | 200K | 🔵 目录已确认 | 未测 | 200 | - | 公开目录中存在；未配密钥，无法验证可用性（轮换中，沿用上轮结果） |
| OpenRouter | `qwen/qwen3.8-27b:free` | 人工登记 | 262K | 🔵 目录已确认 | 未测 | 200 | - | 公开目录中存在；未配密钥，无法验证可用性（轮换中，沿用上轮结果） |
| OpenRouter | `cohere/north-mini-code:free` | 自动发现 | 256K | 🔵 目录已确认 | 未测 | 200 | - | 公开目录中存在；未配密钥，无法验证可用性（轮换中，沿用上轮结果） |
| OpenRouter | `dots-studio/dots-3-note-preview:free` | 自动发现 | 512K | 🔵 目录已确认 | 未测 | 200 | - | 公开目录中存在；未配密钥，无法验证可用性（轮换中，沿用上轮结果） |
| OpenRouter | `google/gemma-4-26b-a4b-it:free` | 自动发现 | 262K | 🔵 目录已确认 | 未测 | 200 | - | 公开目录中存在；未配密钥，无法验证可用性（轮换中，沿用上轮结果） |
| OpenRouter | `google/gemma-4-31b-it:free` | 自动发现 | 262K | 🔵 目录已确认 | 未测 | 200 | - | 公开目录中存在；未配密钥，无法验证可用性（轮换中，沿用上轮结果） |
| OpenRouter | `inclusionai/ling-3.0-flash-sante:free` | 自动发现 | 262K | 🔵 目录已确认 | 未测 | 200 | - | 公开目录中存在；未配密钥，无法验证可用性（轮换中，沿用上轮结果） |
| OpenRouter | `liquid/lfm-2.5-2.6b:free` | 自动发现 | 65K | 🔵 目录已确认 | 未测 | 200 | - | 公开目录中存在；未配密钥，无法验证可用性（轮换中，沿用上轮结果） |
| OpenRouter | `nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free` | 自动发现 | 256K | ✅ 正常可用 | 〽️ 收参不吐调用 | 200 | 321 ms | （轮换中，沿用上轮结果） |
| OpenRouter | `nvidia/nemotron-3-super-120b-a12b:free` | 自动发现 | 262K | ✅ 正常可用 | 🔧 原生工具调用 | 200 | 361 ms | （轮换中，沿用上轮结果） |
| OpenRouter | `nvidia/nemotron-3-ultra-550b-a55b:free` | 自动发现 | 1M | ✅ 正常可用 | 〽️ 收参不吐调用 | 200 | 1112 ms | （轮换中，沿用上轮结果） |
| OpenRouter | `nvidia/nemotron-3.5-lightning:free` | 自动发现 | 1M | ✅ 正常可用 | 🔧 原生工具调用 | 200 | 67639 ms | （轮换中，沿用上轮结果） |
| OpenRouter | `poolside/laguna-s-2.1:free` | 自动发现 | 262K | ✅ 正常可用 | 🔧 原生工具调用 | 200 | 621 ms | （轮换中，沿用上轮结果） |
| OpenRouter | `poolside/laguna-xs-2.1:free` | 自动发现 | 262K | ⚠️ 限流/额度耗尽 | 未测 | 429 | 88 ms | Provider returned error（轮换中，沿用上轮结果） |
| OpenRouter | `stealth/space-bunny-alpha` | 自动发现 | 1M | ✅ 正常可用 | 🔧 原生工具调用 | 200 | 966 ms | （轮换中，沿用上轮结果） |
| OpenRouter | `thinkingmachines/inkling-small:free` | 自动发现 | 1M | 🔑 密钥失效/无权限 | 未测 | 403 | 116 ms | thinkingmachines/inkling-small:free is only available on agentic harnesses. Try plugging it into a coding agent or productivity app listed on https://openrouter.ai/apps |
| OpenRouter | `thinkingmachines/inkling:free` | 自动发现 | 1M | 🔑 密钥失效/无权限 | 未测 | 403 | 36 ms | thinkingmachines/inkling:free is only available on agentic harnesses. Try plugging it into a coding agent or productivity app listed on https://openrouter.ai/apps |
| OpenRouter | `apodex/apodex-1.1-mini:free` | 自动发现 | 262K | ✅ 正常可用 | 🔧 原生工具调用 | 200 | 571 ms |  |
| OpenRouter | `inclusionai/ling-3.1-flash` | 自动发现 | 262K | ⚠️ 限流/额度耗尽 | 未测 | 402 | 55 ms | Insufficient credits. This account never purchased credits. Make sure your key is on the correct account or org, and if so, purchase more at https://openrouter.ai/settings/credits（轮换中，沿用上轮结果） |
| Groq | `openai/gpt-oss-120b` | 人工登记 | 131K | ⏭️ 无法判断 | 未测 | - | - | 缺少环境变量 GROQ_KEY |
| Groq | `openai/gpt-oss-20b` | 人工登记 | 131K | ⏭️ 无法判断 | 未测 | - | - | 缺少环境变量 GROQ_KEY |
| Groq | `qwen/qwen3.8-27b` | 人工登记 |  | ⏭️ 无法判断 | 未测 | - | - | 缺少环境变量 GROQ_KEY |
| Google Gemini | `gemini-3.8-flash` | 人工登记 | 1M | ⏭️ 无法判断 | 未测 | - | - | 缺少环境变量 GEMINI_KEY |
| Google Gemini | `gemini-3.5-flash` | 人工登记 | 1M | ⏭️ 无法判断 | 未测 | - | - | 缺少环境变量 GEMINI_KEY |
| Google Gemini | `gemini-3.1-flash-lite` | 人工登记 | 1M | ⏭️ 无法判断 | 未测 | - | - | 缺少环境变量 GEMINI_KEY |
| Google Gemini | `gemini-2.5-flash` | 人工登记 | 1M | ⏭️ 无法判断 | 未测 | - | - | 缺少环境变量 GEMINI_KEY |
| Cerebras | `gpt-oss-120b` | 人工登记 | 131K | ⏭️ 无法判断 | 未测 | - | - | 缺少环境变量 CEREBRAS_KEY |
| Cerebras | `qwen-3.8-27b` | 人工登记 |  | ⏭️ 无法判断 | 未测 | - | - | 缺少环境变量 CEREBRAS_KEY |
| Mistral AI | `mistral-small-2603` | 人工登记 |  | ⏭️ 无法判断 | 未测 | - | - | 缺少环境变量 MISTRAL_KEY |
| Mistral AI | `mistral-moderation-2603` | 人工登记 |  | ⏭️ 无法判断 | 未测 | - | - | 缺少环境变量 MISTRAL_KEY |
| Together AI | `Prism-ML/Ternary-Bonsai-27B` | 人工登记 |  | ⏭️ 无法判断 | 未测 | - | - | 缺少环境变量 TOGETHER_KEY |
| Together AI | `together/Tev1-4B-experimental` | 人工登记 |  | ⏭️ 无法判断 | 未测 | - | - | 缺少环境变量 TOGETHER_KEY |
| NVIDIA NIM | `deepseek-ai/deepseek-v4.1-flash` | 人工登记 |  | 🔵 目录已确认 | 未测 | 200 | - | 公开目录中存在；未配密钥，无法验证可用性 |
| NVIDIA NIM | `z-ai/glm-5-3` | 人工登记 |  | ⚪ 目录中已消失 | 未测 | - | - | 平台公开目录里已经找不到这个模型了 |
| NVIDIA NIM | `moonshotai/kimi-k3` | 人工登记 |  | 🔵 目录已确认 | 未测 | 200 | - | 公开目录中存在；未配密钥，无法验证可用性 |
| NVIDIA NIM | `nvidia/nemotron-3-ultra-550b-a55b` | 人工登记 |  | 🔵 目录已确认 | 未测 | 200 | - | 公开目录中存在；未配密钥，无法验证可用性 |
| NVIDIA NIM | `openai/gpt-oss-20b` | 人工登记 |  | 🔵 目录已确认 | 未测 | 200 | - | 公开目录中存在；未配密钥，无法验证可用性 |
| SambaNova (SambaCloud) | `DeepSeek-V3.2` | 人工登记 |  | 🔵 目录已确认 | 未测 | 200 | - | 公开目录中存在；未配密钥，无法验证可用性 |
| SambaNova (SambaCloud) | `DeepSeek-V3.1` | 人工登记 |  | 🔵 目录已确认 | 未测 | 200 | - | 公开目录中存在；未配密钥，无法验证可用性 |
| SambaNova (SambaCloud) | `Meta-Llama-3.3-70B-Instruct` | 人工登记 | 131K | 🔵 目录已确认 | 未测 | 200 | - | 公开目录中存在；未配密钥，无法验证可用性 |
| SambaNova (SambaCloud) | `gpt-oss-120b` | 人工登记 |  | 🔵 目录已确认 | 未测 | 200 | - | 公开目录中存在；未配密钥，无法验证可用性 |
| Nebius Token Factory | `Qwen/Qwen3-235B-A22B` | 人工登记 |  | ⏭️ 无法判断 | 未测 | - | - | 缺少环境变量 NEBIUS_KEY |
| Nebius Token Factory | `moonshotai/Kimi-K2.5` | 人工登记 |  | ⏭️ 无法判断 | 未测 | - | - | 缺少环境变量 NEBIUS_KEY |
| Novita AI | `inclusionai/ling-3.1-flash` | 人工登记 |  | 🔵 目录已确认 | 未测 | 200 | - | 公开目录中存在；未配密钥，无法验证可用性 |
| Novita AI | `inclusionai/ling-3.0-flash-sante` | 人工登记 |  | 🔵 目录已确认 | 未测 | 200 | - | 公开目录中存在；未配密钥，无法验证可用性 |
| Novita AI | `inclusionai/ling-3.0-flash-vl` | 人工登记 |  | 🔵 目录已确认 | 未测 | 200 | - | 公开目录中存在；未配密钥，无法验证可用性 |
| Novita AI | `bunny` | 自动发现 | 262K | 🔵 目录已确认 | 未测 | 200 | - | 公开目录中存在；未配密钥，无法验证可用性 |
| Novita AI | `dev/glm46` | 自动发现 | 256K | 🔵 目录已确认 | 未测 | 200 | - | 公开目录中存在；未配密钥，无法验证可用性 |
| Novita AI | `apodex/apodex-1.1-mini` | 自动发现 | 262K | 🔵 目录已确认 | 未测 | 200 | - | 公开目录中存在；未配密钥，无法验证可用性 |
| Cloudflare Workers AI | `@cf/meta/llama-3.3-70b-instruct-fp8-fast` | 人工登记 |  | ⏭️ 无法判断 | 未测 | - | - | 缺少环境变量 CLOUDFLARE_API_TOKEN, CLOUDFLARE_ACCOUNT_ID |
| Cloudflare Workers AI | `@cf/qwen/qwen3.8-27b` | 人工登记 |  | ⏭️ 无法判断 | 未测 | - | - | 缺少环境变量 CLOUDFLARE_API_TOKEN, CLOUDFLARE_ACCOUNT_ID |
| Cloudflare Workers AI | `@cf/openai/gpt-oss-120b` | 人工登记 |  | ⏭️ 无法判断 | 未测 | - | - | 缺少环境变量 CLOUDFLARE_API_TOKEN, CLOUDFLARE_ACCOUNT_ID |
| Cloudflare Workers AI | `@cf/zai-org/glm-4.7-flash` | 人工登记 |  | ⏭️ 无法判断 | 未测 | - | - | 缺少环境变量 CLOUDFLARE_API_TOKEN, CLOUDFLARE_ACCOUNT_ID |

## 客户端配置示例

任意支持 OpenAI 兼容协议的客户端（Cline / Cherry Studio / NextChat / One API / Roo Code …）
填上表中「正常可用」那行的 `BaseURL`、你申请的 Key 和 `模型 ID` 即可：

```json
{
  "apiProvider": "openai",
  "openAiBaseUrl": "https://open.bigmodel.cn/api/paas/v4",
  "openAiApiKey": "$ZHIPU_KEY",
  "openAiModelId": "glm-4.7-flash"
}
```

> Cline 里对应字段：API Provider 选 `OpenAI Compatible`，Base URL 填上表的 BaseURL，
> API Key 填你的密钥，Model ID 填模型 ID。

## 部署到自己的仓库（5 分钟）

1. **新建仓库**：GitHub 上新建一个仓库（公开私有都可以），把本目录的文件推上去：

   ```bash
   git init && git add . && git commit -m "init: 免费 LLM API 状态清单"
   git branch -M main
   git remote add origin https://github.com/<你的用户名>/free-llm-api-list.git
   git push -u origin main
   ```

2. **加密钥**：仓库 **Settings → Secrets and variables → Actions → New repository secret**，
   Name 填上表里的「密钥变量」（如 `ZHIPU_KEY`），Secret 填平台控制台申请的 Key。
   只加你实际有的平台即可。
3. **确认写权限**：**Settings → Actions → General → Workflow permissions** 选
   *Read and write permissions*（工作流里已经声明 `permissions: contents: write`，
   但如果这一步被组织策略限制，push 会失败）。
4. **手动跑一次**：**Actions → 更新免费 LLM API 状态 → Run workflow**，
   之后每 8 小时会自动更新，也可以在触发时填 `only` 只检查某几个平台。

> 想降低提交频率，把 `.github/workflows/update.yml` 里的 `cron` 改成 `0 2 * * *`（每天一次）即可。

## 自动更新原理

GitHub Actions 每 8 小时启动一次云环境，运行 `update_list.py`，全程不需要服务器。
脚本只用 Python 标准库，**不需要 pip install**。每一轮跑四件事：

1. **匿名探活**：给每个平台发一条用「无效密钥」的请求。鉴权通常发生在解析模型之前，
   所以返回 `401/403/400` 就说明 **服务活着、地址没变**；`404` 说明路径变了或服务下线；
   连不上说明域名不通。**这一步完全不需要真实密钥**，28 个平台全都有状态。
2. **同步目录**：请求各平台的 `GET /models`。有 7 家的目录是公开可读的（不需要密钥），
   其余需要密钥。读到之后和本地清单对比，就能发现**模型增删和改名**。
3. **自动发现**：目录里能被机器确证免费的模型（定价字段为 0、或 ID 带 `:free`）
   自动写进 `models.auto.json` 并纳入下一轮检测；名字像但无法确证的只进「候选区」。
   自动收进来的模型如果连续 3 轮实测失败，会被自动剔除（自净）。
4. **逐模型实测**：对**配了密钥**的平台，每个模型发一条 `max_tokens=1` 的极短请求，
   几乎不消耗免费额度，按返回码判定可用性；可用的模型再带 `tools` 发一条真实请求，
   只有返回里**真的吐出 `tool_calls`** 才标 🔧 —— 这才是 agent（DSH/Cline/Roo）能用的模型。
   为省额度每轮只抽测一批，各模型轮流上，结论跨轮保留。
5. **看外部清单**：拉别家维护的模型目录（Cline 清单、HuggingFace Router），和上一轮比对，
   有增删、有新的 0 元组合就记下来 —— 用别人的清单当传感器。
6. **盯官方文档**：把十几个官方限流/定价页抓一遍，**只比对内容摘要，不解析数字**。
   页面一变就报警，然后人工去看一眼。政策数字难解析，但「页面变了」很容易检测。

然后把结果写成 README / CSV / status.json，状态有变化时追加 history.jsonl，最后 commit & push。

### 产出文件

| 文件 | 用途 |
| --- | --- |
| `README.md` | 本文件，可读表格版，GitHub 直接预览 |
| `free_llm_api.csv` | 可下载表格（带 BOM，Excel 双击不乱码） |
| `status.json` | 结构化数据，供程序调用（例如自动切换代理） |
| `providers.json` | 平台与模型清单 + 官方核实的政策数据（人工维护，改清单不用碰代码） |
| `models.auto.json` | **脚本自己维护**的自动纳管模型池（确证免费的才进，连续失败自动剔除） |
| `sources.json` | 外部清单的模型 ID 快照 + 官方文档页的内容摘要（用来做变更检测） |
| `history.jsonl` | 状态**变化**历史，一行一次变更快照 |

三层模型池的关系：

| 文件 | 谁写 | 作用 |
| --- | --- | --- |
| `providers.json` | 人工 | 骨架：平台地址、申请入口、模型清单、官方政策数据 |
| `models.custom.json` | 人工 | 你自己增删的模型（可选，默认没有这个文件） |
| `models.auto.json` | **脚本** | 自动发现的模型，不用管它，它会自己长也会自己瘦 |

`status.json` 每次都会因为时间戳变化而提交一次（相当于心跳，能看出定时任务有没有在跑）；
`history.jsonl` 只在状态变化或发现增减时追加，所以历史记录是干净的。

## 如何添加 / 更换密钥

1. 打开仓库 **Settings → Secrets and variables → Actions → New repository secret**
2. Name 填上表里的「密钥变量」（如 `ZHIPU_KEY`），Secret 填平台控制台申请的 Key
3. 到 **Actions → 更新免费 LLM API 状态 → Run workflow** 手动跑一次，或等下一次定时任务

没配密钥的平台会显示 ⏭️ 未配置密钥，不影响其他平台检测；换 Key 直接编辑同名 Secret 即可。

### 想增删模型

复制 `models.custom.example.json` 为 `models.custom.json` 后修改并提交，工作流会自动带上：

- 同 `env` 的条目：覆盖该平台字段，`models` 按 `id` 追加或合并
- 新 `env` 的条目：作为新平台追加

也可以直接改 `providers.json` —— 平台与模型清单已经和代码分开了，改清单不用碰脚本。

### 本地运行

```bash
python update_list.py                              # 检测全部平台（探活 + 目录 + 实测）
python update_list.py --only ZHIPU_KEY,GROQ_KEY     # 只检测指定平台
python update_list.py --list                        # 只看模型池，不发任何请求
python update_list.py --no-probe --no-discover      # 只实测，不探活不同步目录
python update_list.py --adopt off                   # 只把发现记进候选区，不自动纳入
python update_list.py --adopt aggressive            # 名字像免费的也自动收进来
python update_list.py --custom models.custom.json   # 带上自定义模型池
```

环境变量就是上表的密钥变量名，本地可以临时设：

```bash
ZHIPU_KEY=xxxx python update_list.py --only ZHIPU_KEY     # Linux / macOS
$env:ZHIPU_KEY="xxxx"; python update_list.py --only ZHIPU_KEY  # Windows PowerShell
```

## 常见问题

| 现象 | 原因与处理 |
| --- | --- |
| 全部显示 ⏭️ 无法判断 | 没配密钥，且该平台目录不公开 —— 这是正常的，平台级「接口探活」仍然有效 |
| 平台是 🟢 但模型全是 🔑 | 接口活着，是密钥不对（复制错了、被吊销、或没开通对应模型） |
| 平台是 ❌ 接口已失效 | 该平台的接口路径返回 404，可能已下线或改地址，需要改 `providers.json` 里的 `base_url` |
| 某个模型 ⚪ 目录中已消失 | 平台目录里查不到这个 ID 了；看「相近的 ID」列，多半只是改了名 |
| 一直是 ⚠️ 限流 | 免费额度确实用完了（或账号在共享 IP 上被限速），等下个周期再看 |
| 自动纳入了奇怪的模型 | 把 `--adopt` 改成 `off` 或 `safe`，并在 `models.auto.json` 里删掉它 |
| 报 `HttpError: 403` 且没提交 | 仓库的 Workflow permissions 还是只读，参考「部署到自己的仓库」第 3 步 |
| 大量 📡 域名不通 | GitHub Runner 出口或被墙平台连通性问题，脚本会自动重试，偶发可忽略 |

## 历史更新记录（最近 10 次）

| 时间 | 可用模型 | 状态变化 |
| --- | ---: | ---: |
| 2026-10-03 11:00:50 | 23/96 | 6 |
| 2026-10-03 04:15:15 | 18/96 | 6 |
| 2026-10-02 22:19:34 | 13/95 | 9 |
| 2026-10-02 13:54:23 | 10/95 | 92 |
| 2026-10-02 13:32:37 | 0/3 | 3 |
| 2026-10-02 09:55:33 | 12/95 | 3 |
| 2026-10-02 09:53:30 | 10/95 | 4 |
| 2026-10-02 09:51:58 | 6/95 | 6 |
| 2026-10-02 09:51:20 | 0/95 | 31 |
| 2026-10-02 00:40:12 | 12/94 | 7 |

完整记录见 `history.jsonl`。

---

## 说明与免责

- 「免费」指平台公开的免费额度 / 免费模型，各平台政策随时可能调整，请以官方控制台为准。
- `429` 只代表**此刻**限流或额度用尽，不代表模型永久失效；隔一段时间会自动恢复。
- 上下文长度、额度类型、预期有效期来自公开文档，仅作参考，不作为计费依据。
- 本仓库只做可用性探测，不代理、不分发任何模型能力，也不存储任何密钥。
