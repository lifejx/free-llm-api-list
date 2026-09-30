# 免费 LLM API 状态清单

自动巡检各大平台免费大模型接口的可用性，每 4 小时更新一次。
密钥只存放在 GitHub Secrets 中，脚本不落地、不外传，仓库里只留下状态结果。

- **最后更新**：2026-09-30 17:47:26 (北京时间 UTC+8)
- **本次耗时**：0.0 秒　|　**巡检频率**：`0 */4 * * *`
- **可用模型**：**0 / 62**　|　**已配置平台**：0 / 28

| 状态 | 数量 | 说明 |
| --- | ---: | --- |
| ✅ 正常可用 | 0 | 返回 200，可正常调用 |
| ⚠️ 限流/额度耗尽 | 0 | 返回 429 或提示配额/余额不足 |
| 🟠 请求被拒 | 0 | 返回 400，参数或模型不被支持 |
| 🔑 密钥失效/无权限 | 0 | 返回 401/403，密钥无效或权限变更 |
| ❌ 模型已下架 | 0 | 返回 404，模型 ID 不存在 |
| 🌐 服务端异常 | 0 | 返回 5xx，平台侧故障 |
| 📡 网络超时/不可达 | 0 | 连接失败或超时 |
| ❔ 未知状态 | 0 | 其他返回码 |
| ⏭️ 未配置密钥 | 62 | 未提供该平台密钥，本次跳过 |

## 平台总览

