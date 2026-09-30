# 免费 LLM API 状态清单

自动巡检各大平台免费大模型接口的可用性，每 4 小时更新一次。
密钥只存放在 GitHub Secrets 中，脚本不落地、不外传，仓库里只留下状态结果。

- **最后更新**：2026-09-30 19:57:02 (北京时间 UTC+8)
- **本次耗时**：17.4 秒　|　**巡检频率**：`0 */4 * * *`
- **实测可用**：**0 / 83**（未配密钥但目录已确认存在 🔵 23 个）　|　**已配置平台**：0 / 28
- **接口探活**：27 个平台已探活（🟢 在线 23，❌ 失效 2，📡 不通 1）　|　**可读目录**：6 个平台（其中 6 个无需密钥）

> 这套清单是**自己维护自己**的：平台接口死活靠「匿名探活」（用一个无效密钥试，
> 401 说明服务活着），模型增删靠拉平台公开的 `/models` 目录，
> 能被机器确证免费的模型会自动纳入 `models.auto.json`，连续 3 轮实测失败会自动剔除。

| 状态 | 数量 | 说明 |
| --- | ---: | --- |
| ✅ 正常可用 | 0 | 用你的密钥实测返回 200 |
| 🔵 目录已确认 | 23 | 未配密钥，但平台公开目录中确认该模型存在 |
| ⚠️ 限流/额度耗尽 | 0 | 返回 429 或提示配额/余额不足 |
| 🟠 请求被拒 | 0 | 返回 400，参数或模型不被支持 |
| 🔑 密钥失效/无权限 | 0 | 返回 401/403，密钥无效或权限变更 |
| ⚪ 目录中已消失 | 12 | 公开目录里查不到它了，疑似已下架 |
| ❌ 模型已下架 | 0 | 返回 404，模型 ID 不存在 |
| 🌐 服务端异常 | 0 | 返回 5xx，平台侧故障 |
| 📡 网络超时/不可达 | 0 | 连接失败或超时 |
| ❔ 未知状态 | 0 | 其他返回码 |
| ⏭️ 无法判断 | 48 | 未配密钥，且平台目录不公开，无从判断 |

**平台级「接口探活」**（不需要任何密钥，用无效密钥试出来的）：

| 探活结果 | 平台数 | 说明 |
| --- | ---: | --- |
| 🟢 接口在线 | 23 | 鉴权层正常拒绝了无效密钥，说明服务活着、地址没变 |
| 🔓 无需密钥 | 0 | 无效密钥竟然返回 200，接口可能不校验密钥 |
| 🟠 接口异常 | 1 | 能连上，但返回 5xx / 410 等服务端错误 |
| ❌ 接口已失效 | 2 | 返回 404，路径变更或服务已下线 |
| 📡 域名不通 | 1 | 连接失败或超时 |
| ❔ 探活异常 | 0 | 返回码无法归类 |
| ⏭️ 未探活 | 1 | 缺少必要环境变量，或本次关闭了探活 |

## 平台总览

