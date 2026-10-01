# 免费 LLM API 状态清单

自动巡检各大平台免费大模型接口的可用性，每 4 小时更新一次。
密钥只存放在 GitHub Secrets 中，脚本不落地、不外传，仓库里只留下状态结果。

- **最后更新**：2026-10-02 00:02:33 (北京时间 UTC+8)
- **本次耗时**：49.3 秒　|　**巡检频率**：`0 */4 * * *`
- **实测可用**：**0 / 4**（未配密钥但目录已确认存在 🔵 0 个）　|　**已配置平台**：1 / 1
- **接口探活**：1 个平台已探活（🟢 在线 1，❌ 失效 0，📡 不通 0）　|　**可读目录**：1 个平台（其中 0 个无需密钥）

> 这套清单是**自己维护自己**的：平台接口死活靠「匿名探活」（用一个无效密钥试，
> 401 说明服务活着），模型增删靠拉平台公开的 `/models` 目录，
> 能被机器确证免费的模型会自动纳入 `models.auto.json`，连续 3 轮实测失败会自动剔除。

| 状态 | 数量 | 说明 |
| --- | ---: | --- |
| ✅ 正常可用 | 0 | 用你的密钥实测返回 200 |
| 🔵 目录已确认 | 0 | 未配密钥，但平台公开目录中确认该模型存在 |
| ⚠️ 限流/额度耗尽 | 0 | 返回 429 或提示配额/余额不足 |
| 🟠 请求被拒 | 0 | 返回 400，参数或模型不被支持 |
| 🔑 密钥失效/无权限 | 4 | 返回 401/403，密钥无效或权限变更 |
| ⚪ 目录中已消失 | 0 | 公开目录里查不到它了，疑似已下架 |
| ❌ 模型已下架 | 0 | 返回 404，模型 ID 不存在 |
| 🌐 服务端异常 | 0 | 返回 5xx，平台侧故障 |
| 📡 网络超时/不可达 | 0 | 连接失败或超时 |
| ❔ 未知状态 | 0 | 其他返回码 |
| ⏭️ 无法判断 | 0 | 未配密钥，且平台目录不公开，无从判断 |

**平台级「接口探活」**（不需要任何密钥，用无效密钥试出来的）：

| 探活结果 | 平台数 | 说明 |
| --- | ---: | --- |
| 🟢 接口在线 | 1 | 鉴权层正常拒绝了无效密钥，说明服务活着、地址没变 |
| 🔓 无需密钥 | 0 | 无效密钥竟然返回 200，接口可能不校验密钥 |
| 🟠 接口异常 | 0 | 能连上，但返回 5xx / 410 等服务端错误 |
| ❌ 接口已失效 | 0 | 返回 404，路径变更或服务已下线 |
| 📡 域名不通 | 0 | 连接失败或超时 |
| ❔ 探活异常 | 0 | 返回码无法归类 |
| ⏭️ 未探活 | 0 | 缺少必要环境变量，或本次关闭了探活 |

## 本次状态变化

| 平台 | 模型 | 变化 |
| --- | --- | --- |
| 魔搭 ModelScope | `Qwen/Qwen3.8-27B` | ✅ 正常可用 → 🔑 密钥失效/无权限 |
| 魔搭 ModelScope | `deepseek-ai/DeepSeek-V4.1-Flash` | ✅ 正常可用 → 🔑 密钥失效/无权限 |
| 魔搭 ModelScope | `ZhipuAI/GLM-4.7-Flash` | ✅ 正常可用 → 🔑 密钥失效/无权限 |
| 魔搭 ModelScope | `stepfun-ai/Step-3.7-Flash` | ✅ 正常可用 → 🔑 密钥失效/无权限 |

## 平台总览