| 平台 | 状态 | 可用模型 | 密钥变量 | 额度类型 | 申请地址 |
| --- | --- | ---: | --- | --- | --- |
| DeepSeek 深度求索 | ⏭️ 未配置密钥 | 0/2 | `DEEPSEEK_KEY` | 注册赠送测试额度，用完后按量计费 | [控制台](https://platform.deepseek.com/api_keys) |
| 智谱 AI (BigModel) | ⏭️ 未配置密钥 | 0/3 | `ZHIPU_KEY` | Flash 系列免费，有限速 | [控制台](https://open.bigmodel.cn/usercenter/apikeys) |
| 月之暗面 Kimi | ⏭️ 未配置密钥 | 0/2 | `MOONSHOT_KEY` | 新用户赠送额度 | [控制台](https://platform.moonshot.cn/console/api-keys) |
| 阿里云百炼 DashScope | ⏭️ 未配置密钥 | 0/3 | `DASHSCOPE_KEY` | 新用户每个模型 100 万 tokens 免费额度 | [控制台](https://bailian.console.aliyun.com/) |
| 硅基流动 SiliconFlow | ⏭️ 未配置密钥 | 0/3 | `SILICONFLOW_KEY` | 部分小模型免费，有限速 | [控制台](https://cloud.siliconflow.cn/account/ak) |
| 魔搭 ModelScope | ⏭️ 未配置密钥 | 0/3 | `MODELSCOPE_KEY` | 每日 2000 次免费调用 | [控制台](https://modelscope.cn/my/myaccesstoken) |
| 腾讯混元 Hunyuan | ⏭️ 未配置密钥 | 0/2 | `HUNYUAN_KEY` | 新用户赠送免费额度 | [控制台](https://console.cloud.tencent.com/hunyuan/api-key) |
| 百度千帆 Qianfan | ⏭️ 未配置密钥 | 0/2 | `QIANFAN_KEY` | ERNIE Speed 系列免费 | [控制台](https://console.bce.baidu.com/iam/#/iam/apikey/list) |
| 火山方舟 Volcengine Ark | ⏭️ 未配置密钥 | 0/2 | `VOLC_ARK_KEY` | 新用户每个模型 50 万 tokens 免费额度 | [控制台](https://console.volcengine.com/ark) |
| 讯飞星火 Spark | ⏭️ 未配置密钥 | 0/2 | `SPARK_KEY` | Lite 版免费不限量（限速） | [控制台](https://console.xfyun.cn/services/bmx1) |
| MiniMax | ⏭️ 未配置密钥 | 0/2 | `MINIMAX_KEY` | 注册赠送额度 | [控制台](https://platform.minimaxi.com/user-center/basic-information/interface-key) |
| 阶跃星辰 StepFun | ⏭️ 未配置密钥 | 0/2 | `STEPFUN_KEY` | Flash 系列免费（限速） | [控制台](https://platform.stepfun.com/interface-key) |
| 零一万物 Yi | ⏭️ 未配置密钥 | 0/1 | `YI_KEY` | 注册赠送额度 | [控制台](https://platform.lingyiwanwu.com/apikeys) |
| 百川智能 Baichuan | ⏭️ 未配置密钥 | 0/1 | `BAICHUAN_KEY` | 新用户赠送 tokens | [控制台](https://platform.baichuan-ai.com/console/apikey) |
| OpenRouter | ⏭️ 未配置密钥 | 0/3 | `OPENROUTER_KEY` | 免费模型每日次数受限（随账户余额放宽） | [控制台](https://openrouter.ai/keys) |
| Groq | ⏭️ 未配置密钥 | 0/3 | `GROQ_KEY` | 免费层按 RPM/TPM/每日限额 | [控制台](https://console.groq.com/keys) |
| Google Gemini | ⏭️ 未配置密钥 | 0/3 | `GEMINI_KEY` | 免费层按 RPM/RPD 限速 | [控制台](https://aistudio.google.com/app/apikey) |
| Cerebras | ⏭️ 未配置密钥 | 0/3 | `CEREBRAS_KEY` | 免费层每日 100 万 tokens | [控制台](https://cloud.cerebras.ai/) |
| Mistral AI | ⏭️ 未配置密钥 | 0/2 | `MISTRAL_KEY` | Experiment 免费层（需手机验证，限速） | [控制台](https://console.mistral.ai/api-keys/) |
| Together AI | ⏭️ 未配置密钥 | 0/2 | `TOGETHER_KEY` | 新用户赠送额度 + 少量 free 模型 | [控制台](https://api.together.xyz/settings/api-keys) |
| NVIDIA NIM | ⏭️ 未配置密钥 | 0/2 | `NVIDIA_KEY` | 注册赠送 1000 credits | [控制台](https://build.nvidia.com/settings/api-keys) |
| SambaNova | ⏭️ 未配置密钥 | 0/2 | `SAMBANOVA_KEY` | 免费层限速 | [控制台](https://cloud.sambanova.ai/apis) |
| Hyperbolic | ⏭️ 未配置密钥 | 0/2 | `HYPERBOLIC_KEY` | 注册赠送约 $1 额度 | [控制台](https://app.hyperbolic.xyz/settings) |
| Nebius AI Studio | ⏭️ 未配置密钥 | 0/2 | `NEBIUS_KEY` | 注册赠送试用额度 | [控制台](https://studio.nebius.com/settings/api-keys) |
| Novita AI | ⏭️ 未配置密钥 | 0/2 | `NOVITA_KEY` | 注册赠送试用额度 | [控制台](https://novita.ai/settings/key-management) |
| Chutes | ⏭️ 未配置密钥 | 0/2 | `CHUTES_KEY` | 注册赠送少量额度 | [控制台](https://chutes.ai/app/api) |
| GitHub Models | ⏭️ 未配置密钥 | 0/2 | `GITHUB_MODELS_TOKEN` | 免费层按 RPM/RPD 限速 | [控制台](https://github.com/settings/tokens) |
| Cloudflare Workers AI | ⏭️ 未配置密钥 | 0/2 | `CLOUDFLARE_API_TOKEN` | 每日 10000 neurons 免费额度 | [控制台](https://dash.cloudflare.com/profile/api-tokens) |

## 模型明细

| 平台 | 模型 ID | 上下文 | 额度类型 | 预期有效期 | 状态 | HTTP | 延迟 | 备注 |
| --- | --- | ---: | --- | --- | --- | ---: | ---: | --- |
| DeepSeek 深度求索 | `deepseek-chat` | 128K | 注册赠送测试额度，用完后按量计费 | 额度用尽即止（非长期免费） | ⏭️ 未配置密钥 | - | - | 缺少环境变量 DEEPSEEK_KEY |
| DeepSeek 深度求索 | `deepseek-reasoner` | 128K | 注册赠送测试额度，用完后按量计费 | 额度用尽即止（非长期免费） | ⏭️ 未配置密钥 | - | - | 缺少环境变量 DEEPSEEK_KEY |
| 智谱 AI (BigModel) | `glm-4-flash` | 128K | Flash 系列免费，有限速 | 长期免费 | ⏭️ 未配置密钥 | - | - | 缺少环境变量 ZHIPU_KEY |
| 智谱 AI (BigModel) | `glm-4.5-flash` | 128K | Flash 系列免费，有限速 | 长期免费 | ⏭️ 未配置密钥 | - | - | 缺少环境变量 ZHIPU_KEY |
| 智谱 AI (BigModel) | `glm-4v-flash` | 8K | Flash 系列免费，有限速 | 长期免费 | ⏭️ 未配置密钥 | - | - | 缺少环境变量 ZHIPU_KEY |
| 月之暗面 Kimi | `kimi-k2-0905-preview` | 262K | 新用户赠送额度 | 额度用尽即止 | ⏭️ 未配置密钥 | - | - | 缺少环境变量 MOONSHOT_KEY |
| 月之暗面 Kimi | `moonshot-v1-8k` | 8K | 新用户赠送额度 | 额度用尽即止 | ⏭️ 未配置密钥 | - | - | 缺少环境变量 MOONSHOT_KEY |
| 阿里云百炼 DashScope | `qwen-turbo` | 1M | 新用户每个模型 100 万 tokens 免费额度 | 自开通起 180 天有效 | ⏭️ 未配置密钥 | - | - | 缺少环境变量 DASHSCOPE_KEY |
| 阿里云百炼 DashScope | `qwen-plus` | 131K | 新用户每个模型 100 万 tokens 免费额度 | 自开通起 180 天有效 | ⏭️ 未配置密钥 | - | - | 缺少环境变量 DASHSCOPE_KEY |
| 阿里云百炼 DashScope | `qwen-long` | 10M | 新用户每个模型 100 万 tokens 免费额度 | 自开通起 180 天有效 | ⏭️ 未配置密钥 | - | - | 缺少环境变量 DASHSCOPE_KEY |
| 硅基流动 SiliconFlow | `Qwen/Qwen3-8B` | 32K | 部分小模型免费，有限速 | 长期免费（免费名单会轮换） | ⏭️ 未配置密钥 | - | - | 缺少环境变量 SILICONFLOW_KEY |
| 硅基流动 SiliconFlow | `THUDM/glm-4-9b-chat` | 32K | 部分小模型免费，有限速 | 长期免费（免费名单会轮换） | ⏭️ 未配置密钥 | - | - | 缺少环境变量 SILICONFLOW_KEY |
| 硅基流动 SiliconFlow | `deepseek-ai/DeepSeek-R1-0528-Qwen3-8B` | 131K | 部分小模型免费，有限速 | 长期免费（免费名单会轮换） | ⏭️ 未配置密钥 | - | - | 缺少环境变量 SILICONFLOW_KEY |
| 魔搭 ModelScope | `Qwen/Qwen3-8B` | 32K | 每日 2000 次免费调用 | 长期免费 | ⏭️ 未配置密钥 | - | - | 缺少环境变量 MODELSCOPE_KEY |
| 魔搭 ModelScope | `deepseek-ai/DeepSeek-R1-Distill-Qwen-7B` | 65K | 每日 2000 次免费调用 | 长期免费 | ⏭️ 未配置密钥 | - | - | 缺少环境变量 MODELSCOPE_KEY |
| 魔搭 ModelScope | `Qwen/Qwen2.5-7B-Instruct` | 32K | 每日 2000 次免费调用 | 长期免费 | ⏭️ 未配置密钥 | - | - | 缺少环境变量 MODELSCOPE_KEY |
| 腾讯混元 Hunyuan | `hunyuan-turbos-latest` | 32K | 新用户赠送免费额度 | 额度用尽即止 | ⏭️ 未配置密钥 | - | - | 缺少环境变量 HUNYUAN_KEY |
| 腾讯混元 Hunyuan | `hunyuan-lite` | 32K | 新用户赠送免费额度 | 额度用尽即止 | ⏭️ 未配置密钥 | - | - | 缺少环境变量 HUNYUAN_KEY |
| 百度千帆 Qianfan | `ernie-speed-128k` | 131K | ERNIE Speed 系列免费 | 长期免费（限速） | ⏭️ 未配置密钥 | - | - | 缺少环境变量 QIANFAN_KEY |
| 百度千帆 Qianfan | `ernie-4.5-turbo-128k` | 131K | ERNIE Speed 系列免费 | 长期免费（限速） | ⏭️ 未配置密钥 | - | - | 缺少环境变量 QIANFAN_KEY |
| 火山方舟 Volcengine Ark | `doubao-seed-1-6-250615` | 262K | 新用户每个模型 50 万 tokens 免费额度 | 额度用尽即止 | ⏭️ 未配置密钥 | - | - | 缺少环境变量 VOLC_ARK_KEY |
| 火山方舟 Volcengine Ark | `doubao-1-5-lite-32k-250115` | 32K | 新用户每个模型 50 万 tokens 免费额度 | 额度用尽即止 | ⏭️ 未配置密钥 | - | - | 缺少环境变量 VOLC_ARK_KEY |
| 讯飞星火 Spark | `lite` | 8K | Lite 版免费不限量（限速） | 长期免费 | ⏭️ 未配置密钥 | - | - | 缺少环境变量 SPARK_KEY |
| 讯飞星火 Spark | `generalv3.5` | 8K | Lite 版免费不限量（限速） | 长期免费 | ⏭️ 未配置密钥 | - | - | 缺少环境变量 SPARK_KEY |
| MiniMax | `MiniMax-Text-01` | 1M | 注册赠送额度 | 额度用尽即止 | ⏭️ 未配置密钥 | - | - | 缺少环境变量 MINIMAX_KEY |
| MiniMax | `abab6.5s-chat` | 245K | 注册赠送额度 | 额度用尽即止 | ⏭️ 未配置密钥 | - | - | 缺少环境变量 MINIMAX_KEY |
| 阶跃星辰 StepFun | `step-1-flash` | 8K | Flash 系列免费（限速） | 长期免费 | ⏭️ 未配置密钥 | - | - | 缺少环境变量 STEPFUN_KEY |
| 阶跃星辰 StepFun | `step-2-mini` | 32K | Flash 系列免费（限速） | 长期免费 | ⏭️ 未配置密钥 | - | - | 缺少环境变量 STEPFUN_KEY |
| 零一万物 Yi | `yi-lightning` | 16K | 注册赠送额度 | 额度用尽即止 | ⏭️ 未配置密钥 | - | - | 缺少环境变量 YI_KEY |
| 百川智能 Baichuan | `Baichuan4-Turbo` | 32K | 新用户赠送 tokens | 额度用尽即止 | ⏭️ 未配置密钥 | - | - | 缺少环境变量 BAICHUAN_KEY |
| OpenRouter | `meta-llama/llama-3.3-70b-instruct:free` | 131K | 免费模型每日次数受限（随账户余额放宽） | 长期免费（:free 名单会轮换） | ⏭️ 未配置密钥 | - | - | 缺少环境变量 OPENROUTER_KEY |
| OpenRouter | `deepseek/deepseek-r1:free` | 163K | 免费模型每日次数受限（随账户余额放宽） | 长期免费（:free 名单会轮换） | ⏭️ 未配置密钥 | - | - | 缺少环境变量 OPENROUTER_KEY |
| OpenRouter | `google/gemini-2.0-flash-exp:free` | 1M | 免费模型每日次数受限（随账户余额放宽） | 长期免费（:free 名单会轮换） | ⏭️ 未配置密钥 | - | - | 缺少环境变量 OPENROUTER_KEY |
| Groq | `llama-3.3-70b-versatile` | 131K | 免费层按 RPM/TPM/每日限额 | 长期免费 | ⏭️ 未配置密钥 | - | - | 缺少环境变量 GROQ_KEY |
| Groq | `llama-3.1-8b-instant` | 131K | 免费层按 RPM/TPM/每日限额 | 长期免费 | ⏭️ 未配置密钥 | - | - | 缺少环境变量 GROQ_KEY |
| Groq | `openai/gpt-oss-120b` | 131K | 免费层按 RPM/TPM/每日限额 | 长期免费 | ⏭️ 未配置密钥 | - | - | 缺少环境变量 GROQ_KEY |
| Google Gemini | `gemini-2.5-flash` | 1M | 免费层按 RPM/RPD 限速 | 长期免费 | ⏭️ 未配置密钥 | - | - | 缺少环境变量 GEMINI_KEY |
| Google Gemini | `gemini-2.5-flash-lite` | 1M | 免费层按 RPM/RPD 限速 | 长期免费 | ⏭️ 未配置密钥 | - | - | 缺少环境变量 GEMINI_KEY |
| Google Gemini | `gemini-2.0-flash` | 1M | 免费层按 RPM/RPD 限速 | 长期免费 | ⏭️ 未配置密钥 | - | - | 缺少环境变量 GEMINI_KEY |
| Cerebras | `llama3.3-70b` | 131K | 免费层每日 100 万 tokens | 长期免费 | ⏭️ 未配置密钥 | - | - | 缺少环境变量 CEREBRAS_KEY |
| Cerebras | `qwen-3-32b` | 131K | 免费层每日 100 万 tokens | 长期免费 | ⏭️ 未配置密钥 | - | - | 缺少环境变量 CEREBRAS_KEY |
| Cerebras | `gpt-oss-120b` | 131K | 免费层每日 100 万 tokens | 长期免费 | ⏭️ 未配置密钥 | - | - | 缺少环境变量 CEREBRAS_KEY |
| Mistral AI | `mistral-small-latest` | 131K | Experiment 免费层（需手机验证，限速） | 长期免费（限速） | ⏭️ 未配置密钥 | - | - | 缺少环境变量 MISTRAL_KEY |
| Mistral AI | `open-mistral-nemo` | 131K | Experiment 免费层（需手机验证，限速） | 长期免费（限速） | ⏭️ 未配置密钥 | - | - | 缺少环境变量 MISTRAL_KEY |
| Together AI | `meta-llama/Llama-Vision-Free` | 131K | 新用户赠送额度 + 少量 free 模型 | 额度用尽即止（free 名单会轮换） | ⏭️ 未配置密钥 | - | - | 缺少环境变量 TOGETHER_KEY |
| Together AI | `deepseek-ai/DeepSeek-R1-Distill-Llama-70B-free` | 131K | 新用户赠送额度 + 少量 free 模型 | 额度用尽即止（free 名单会轮换） | ⏭️ 未配置密钥 | - | - | 缺少环境变量 TOGETHER_KEY |
| NVIDIA NIM | `deepseek-ai/deepseek-r1` | 131K | 注册赠送 1000 credits | 额度用尽即止 | ⏭️ 未配置密钥 | - | - | 缺少环境变量 NVIDIA_KEY |
| NVIDIA NIM | `meta/llama-3.3-70b-instruct` | 131K | 注册赠送 1000 credits | 额度用尽即止 | ⏭️ 未配置密钥 | - | - | 缺少环境变量 NVIDIA_KEY |
| SambaNova | `Meta-Llama-3.3-70B-Instruct` | 131K | 免费层限速 | 长期免费（限速） | ⏭️ 未配置密钥 | - | - | 缺少环境变量 SAMBANOVA_KEY |
| SambaNova | `DeepSeek-R1-Distill-Llama-70B` | 131K | 免费层限速 | 长期免费（限速） | ⏭️ 未配置密钥 | - | - | 缺少环境变量 SAMBANOVA_KEY |
| Hyperbolic | `Qwen/Qwen3-235B-A22B` | 131K | 注册赠送约 $1 额度 | 额度用尽即止 | ⏭️ 未配置密钥 | - | - | 缺少环境变量 HYPERBOLIC_KEY |
| Hyperbolic | `meta-llama/Llama-3.3-70B-Instruct` | 131K | 注册赠送约 $1 额度 | 额度用尽即止 | ⏭️ 未配置密钥 | - | - | 缺少环境变量 HYPERBOLIC_KEY |
| Nebius AI Studio | `Qwen/Qwen3-235B-A22B` | 131K | 注册赠送试用额度 | 额度用尽即止 | ⏭️ 未配置密钥 | - | - | 缺少环境变量 NEBIUS_KEY |
| Nebius AI Studio | `meta-llama/Llama-3.3-70B-Instruct` | 131K | 注册赠送试用额度 | 额度用尽即止 | ⏭️ 未配置密钥 | - | - | 缺少环境变量 NEBIUS_KEY |
| Novita AI | `deepseek/deepseek-v3-0324` | 131K | 注册赠送试用额度 | 额度用尽即止 | ⏭️ 未配置密钥 | - | - | 缺少环境变量 NOVITA_KEY |
| Novita AI | `meta-llama/llama-3.3-70b-instruct` | 131K | 注册赠送试用额度 | 额度用尽即止 | ⏭️ 未配置密钥 | - | - | 缺少环境变量 NOVITA_KEY |
| Chutes | `deepseek-ai/DeepSeek-V3-0324` | 131K | 注册赠送少量额度 | 额度用尽即止 | ⏭️ 未配置密钥 | - | - | 缺少环境变量 CHUTES_KEY |
| Chutes | `Qwen/Qwen3-32B` | 131K | 注册赠送少量额度 | 额度用尽即止 | ⏭️ 未配置密钥 | - | - | 缺少环境变量 CHUTES_KEY |
| GitHub Models | `gpt-4o-mini` | 131K | 免费层按 RPM/RPD 限速 | 长期免费（限速） | ⏭️ 未配置密钥 | - | - | 缺少环境变量 GITHUB_MODELS_TOKEN |
| GitHub Models | `Llama-3.3-70B-Instruct` | 131K | 免费层按 RPM/RPD 限速 | 长期免费（限速） | ⏭️ 未配置密钥 | - | - | 缺少环境变量 GITHUB_MODELS_TOKEN |
| Cloudflare Workers AI | `@cf/meta/llama-3.3-70b-instruct-fp8-fast` | 24K | 每日 10000 neurons 免费额度 | 长期免费（每日重置） | ⏭️ 未配置密钥 | - | - | 缺少环境变量 CLOUDFLARE_API_TOKEN, CLOUDFLARE_ACCOUNT_ID |
| Cloudflare Workers AI | `@cf/meta/llama-3.1-8b-instruct` | 8K | 每日 10000 neurons 免费额度 | 长期免费（每日重置） | ⏭️ 未配置密钥 | - | - | 缺少环境变量 CLOUDFLARE_API_TOKEN, CLOUDFLARE_ACCOUNT_ID |

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

GitHub Actions 每 4 小时启动一次云环境，运行 `update_list.py`，全程不需要服务器：

1. 读取内置免费模型池（平台 / 模型 ID / BaseURL / 上下文 / 额度类型 / 预期有效期）
2. 对每个模型发 **1 条**极短测试请求（`max_tokens=1`），几乎不消耗免费额度
3. 按返回状态码归类：`200` 可用、`429` 限流/额度耗尽、`404` 模型下架、`401/403` 密钥失效
4. 生成 `README.md`、`free_llm_api.csv`、`status.json`，状态变化时追加 `history.jsonl`
5. 自动 commit & push 回本仓库，历史全部可回溯

脚本只用 Python 标准库，**不需要 pip install**，也不需要任何第三方依赖。

### 产出文件

| 文件 | 用途 |
| --- | --- |
| `README.md` | 本文件，可读表格版，GitHub 直接预览 |
| `free_llm_api.csv` | 可下载表格（带 BOM，Excel 双击不乱码） |
| `status.json` | 结构化数据，供程序调用（例如自动切换代理） |
| `history.jsonl` | 状态**变化**历史，一行一次变更快照 |

`status.json` 每次都会因为时间戳变化而提交一次（相当于心跳，能看出定时任务有没有在跑）；
`history.jsonl` 只在状态变化时追加，所以历史记录是干净的。

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
python update_list.py                              # 检测全部已配置密钥的平台
python update_list.py --only ZHIPU_KEY,GROQ_KEY     # 只检测指定平台
python update_list.py --list                        # 只看内置模型池，不发任何请求
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
| 全部显示 ⏭️ 未配置密钥 | Secrets 名字拼错，或没在 Actions 里手动跑过；对一下上表「密钥变量」列 |
| 几百个模型全变成 🔑 | 该平台的 Secret 放错平台了，或 Key 被吊销 / 重置 |
| 一直是 ⚠️ 限流 | 免费额度确实用完了（或账号在共享 IP 上被限速），等下个周期再看 |
| 报 `HttpError: 403` 且没提交 | 仓库的 Workflow permissions 还是只读，参考「部署到自己的仓库」第 3 步 |
| 某模型一直 ❌ 已下架 | 平台下线或改名了，改 `PROVIDER_POOL` / `models.custom.json` 里的 `id` |
| 大量 📡 网络超时 | GitHub Runner 出口或被墙平台连通性问题，脚本会自动重试，偶发可忽略 |

---

## 说明与免责

- 「免费」指平台公开的免费额度 / 免费模型，各平台政策随时可能调整，请以官方控制台为准。
- `429` 只代表**此刻**限流或额度用尽，不代表模型永久失效；隔一段时间会自动恢复。
- 上下文长度、额度类型、预期有效期来自公开文档，仅作参考，不作为计费依据。
- 本仓库只做可用性探测，不代理、不分发任何模型能力，也不存储任何密钥。