| 平台 | 接口探活 | 模型状态 | 密钥变量 | 目录 | 额度类型 | 申请地址 |
| --- | --- | --- | --- | ---: | --- | --- |
| DeepSeek 深度求索 | 🟢 接口在线 | ⏭️ 无法判断 0/2 | `DEEPSEEK_KEY` | - | 注册赠送测试额度，用完后按量计费 | [控制台](https://platform.deepseek.com/api_keys) |
| 智谱 AI (BigModel) | 🟢 接口在线 | ⏭️ 无法判断 0/3 | `ZHIPU_KEY` | - | Flash 系列免费，有限速 | [控制台](https://open.bigmodel.cn/usercenter/apikeys) |
| 月之暗面 Kimi | 🟢 接口在线 | ⏭️ 无法判断 0/2 | `MOONSHOT_KEY` | - | 新用户赠送额度 | [控制台](https://platform.moonshot.cn/console/api-keys) |
| 阿里云百炼 DashScope | 🟢 接口在线 | ⏭️ 无法判断 0/3 | `DASHSCOPE_KEY` | - | 新用户每个模型 100 万 tokens 免费额度 | [控制台](https://bailian.console.aliyun.com/) |
| 硅基流动 SiliconFlow | 🟢 接口在线 | ⏭️ 无法判断 0/3 | `SILICONFLOW_KEY` | - | 部分小模型免费，有限速 | [控制台](https://cloud.siliconflow.cn/account/ak) |
| 魔搭 ModelScope | 🟢 接口在线 | ⚪ 目录中已消失 0/3 | `MODELSCOPE_KEY` | 35（公开） | 每日 2000 次免费调用 | [控制台](https://modelscope.cn/my/myaccesstoken) |
| 腾讯混元 Hunyuan | 🟢 接口在线 | ⏭️ 无法判断 0/2 | `HUNYUAN_KEY` | - | 新用户赠送免费额度 | [控制台](https://console.cloud.tencent.com/hunyuan/api-key) |
| 百度千帆 Qianfan | 🟢 接口在线 | ⏭️ 无法判断 0/2 | `QIANFAN_KEY` | - | ERNIE Speed 系列免费 | [控制台](https://console.bce.baidu.com/iam/#/iam/apikey/list) |
| 火山方舟 Volcengine Ark | 🟢 接口在线 | ⏭️ 无法判断 0/2 | `VOLC_ARK_KEY` | - | 新用户每个模型 50 万 tokens 免费额度 | [控制台](https://console.volcengine.com/ark) |
| 讯飞星火 Spark | 🟢 接口在线 | ⏭️ 无法判断 0/2 | `SPARK_KEY` | - | Lite 版免费不限量（限速） | [控制台](https://console.xfyun.cn/services/bmx1) |
| MiniMax | 🟢 接口在线 | ⏭️ 无法判断 0/2 | `MINIMAX_KEY` | - | 注册赠送额度 | [控制台](https://platform.minimaxi.com/user-center/basic-information/interface-key) |
| 阶跃星辰 StepFun | 🟢 接口在线 | ⏭️ 无法判断 0/2 | `STEPFUN_KEY` | - | Flash 系列免费（限速） | [控制台](https://platform.stepfun.com/interface-key) |
| 零一万物 Yi | 🟠 接口异常 | ⏭️ 无法判断 0/1 | `YI_KEY` | - | 注册赠送额度 | [控制台](https://platform.lingyiwanwu.com/apikeys) |
| 百川智能 Baichuan | 🟢 接口在线 | ⏭️ 无法判断 0/1 | `BAICHUAN_KEY` | - | 新用户赠送 tokens | [控制台](https://platform.baichuan-ai.com/console/apikey) |
| OpenRouter | 🟢 接口在线 | 🔵 目录已确认 0/20 | `OPENROUTER_KEY` | 464（公开） | 免费模型每日次数受限（随账户余额放宽） | [控制台](https://openrouter.ai/keys) |
| Groq | 🟢 接口在线 | ⏭️ 无法判断 0/3 | `GROQ_KEY` | - | 免费层按 RPM/TPM/每日限额 | [控制台](https://console.groq.com/keys) |
| Google Gemini | 🟢 接口在线 | ⏭️ 无法判断 0/3 | `GEMINI_KEY` | - | 免费层按 RPM/RPD 限速 | [控制台](https://aistudio.google.com/app/apikey) |
| Cerebras | 🟢 接口在线 | ⏭️ 无法判断 0/3 | `CEREBRAS_KEY` | - | 免费层每日 100 万 tokens | [控制台](https://cloud.cerebras.ai/) |
| Mistral AI | 🟢 接口在线 | ⏭️ 无法判断 0/2 | `MISTRAL_KEY` | - | Experiment 免费层（需手机验证，限速） | [控制台](https://console.mistral.ai/api-keys/) |
| Together AI | 🟢 接口在线 | ⏭️ 无法判断 0/2 | `TOGETHER_KEY` | - | 新用户赠送额度 + 少量 free 模型 | [控制台](https://api.together.xyz/settings/api-keys) |
| NVIDIA NIM | ❌ 接口已失效 | ⚪ 目录中已消失 0/2 | `NVIDIA_KEY` | 81（公开） | 注册赠送 1000 credits | [控制台](https://build.nvidia.com/settings/api-keys) |
| SambaNova | 🟢 接口在线 | 🔵 目录已确认 0/2 | `SAMBANOVA_KEY` | 7（公开） | 免费层限速 | [控制台](https://cloud.sambanova.ai/apis) |
| Hyperbolic | ❌ 接口已失效 | ⏭️ 无法判断 0/2 | `HYPERBOLIC_KEY` | - | 注册赠送约 $1 额度 | [控制台](https://app.hyperbolic.xyz/settings) |
| Nebius AI Studio | 🟢 接口在线 | ⏭️ 无法判断 0/2 | `NEBIUS_KEY` | - | 注册赠送试用额度 | [控制台](https://studio.nebius.com/settings/api-keys) |
| Novita AI | 🟢 接口在线 | 🔵 目录已确认 0/6 | `NOVITA_KEY` | 120（公开） | 注册赠送试用额度 | [控制台](https://novita.ai/settings/key-management) |
| Chutes | 🟢 接口在线 | ⚪ 目录中已消失 0/2 | `CHUTES_KEY` | 14（公开） | 注册赠送少量额度 | [控制台](https://chutes.ai/app/api) |
| GitHub Models | 📡 域名不通 | ⏭️ 无法判断 0/2 | `GITHUB_MODELS_TOKEN` | - | 免费层按 RPM/RPD 限速 | [控制台](https://github.com/settings/tokens) |
| Cloudflare Workers AI | ⏭️ 未探活 | ⏭️ 无法判断 0/2 | `CLOUDFLARE_API_TOKEN` | - | 每日 10000 neurons 免费额度 | [控制台](https://dash.cloudflare.com/profile/api-tokens) |

## 自动发现

这一节的内容**全部由脚本自动产生**，不需要人工维护：

- **自动纳入**：从平台公开目录里读到、且能被机器确证免费的模型 → 自动进 `models.auto.json`
- **候选**：名字看起来免费但无法确证的 → 只列在这里，等你确认后才进池子
- **目录中消失**：我们登记了、但平台目录里已经查不到 → 大概率被下架了

> 当前自动纳入模式：**safe**（`safe` = 只收机器确证免费的；`aggressive` = 名字像的也收；`off` = 只记候选）

### 候选（未自动纳入，共 38 个）

名字看起来是免费档、但平台没给出可机器核对的定价信息，所以只列在这里。
想收进来就把对应 `id` 加到 `models.custom.json`，或者手动跑 `--adopt aggressive`。

| 平台 | 模型 | 依据 | 上下文 |
| --- | --- | --- | ---: |
| Chutes | `Nemotron-3-Nano-Omni-30B-TEE` | 疑似免费 | 131K |
| Chutes | `Qwen/Qwen3.5-397B-A17B-TEE` | 疑似免费 | 262K |
| Chutes | `Qwen/Qwen3.6-27B-TEE` | 疑似免费 | 262K |
| Chutes | `Qwen/Qwen3.8-27B-TEE` | 疑似免费 | 262K |
| Chutes | `deepseek-ai/DeepSeek-V4-Flash-0731-TEE` | 疑似免费 | 1M |
| Chutes | `google/gemma-4-31B-turbo-TEE` | 疑似免费 | 131K |
| NVIDIA NIM | `adept/fuyu-8b` | 疑似免费 |  |
| NVIDIA NIM | `aisingapore/sea-lion-7b-instruct` | 疑似免费 |  |
| NVIDIA NIM | `deepseek-ai/deepseek-coder-6.7b-instruct` | 疑似免费 |  |
| NVIDIA NIM | `deepseek-ai/deepseek-v4.1-flash` | 疑似免费 |  |
| NVIDIA NIM | `google/codegemma-1.1-7b` | 疑似免费 |  |
| NVIDIA NIM | `google/codegemma-7b` | 疑似免费 |  |
| NVIDIA NIM | `google/diffusiongemma-26b-a4b-it` | 疑似免费 |  |
| NVIDIA NIM | `google/gemma-3-4b-it` | 疑似免费 |  |
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
| … | 其余 8 个已截断 | | |

## 模型明细

| 平台 | 模型 ID | 来源 | 上下文 | 额度类型 | 预期有效期 | 状态 | HTTP | 延迟 | 备注 |
| --- | --- | --- | ---: | --- | --- | --- | ---: | ---: | --- |
| DeepSeek 深度求索 | `deepseek-chat` | 人工登记 | 128K | 注册赠送测试额度，用完后按量计费 | 额度用尽即止（非长期免费） | ⏭️ 无法判断 | - | - | 缺少环境变量 DEEPSEEK_KEY |
| DeepSeek 深度求索 | `deepseek-reasoner` | 人工登记 | 128K | 注册赠送测试额度，用完后按量计费 | 额度用尽即止（非长期免费） | ⏭️ 无法判断 | - | - | 缺少环境变量 DEEPSEEK_KEY |
| 智谱 AI (BigModel) | `glm-4-flash` | 人工登记 | 128K | Flash 系列免费，有限速 | 长期免费 | ⏭️ 无法判断 | - | - | 缺少环境变量 ZHIPU_KEY |
| 智谱 AI (BigModel) | `glm-4.5-flash` | 人工登记 | 128K | Flash 系列免费，有限速 | 长期免费 | ⏭️ 无法判断 | - | - | 缺少环境变量 ZHIPU_KEY |
| 智谱 AI (BigModel) | `glm-4v-flash` | 人工登记 | 8K | Flash 系列免费，有限速 | 长期免费 | ⏭️ 无法判断 | - | - | 缺少环境变量 ZHIPU_KEY |
| 月之暗面 Kimi | `kimi-k2-0905-preview` | 人工登记 | 262K | 新用户赠送额度 | 额度用尽即止 | ⏭️ 无法判断 | - | - | 缺少环境变量 MOONSHOT_KEY |
| 月之暗面 Kimi | `moonshot-v1-8k` | 人工登记 | 8K | 新用户赠送额度 | 额度用尽即止 | ⏭️ 无法判断 | - | - | 缺少环境变量 MOONSHOT_KEY |
| 阿里云百炼 DashScope | `qwen-turbo` | 人工登记 | 1M | 新用户每个模型 100 万 tokens 免费额度 | 自开通起 180 天有效 | ⏭️ 无法判断 | - | - | 缺少环境变量 DASHSCOPE_KEY |
| 阿里云百炼 DashScope | `qwen-plus` | 人工登记 | 131K | 新用户每个模型 100 万 tokens 免费额度 | 自开通起 180 天有效 | ⏭️ 无法判断 | - | - | 缺少环境变量 DASHSCOPE_KEY |
| 阿里云百炼 DashScope | `qwen-long` | 人工登记 | 10M | 新用户每个模型 100 万 tokens 免费额度 | 自开通起 180 天有效 | ⏭️ 无法判断 | - | - | 缺少环境变量 DASHSCOPE_KEY |
| 硅基流动 SiliconFlow | `Qwen/Qwen3-8B` | 人工登记 | 32K | 部分小模型免费，有限速 | 长期免费（免费名单会轮换） | ⏭️ 无法判断 | - | - | 缺少环境变量 SILICONFLOW_KEY |
| 硅基流动 SiliconFlow | `THUDM/glm-4-9b-chat` | 人工登记 | 32K | 部分小模型免费，有限速 | 长期免费（免费名单会轮换） | ⏭️ 无法判断 | - | - | 缺少环境变量 SILICONFLOW_KEY |
| 硅基流动 SiliconFlow | `deepseek-ai/DeepSeek-R1-0528-Qwen3-8B` | 人工登记 | 131K | 部分小模型免费，有限速 | 长期免费（免费名单会轮换） | ⏭️ 无法判断 | - | - | 缺少环境变量 SILICONFLOW_KEY |
| 魔搭 ModelScope | `Qwen/Qwen3-8B` | 人工登记 | 32K | 每日 2000 次免费调用 | 长期免费 | ⚪ 目录中已消失 | - | - | 平台公开目录里已经找不到这个模型了 |
| 魔搭 ModelScope | `deepseek-ai/DeepSeek-R1-Distill-Qwen-7B` | 人工登记 | 65K | 每日 2000 次免费调用 | 长期免费 | ⚪ 目录中已消失 | - | - | 平台公开目录里已经找不到这个模型了 |
| 魔搭 ModelScope | `Qwen/Qwen2.5-7B-Instruct` | 人工登记 | 32K | 每日 2000 次免费调用 | 长期免费 | ⚪ 目录中已消失 | - | - | 平台公开目录里已经找不到这个模型了 |
| 腾讯混元 Hunyuan | `hunyuan-turbos-latest` | 人工登记 | 32K | 新用户赠送免费额度 | 额度用尽即止 | ⏭️ 无法判断 | - | - | 缺少环境变量 HUNYUAN_KEY |
| 腾讯混元 Hunyuan | `hunyuan-lite` | 人工登记 | 32K | 新用户赠送免费额度 | 额度用尽即止 | ⏭️ 无法判断 | - | - | 缺少环境变量 HUNYUAN_KEY |
| 百度千帆 Qianfan | `ernie-speed-128k` | 人工登记 | 131K | ERNIE Speed 系列免费 | 长期免费（限速） | ⏭️ 无法判断 | - | - | 缺少环境变量 QIANFAN_KEY |
| 百度千帆 Qianfan | `ernie-4.5-turbo-128k` | 人工登记 | 131K | ERNIE Speed 系列免费 | 长期免费（限速） | ⏭️ 无法判断 | - | - | 缺少环境变量 QIANFAN_KEY |
| 火山方舟 Volcengine Ark | `doubao-seed-1-6-250615` | 人工登记 | 262K | 新用户每个模型 50 万 tokens 免费额度 | 额度用尽即止 | ⏭️ 无法判断 | - | - | 缺少环境变量 VOLC_ARK_KEY |
| 火山方舟 Volcengine Ark | `doubao-1-5-lite-32k-250115` | 人工登记 | 32K | 新用户每个模型 50 万 tokens 免费额度 | 额度用尽即止 | ⏭️ 无法判断 | - | - | 缺少环境变量 VOLC_ARK_KEY |
| 讯飞星火 Spark | `lite` | 人工登记 | 8K | Lite 版免费不限量（限速） | 长期免费 | ⏭️ 无法判断 | - | - | 缺少环境变量 SPARK_KEY |
| 讯飞星火 Spark | `generalv3.5` | 人工登记 | 8K | Lite 版免费不限量（限速） | 长期免费 | ⏭️ 无法判断 | - | - | 缺少环境变量 SPARK_KEY |
| MiniMax | `MiniMax-Text-01` | 人工登记 | 1M | 注册赠送额度 | 额度用尽即止 | ⏭️ 无法判断 | - | - | 缺少环境变量 MINIMAX_KEY |
| MiniMax | `abab6.5s-chat` | 人工登记 | 245K | 注册赠送额度 | 额度用尽即止 | ⏭️ 无法判断 | - | - | 缺少环境变量 MINIMAX_KEY |
| 阶跃星辰 StepFun | `step-1-flash` | 人工登记 | 8K | Flash 系列免费（限速） | 长期免费 | ⏭️ 无法判断 | - | - | 缺少环境变量 STEPFUN_KEY |
| 阶跃星辰 StepFun | `step-2-mini` | 人工登记 | 32K | Flash 系列免费（限速） | 长期免费 | ⏭️ 无法判断 | - | - | 缺少环境变量 STEPFUN_KEY |
| 零一万物 Yi | `yi-lightning` | 人工登记 | 16K | 注册赠送额度 | 额度用尽即止 | ⏭️ 无法判断 | - | - | 缺少环境变量 YI_KEY |
| 百川智能 Baichuan | `Baichuan4-Turbo` | 人工登记 | 32K | 新用户赠送 tokens | 额度用尽即止 | ⏭️ 无法判断 | - | - | 缺少环境变量 BAICHUAN_KEY |
| OpenRouter | `meta-llama/llama-3.3-70b-instruct:free` | 人工登记 | 131K | 免费模型每日次数受限（随账户余额放宽） | 长期免费（:free 名单会轮换） | ⚪ 目录中已消失 | - | - | 平台公开目录里已经找不到这个模型了 |
| OpenRouter | `deepseek/deepseek-r1:free` | 人工登记 | 163K | 免费模型每日次数受限（随账户余额放宽） | 长期免费（:free 名单会轮换） | ⚪ 目录中已消失 | - | - | 平台公开目录里已经找不到这个模型了 |
| OpenRouter | `google/gemini-2.0-flash-exp:free` | 人工登记 | 1M | 免费模型每日次数受限（随账户余额放宽） | 长期免费（:free 名单会轮换） | ⚪ 目录中已消失 | - | - | 平台公开目录里已经找不到这个模型了 |
| OpenRouter | `cohere/north-mini-code:free` | 自动发现 | 256K | 免费模型每日次数受限（随账户余额放宽） | 长期免费（:free 名单会轮换） | 🔵 目录已确认 | 200 | - | 公开目录中存在；未配密钥，无法验证可用性 |
| OpenRouter | `dots-studio/dots-3-note-preview:free` | 自动发现 | 512K | 免费模型每日次数受限（随账户余额放宽） | 长期免费（:free 名单会轮换） | 🔵 目录已确认 | 200 | - | 公开目录中存在；未配密钥，无法验证可用性 |
| OpenRouter | `google/gemma-4-26b-a4b-it:free` | 自动发现 | 262K | 免费模型每日次数受限（随账户余额放宽） | 长期免费（:free 名单会轮换） | 🔵 目录已确认 | 200 | - | 公开目录中存在；未配密钥，无法验证可用性 |
| OpenRouter | `google/gemma-4-31b-it:free` | 自动发现 | 262K | 免费模型每日次数受限（随账户余额放宽） | 长期免费（:free 名单会轮换） | 🔵 目录已确认 | 200 | - | 公开目录中存在；未配密钥，无法验证可用性 |
| OpenRouter | `inclusionai/ling-3.0-flash-sante:free` | 自动发现 | 262K | 免费模型每日次数受限（随账户余额放宽） | 长期免费（:free 名单会轮换） | 🔵 目录已确认 | 200 | - | 公开目录中存在；未配密钥，无法验证可用性 |
| OpenRouter | `liquid/lfm-2.5-2.6b:free` | 自动发现 | 65K | 免费模型每日次数受限（随账户余额放宽） | 长期免费（:free 名单会轮换） | 🔵 目录已确认 | 200 | - | 公开目录中存在；未配密钥，无法验证可用性 |
| OpenRouter | `nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free` | 自动发现 | 256K | 免费模型每日次数受限（随账户余额放宽） | 长期免费（:free 名单会轮换） | 🔵 目录已确认 | 200 | - | 公开目录中存在；未配密钥，无法验证可用性 |
| OpenRouter | `nvidia/nemotron-3-super-120b-a12b:free` | 自动发现 | 262K | 免费模型每日次数受限（随账户余额放宽） | 长期免费（:free 名单会轮换） | 🔵 目录已确认 | 200 | - | 公开目录中存在；未配密钥，无法验证可用性 |
| OpenRouter | `nvidia/nemotron-3-ultra-550b-a55b:free` | 自动发现 | 1M | 免费模型每日次数受限（随账户余额放宽） | 长期免费（:free 名单会轮换） | 🔵 目录已确认 | 200 | - | 公开目录中存在；未配密钥，无法验证可用性 |
| OpenRouter | `nvidia/nemotron-3.5-lightning:free` | 自动发现 | 1M | 免费模型每日次数受限（随账户余额放宽） | 长期免费（:free 名单会轮换） | 🔵 目录已确认 | 200 | - | 公开目录中存在；未配密钥，无法验证可用性 |
| OpenRouter | `openrouter/free` | 自动发现 | 200K | 免费模型每日次数受限（随账户余额放宽） | 长期免费（:free 名单会轮换） | 🔵 目录已确认 | 200 | - | 公开目录中存在；未配密钥，无法验证可用性 |
| OpenRouter | `poolside/laguna-s-2.1:free` | 自动发现 | 262K | 免费模型每日次数受限（随账户余额放宽） | 长期免费（:free 名单会轮换） | 🔵 目录已确认 | 200 | - | 公开目录中存在；未配密钥，无法验证可用性 |
| OpenRouter | `poolside/laguna-xs-2.1:free` | 自动发现 | 262K | 免费模型每日次数受限（随账户余额放宽） | 长期免费（:free 名单会轮换） | 🔵 目录已确认 | 200 | - | 公开目录中存在；未配密钥，无法验证可用性 |
| OpenRouter | `qwen/qwen3.8-27b:free` | 自动发现 | 262K | 免费模型每日次数受限（随账户余额放宽） | 长期免费（:free 名单会轮换） | 🔵 目录已确认 | 200 | - | 公开目录中存在；未配密钥，无法验证可用性 |
| OpenRouter | `stealth/space-bunny-alpha` | 自动发现 | 1M | 免费模型每日次数受限（随账户余额放宽） | 长期免费（:free 名单会轮换） | 🔵 目录已确认 | 200 | - | 公开目录中存在；未配密钥，无法验证可用性 |
| OpenRouter | `thinkingmachines/inkling-small:free` | 自动发现 | 1M | 免费模型每日次数受限（随账户余额放宽） | 长期免费（:free 名单会轮换） | 🔵 目录已确认 | 200 | - | 公开目录中存在；未配密钥，无法验证可用性 |
| OpenRouter | `thinkingmachines/inkling:free` | 自动发现 | 1M | 免费模型每日次数受限（随账户余额放宽） | 长期免费（:free 名单会轮换） | 🔵 目录已确认 | 200 | - | 公开目录中存在；未配密钥，无法验证可用性 |
| Groq | `llama-3.3-70b-versatile` | 人工登记 | 131K | 免费层按 RPM/TPM/每日限额 | 长期免费 | ⏭️ 无法判断 | - | - | 缺少环境变量 GROQ_KEY |
| Groq | `llama-3.1-8b-instant` | 人工登记 | 131K | 免费层按 RPM/TPM/每日限额 | 长期免费 | ⏭️ 无法判断 | - | - | 缺少环境变量 GROQ_KEY |
| Groq | `openai/gpt-oss-120b` | 人工登记 | 131K | 免费层按 RPM/TPM/每日限额 | 长期免费 | ⏭️ 无法判断 | - | - | 缺少环境变量 GROQ_KEY |
| Google Gemini | `gemini-2.5-flash` | 人工登记 | 1M | 免费层按 RPM/RPD 限速 | 长期免费 | ⏭️ 无法判断 | - | - | 缺少环境变量 GEMINI_KEY |
| Google Gemini | `gemini-2.5-flash-lite` | 人工登记 | 1M | 免费层按 RPM/RPD 限速 | 长期免费 | ⏭️ 无法判断 | - | - | 缺少环境变量 GEMINI_KEY |
| Google Gemini | `gemini-2.0-flash` | 人工登记 | 1M | 免费层按 RPM/RPD 限速 | 长期免费 | ⏭️ 无法判断 | - | - | 缺少环境变量 GEMINI_KEY |
| Cerebras | `llama3.3-70b` | 人工登记 | 131K | 免费层每日 100 万 tokens | 长期免费 | ⏭️ 无法判断 | - | - | 缺少环境变量 CEREBRAS_KEY |
| Cerebras | `qwen-3-32b` | 人工登记 | 131K | 免费层每日 100 万 tokens | 长期免费 | ⏭️ 无法判断 | - | - | 缺少环境变量 CEREBRAS_KEY |
| Cerebras | `gpt-oss-120b` | 人工登记 | 131K | 免费层每日 100 万 tokens | 长期免费 | ⏭️ 无法判断 | - | - | 缺少环境变量 CEREBRAS_KEY |
| Mistral AI | `mistral-small-latest` | 人工登记 | 131K | Experiment 免费层（需手机验证，限速） | 长期免费（限速） | ⏭️ 无法判断 | - | - | 缺少环境变量 MISTRAL_KEY |
| Mistral AI | `open-mistral-nemo` | 人工登记 | 131K | Experiment 免费层（需手机验证，限速） | 长期免费（限速） | ⏭️ 无法判断 | - | - | 缺少环境变量 MISTRAL_KEY |
| Together AI | `meta-llama/Llama-Vision-Free` | 人工登记 | 131K | 新用户赠送额度 + 少量 free 模型 | 额度用尽即止（free 名单会轮换） | ⏭️ 无法判断 | - | - | 缺少环境变量 TOGETHER_KEY |
| Together AI | `deepseek-ai/DeepSeek-R1-Distill-Llama-70B-free` | 人工登记 | 131K | 新用户赠送额度 + 少量 free 模型 | 额度用尽即止（free 名单会轮换） | ⏭️ 无法判断 | - | - | 缺少环境变量 TOGETHER_KEY |
| NVIDIA NIM | `deepseek-ai/deepseek-r1` | 人工登记 | 131K | 注册赠送 1000 credits | 额度用尽即止 | ⚪ 目录中已消失 | - | - | 平台公开目录里已经找不到这个模型了 |
| NVIDIA NIM | `meta/llama-3.3-70b-instruct` | 人工登记 | 131K | 注册赠送 1000 credits | 额度用尽即止 | ⚪ 目录中已消失 | - | - | 平台公开目录里已经找不到这个模型了 |
| SambaNova | `Meta-Llama-3.3-70B-Instruct` | 人工登记 | 131K | 免费层限速 | 长期免费（限速） | 🔵 目录已确认 | 200 | - | 公开目录中存在；未配密钥，无法验证可用性 |
| SambaNova | `DeepSeek-R1-Distill-Llama-70B` | 人工登记 | 131K | 免费层限速 | 长期免费（限速） | ⚪ 目录中已消失 | - | - | 平台公开目录里已经找不到这个模型了 |
| Hyperbolic | `Qwen/Qwen3-235B-A22B` | 人工登记 | 131K | 注册赠送约 $1 额度 | 额度用尽即止 | ⏭️ 无法判断 | - | - | 缺少环境变量 HYPERBOLIC_KEY |
| Hyperbolic | `meta-llama/Llama-3.3-70B-Instruct` | 人工登记 | 131K | 注册赠送约 $1 额度 | 额度用尽即止 | ⏭️ 无法判断 | - | - | 缺少环境变量 HYPERBOLIC_KEY |
| Nebius AI Studio | `Qwen/Qwen3-235B-A22B` | 人工登记 | 131K | 注册赠送试用额度 | 额度用尽即止 | ⏭️ 无法判断 | - | - | 缺少环境变量 NEBIUS_KEY |
| Nebius AI Studio | `meta-llama/Llama-3.3-70B-Instruct` | 人工登记 | 131K | 注册赠送试用额度 | 额度用尽即止 | ⏭️ 无法判断 | - | - | 缺少环境变量 NEBIUS_KEY |
| Novita AI | `deepseek/deepseek-v3-0324` | 人工登记 | 131K | 注册赠送试用额度 | 额度用尽即止 | ⚪ 目录中已消失 | - | - | 平台公开目录里已经找不到这个模型了 |
| Novita AI | `meta-llama/llama-3.3-70b-instruct` | 人工登记 | 131K | 注册赠送试用额度 | 额度用尽即止 | 🔵 目录已确认 | 200 | - | 公开目录中存在；未配密钥，无法验证可用性 |
| Novita AI | `bunny` | 自动发现 | 262K | 注册赠送试用额度 | 额度用尽即止 | 🔵 目录已确认 | 200 | - | 公开目录中存在；未配密钥，无法验证可用性 |
| Novita AI | `dev/glm46` | 自动发现 | 256K | 注册赠送试用额度 | 额度用尽即止 | 🔵 目录已确认 | 200 | - | 公开目录中存在；未配密钥，无法验证可用性 |
| Novita AI | `inclusionai/ling-3.0-flash-sante` | 自动发现 | 262K | 注册赠送试用额度 | 额度用尽即止 | 🔵 目录已确认 | 200 | - | 公开目录中存在；未配密钥，无法验证可用性 |
| Novita AI | `inclusionai/ling-3.1-flash` | 自动发现 | 262K | 注册赠送试用额度 | 额度用尽即止 | 🔵 目录已确认 | 200 | - | 公开目录中存在；未配密钥，无法验证可用性 |
| Chutes | `deepseek-ai/DeepSeek-V3-0324` | 人工登记 | 131K | 注册赠送少量额度 | 额度用尽即止 | ⚪ 目录中已消失 | - | - | 平台公开目录里已经找不到这个模型了 |
| Chutes | `Qwen/Qwen3-32B` | 人工登记 | 131K | 注册赠送少量额度 | 额度用尽即止 | ⚪ 目录中已消失 | - | - | 平台公开目录里已经找不到这个模型了 |
| GitHub Models | `gpt-4o-mini` | 人工登记 | 131K | 免费层按 RPM/RPD 限速 | 长期免费（限速） | ⏭️ 无法判断 | - | - | 缺少环境变量 GITHUB_MODELS_TOKEN |
| GitHub Models | `Llama-3.3-70B-Instruct` | 人工登记 | 131K | 免费层按 RPM/RPD 限速 | 长期免费（限速） | ⏭️ 无法判断 | - | - | 缺少环境变量 GITHUB_MODELS_TOKEN |
| Cloudflare Workers AI | `@cf/meta/llama-3.3-70b-instruct-fp8-fast` | 人工登记 | 24K | 每日 10000 neurons 免费额度 | 长期免费（每日重置） | ⏭️ 无法判断 | - | - | 缺少环境变量 CLOUDFLARE_API_TOKEN, CLOUDFLARE_ACCOUNT_ID |
| Cloudflare Workers AI | `@cf/meta/llama-3.1-8b-instruct` | 人工登记 | 8K | 每日 10000 neurons 免费额度 | 长期免费（每日重置） | ⏭️ 无法判断 | - | - | 缺少环境变量 CLOUDFLARE_API_TOKEN, CLOUDFLARE_ACCOUNT_ID |

## 客户端配置示例

任意支持 OpenAI 兼容协议的客户端（Cline / Cherry Studio / NextChat / One API / Roo Code …）
填上表中「正常可用」那行的 `BaseURL`、你申请的 Key 和 `模型 ID` 即可：

```json
{
  "apiProvider": "openai",
  "openAiBaseUrl": "https://api.example.com/v1",
  "openAiApiKey": "$YOUR_API_KEY",
  "openAiModelId": "model-id"
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
   之后每 4 小时会自动更新，也可以在触发时填 `only` 只检查某几个平台。

> 想降低提交频率，把 `.github/workflows/update.yml` 里的 `cron` 改成 `0 2 * * *`（每天一次）即可。

## 自动更新原理

GitHub Actions 每 4 小时启动一次云环境，运行 `update_list.py`，全程不需要服务器。
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
   几乎不消耗免费额度，按返回码判定可用性。

然后把结果写成 README / CSV / status.json，状态有变化时追加 history.jsonl，最后 commit & push。

### 产出文件

| 文件 | 用途 |
| --- | --- |
| `README.md` | 本文件，可读表格版，GitHub 直接预览 |
| `free_llm_api.csv` | 可下载表格（带 BOM，Excel 双击不乱码） |
| `status.json` | 结构化数据，供程序调用（例如自动切换代理） |
| `models.auto.json` | **脚本自己维护**的自动纳管模型池（确证免费的才进，连续失败自动剔除） |
| `history.jsonl` | 状态**变化**历史，一行一次变更快照 |

三层模型池的关系：

| 文件 | 谁写 | 作用 |
| --- | --- | --- |
| `update_list.py` 里的 `PROVIDER_POOL` | 人工 | 骨架：平台地址、申请入口、免费额度说明 |
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

也可以直接改 `update_list.py` 顶部的 `PROVIDER_POOL`，格式一目了然。

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
| 平台是 ❌ 接口已失效 | 该平台的接口路径返回 404，可能已下线或改地址，需要改 `PROVIDER_POOL` 里的 `base_url` |
| 某个模型 ⚪ 目录中已消失 | 平台目录里查不到这个 ID 了；看「相近的 ID」列，多半只是改了名 |
| 一直是 ⚠️ 限流 | 免费额度确实用完了（或账号在共享 IP 上被限速），等下个周期再看 |
| 自动纳入了奇怪的模型 | 把 `--adopt` 改成 `off` 或 `safe`，并在 `models.auto.json` 里删掉它 |
| 报 `HttpError: 403` 且没提交 | 仓库的 Workflow permissions 还是只读，参考「部署到自己的仓库」第 3 步 |
| 大量 📡 域名不通 | GitHub Runner 出口或被墙平台连通性问题，脚本会自动重试，偶发可忽略 |

## 历史更新记录（最近 10 次）

| 时间 | 可用模型 | 状态变化 |
| --- | ---: | ---: |
| 2026-09-30 19:48:18 | 0/83 | 0 |

完整记录见 `history.jsonl`。

---

## 说明与免责

- 「免费」指平台公开的免费额度 / 免费模型，各平台政策随时可能调整，请以官方控制台为准。
- `429` 只代表**此刻**限流或额度用尽，不代表模型永久失效；隔一段时间会自动恢复。
- 上下文长度、额度类型、预期有效期来自公开文档，仅作参考，不作为计费依据。
- 本仓库只做可用性探测，不代理、不分发任何模型能力，也不存储任何密钥。