| 平台 | 接口探活 | 模型状态 | 免费性质 | 大陆可用性 | 密钥变量 | 目录 | 申请地址 |
| --- | --- | --- | --- | --- | --- | ---: | --- |
| 魔搭 ModelScope | 🟢 接口在线 | 🔑 密钥失效/无权限 0/4 | 长期免费 | 🟡 要点技巧 | `MODELSCOPE_KEY` | 35 | [控制台](https://modelscope.cn/my/myaccesstoken) |

## 免费政策与限流

这一节是**人工核实的官方数据**，不是实测值 —— 全部来自研究员实际读到的官方页面，
查不到的一律写「未公布」。核实日期见末列，来源链接在 `providers.json` 里。

| 平台 | 免费性质 | RPM | RPD | TPM | TPD | 并发 | 重置 | 闲时/忙时 | 手机号 | 实名 | 外币卡 | 置信度 | 核实日 |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- | --- | :-: | :-: | :-: | :-: | --- |
| 魔搭 ModelScope | 长期免费 | 未公布 | 未公布 | 未公布 | 未公布 | 未公布 | 未公布 | 无 | ✅ | ✅ | ? | partial | 2026-09-30 |

> 门槛列：✅ = 需要，— = 不需要，? = 官方页面未说明。
> 「未公布」不代表没有限制 —— 大部分平台的限速数字只在登录后的控制台可见。

## 中国大陆可用性

这一节回答的是「**身在墙内能不能拿到并调用它**」，数据来自官方条款与实测。
对我们来说，**地区封锁和非中国出口往往比外币卡更早成为障碍**。

| 平台 | 拿到密钥的难度 | 原因 | 封锁大陆 | 需非中国出口 | 拿免费额度要绑卡 |
| --- | --- | --- | :-: | :-: | :-: |
| 魔搭 ModelScope | 🟡 要点技巧 | 对大陆开发者来说卡点和钱、卡都无关：手机号与身份证人皆有之，难在「不是注册即用」——注册完只能拿到 Access To… | — | — | — |

## 平台打分

**打分原则：只用能确证的维度。** 缺数据的维度不计入总分，权重会自动重新归一化，
并在末列标出缺了什么 —— 我们没有用「未知」去冒充中位数。

权重：免费性质 30 / 大陆门槛 25 / 限速 20 / 上下文 15 / 模型数 10（满分 10）

| # | 平台 | 综合分 | 评价 | 免费性质 | 大陆门槛 | 限速 | 上下文 | 模型数 | 缺数据 |
| ---: | --- | ---: | --- | ---: | ---: | ---: | ---: | ---: | --- |
| 1 | 魔搭 ModelScope | **8.5** | 🟢 推荐 | 10.0 | 7.0 | — | — | 8.0 | 限速、上下文 |

> **这个分数衡量的是「白嫖的性价比」，不是模型有多聪明。**
> 「限速」和「上下文」两列出现 `—` 是因为官方没有公布数值或没登记上下文，
> 不是它们不重要 —— 只是我们拒绝用猜的数字打分。

## 自动发现

这一节的内容**全部由脚本自动产生**，不需要人工维护：

- **自动纳入**：从平台公开目录里读到、且能被机器确证免费的模型 → 自动进 `models.auto.json`
- **候选**：名字看起来免费但无法确证的 → 只列在这里，等你确认后才进池子
- **目录中消失**：我们登记了、但平台目录里已经查不到 → 大概率被下架了

> 当前自动纳入模式：**safe**（`safe` = 只收机器确证免费的；`aggressive` = 名字像的也收；`off` = 只记候选）

### 候选（未自动纳入，共 8 个）

名字看起来是免费档、但平台没给出可机器核对的定价信息，所以只列在这里。
想收进来就把对应 `id` 加到 `models.custom.json`，或者手动跑 `--adopt aggressive`。

| 平台 | 模型 | 依据 | 上下文 |
| --- | --- | --- | ---: |
| 魔搭 ModelScope | `OpenGVLab/InternVL3_5-241B-A28B` | 疑似免费 |  |
| 魔搭 ModelScope | `PaddlePaddle/ERNIE-4.5-0.3B-PT` | 疑似免费 |  |
| 魔搭 ModelScope | `PaddlePaddle/ERNIE-4.5-21B-A3B-PT` | 疑似免费 |  |
| 魔搭 ModelScope | `PaddlePaddle/ERNIE-4.5-300B-A47B-PT` | 疑似免费 |  |
| 魔搭 ModelScope | `PaddlePaddle/ERNIE-4.5-VL-28B-A3B-PT` | 疑似免费 |  |
| 魔搭 ModelScope | `Qwen/Qwen3.5-27B` | 疑似免费 |  |
| 魔搭 ModelScope | `Qwen/Qwen3.5-35B-A3B` | 疑似免费 |  |
| 魔搭 ModelScope | `Qwen/Qwen3.5-397B-A17B` | 疑似免费 |  |

## 外部清单与官方文档变更

政策数字很难自动解析，但**「页面变了」很容易检测**。这一节只做变更提醒，不做解读。

### 别家清单的变化

| 来源 | 模型数 | 本轮变化 |
| --- | ---: | --- |
| Cline 模型目录 | 463 | 无变化 |

> Cline 模型目录：Cline 用量计费通道的目录；实测与 OpenRouter 一致（464 个），用来交叉验证

### 官方文档页变更提醒

**这些页面本轮内容变了，政策可能已经调整，建议去看一眼：**

| 页面 | 变更时间 | 链接 |
| --- | --- | --- |
| Cloudflare 定价 | 2026-10-02 00:02 | [打开](https://developers.cloudflare.com/workers-ai/platform/pricing/) |

> 有 12 个页面是第一次抓取，本轮只建立基线，不算变更。
> 有 2 个页面本轮抓取失败（Kimi 限流, 阶跃星辰定价），不影响其他检测。

共监控 16 个页面，摘要存放在 `sources.json`。

## 可用性时间线（自动累积）

已累积 **13** 次巡检（2026-09-30 19:57 起）。这一节是为了回答文档回答不了的问题：**哪个平台在哪个时段容易被限流**。

| 平台 | 巡检轮次 | 实测成功累计 | 限流(429)累计 | 探活异常 | 最容易限流的时段 |
| --- | ---: | ---: | ---: | ---: | --- |
| SILICONFLOW_KEY | 11 | 11 | 19 | 0 | 20:00 前后 |
| OPENROUTER_KEY | 11 | 34 | 10 | 0 | 20:00 前后 |
| 魔搭 ModelScope | 13 | 12 | 0 | 0 | - |
| BAICHUAN_KEY | 11 | 0 | 0 | 0 | - |
| CEREBRAS_KEY | 11 | 0 | 0 | 0 | - |
| CHUTES_KEY | 2 | 0 | 0 | 0 | - |
| CLOUDFLARE_API_TOKEN | 11 | 0 | 0 | 0 | - |
| DASHSCOPE_KEY | 11 | 0 | 0 | 0 | - |
| DEEPSEEK_KEY | 2 | 0 | 0 | 0 | - |
| GEMINI_KEY | 11 | 0 | 0 | 0 | - |
| GITHUB_MODELS_TOKEN | 2 | 0 | 0 | 2 | - |
| GROQ_KEY | 11 | 0 | 0 | 0 | - |
| HUNYUAN_KEY | 11 | 0 | 0 | 0 | - |
| HYPERBOLIC_KEY | 2 | 0 | 0 | 2 | - |
| MINIMAX_KEY | 11 | 0 | 0 | 0 | - |
| MISTRAL_KEY | 11 | 0 | 0 | 0 | - |
| MOONSHOT_KEY | 11 | 0 | 0 | 0 | - |
| NEBIUS_KEY | 11 | 0 | 0 | 0 | - |
| NOVITA_KEY | 11 | 0 | 0 | 0 | - |
| NVIDIA_KEY | 11 | 0 | 0 | 2 | - |

> **没配密钥的平台，限流列会一直是 0** —— 429 只有真正调用时才会出现，
> 匿名探活看不到它。想让这一节有数据，配一个密钥就行。
> 时段按北京时间（UTC+8）统计，每 4 小时一个采样点，数据越攒越准。

## 模型明细

| 平台 | 模型 ID | 来源 | 上下文 | 状态 | HTTP | 延迟 | 备注 |
| --- | --- | --- | ---: | --- | ---: | ---: | --- |
| 魔搭 ModelScope | `Qwen/Qwen3.8-27B` | 人工登记 |  | 🔑 密钥失效/无权限 | 401 | 1067 ms | Authentication failed, please make sure that a valid ModelScope token is supplied. |
| 魔搭 ModelScope | `deepseek-ai/DeepSeek-V4.1-Flash` | 人工登记 |  | 🔑 密钥失效/无权限 | 401 | 1025 ms | Authentication failed, please make sure that a valid ModelScope token is supplied. |
| 魔搭 ModelScope | `ZhipuAI/GLM-4.7-Flash` | 人工登记 |  | 🔑 密钥失效/无权限 | 401 | 991 ms | Authentication failed, please make sure that a valid ModelScope token is supplied. |
| 魔搭 ModelScope | `stepfun-ai/Step-3.7-Flash` | 人工登记 |  | 🔑 密钥失效/无权限 | 401 | 1008 ms | Authentication failed, please make sure that a valid ModelScope token is supplied. |

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
5. **看外部清单**：拉一份别家维护的模型目录（目前是 Cline 的），和上一轮比对，
   有增删就记下来 —— 用别人的清单当传感器。
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
| 2026-10-01 23:07:31 | 16/94 | 2 |
| 2026-10-01 20:52:58 | 15/93 | 89 |
| 2026-10-01 20:48:50 | 4/4 | 4 |
| 2026-10-01 19:58:42 | 19/93 | 26 |
| 2026-10-01 18:50:58 | 3/88 | 4 |
| 2026-10-01 02:53:04 | 0/88 | 52 |
| 2026-09-30 19:48:18 | 0/83 | 0 |

完整记录见 `history.jsonl`。

---

## 说明与免责

- 「免费」指平台公开的免费额度 / 免费模型，各平台政策随时可能调整，请以官方控制台为准。
- `429` 只代表**此刻**限流或额度用尽，不代表模型永久失效；隔一段时间会自动恢复。
- 上下文长度、额度类型、预期有效期来自公开文档，仅作参考，不作为计费依据。
- 本仓库只做可用性探测，不代理、不分发任何模型能力，也不存储任何密钥。
