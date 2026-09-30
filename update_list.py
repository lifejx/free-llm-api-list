#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
free-llm-api-list / update_list.py

零依赖（仅用 Python 标准库）的免费 LLM API 活性检测脚本。

做三件事：
  1. 内置主流平台的免费模型清单（平台 / 模型 ID / BaseURL / 上下文 / 额度类型 / 预期有效期）
  2. 对每个模型发 1 条极短测试请求（max_tokens=1），按返回状态码判定可用性
  3. 生成 README.md、free_llm_api.csv、status.json，并在状态变化时追加 history.jsonl

状态判定：
  200        -> ok             ✅ 正常可用
  429 / 配额  -> rate_limited   ⚠️ 限流 / 额度耗尽
  404        -> not_found      ❌ 模型已下架
  401 / 403  -> auth_error     🔑 密钥失效 / 权限变更
  400        -> bad_request    🟠 请求被拒（参数或模型不被支持）
  5xx        -> server_error   🌐 服务端异常
  超时 / 连接失败 -> network_error 📡 网络超时或不可达
  未配置密钥  -> skipped        ⏭️ 未配置密钥

用法：
    python update_list.py                          # 检测全部已配置密钥的平台
    python update_list.py --only ZHIPU_KEY,GROQ_KEY  # 只检测指定平台
    python update_list.py --custom models.custom.json
    python update_list.py --list                   # 只打印内置模型池，不发请求
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import random
import re
import socket
import sys
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta, timezone
from pathlib import Path

# --------------------------------------------------------------------------- #
# 常量
# --------------------------------------------------------------------------- #

UA = "free-llm-api-list/1.0 (+https://github.com/)"
CST = timezone(timedelta(hours=8))
ROOT = Path(__file__).resolve().parent
SKIP_COMMIT_MARKER = "[skip ci]"

STATUS_META: dict[str, dict[str, str]] = {
    "ok":            {"icon": "✅", "label": "正常可用",        "desc": "返回 200，可正常调用"},
    "rate_limited":  {"icon": "⚠️", "label": "限流/额度耗尽",   "desc": "返回 429 或提示配额/余额不足"},
    "not_found":     {"icon": "❌", "label": "模型已下架",      "desc": "返回 404，模型 ID 不存在"},
    "auth_error":    {"icon": "🔑", "label": "密钥失效/无权限", "desc": "返回 401/403，密钥无效或权限变更"},
    "bad_request":   {"icon": "🟠", "label": "请求被拒",        "desc": "返回 400，参数或模型不被支持"},
    "server_error":  {"icon": "🌐", "label": "服务端异常",      "desc": "返回 5xx，平台侧故障"},
    "network_error": {"icon": "📡", "label": "网络超时/不可达", "desc": "连接失败或超时"},
    "unknown":       {"icon": "❔", "label": "未知状态",        "desc": "其他返回码"},
    "skipped":       {"icon": "⏭️", "label": "未配置密钥",      "desc": "未提供该平台密钥，本次跳过"},
}

STATUS_ORDER = ["ok", "rate_limited", "bad_request", "auth_error", "not_found",
                "server_error", "network_error", "unknown", "skipped"]

# 命中这些关键词时，即使返回 400/402/403 也判为额度问题而非密钥问题
QUOTA_HINTS = (
    "insufficient", "quota", "balance", "exceeded", "exceed", "credit",
    "rate limit", "ratelimit", "too many requests", "arrears", "billing",
    "free tier", "limit reached", "额度", "余额不足", "配额", "欠费", "超出",
)

# --------------------------------------------------------------------------- #
# 内置免费模型池
#   auth:     认证方式，bearer（默认）/ api-key / x-api-key
#   requires: 除 env 外还需要的环境变量
#   base_url: 支持 {ENV_NAME} 占位符，从环境变量取值
# --------------------------------------------------------------------------- #

PROVIDER_POOL: list[dict] = [
    {
        "name": "DeepSeek 深度求索",
        "env": "DEEPSEEK_KEY",
        "base_url": "https://api.deepseek.com/v1",
        "console": "https://platform.deepseek.com/api_keys",
        "quota": "注册赠送测试额度，用完后按量计费",
        "lifetime": "额度用尽即止（非长期免费）",
        "models": [
            {"id": "deepseek-chat", "context": 128000},
            {"id": "deepseek-reasoner", "context": 128000},
        ],
    },
    {
        "name": "智谱 AI (BigModel)",
        "env": "ZHIPU_KEY",
        "base_url": "https://open.bigmodel.cn/api/paas/v4",
        "console": "https://open.bigmodel.cn/usercenter/apikeys",
        "quota": "Flash 系列免费，有限速",
        "lifetime": "长期免费",
        "models": [
            {"id": "glm-4-flash", "context": 128000},
            {"id": "glm-4.5-flash", "context": 128000},
            {"id": "glm-4v-flash", "context": 8192, "note": "视觉模型"},
        ],
    },
    {
        "name": "月之暗面 Kimi",
        "env": "MOONSHOT_KEY",
        "base_url": "https://api.moonshot.cn/v1",
        "console": "https://platform.moonshot.cn/console/api-keys",
        "quota": "新用户赠送额度",
        "lifetime": "额度用尽即止",
        "models": [
            {"id": "kimi-k2-0905-preview", "context": 262144},
            {"id": "moonshot-v1-8k", "context": 8192},
        ],
    },
    {
        "name": "阿里云百炼 DashScope",
        "env": "DASHSCOPE_KEY",
        "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "console": "https://bailian.console.aliyun.com/",
        "quota": "新用户每个模型 100 万 tokens 免费额度",
        "lifetime": "自开通起 180 天有效",
        "models": [
            {"id": "qwen-turbo", "context": 1000000},
            {"id": "qwen-plus", "context": 131072},
            {"id": "qwen-long", "context": 10000000},
        ],
    },
    {
        "name": "硅基流动 SiliconFlow",
        "env": "SILICONFLOW_KEY",
        "base_url": "https://api.siliconflow.cn/v1",
        "console": "https://cloud.siliconflow.cn/account/ak",
        "quota": "部分小模型免费，有限速",
        "lifetime": "长期免费（免费名单会轮换）",
        "models": [
            {"id": "Qwen/Qwen3-8B", "context": 32768},
            {"id": "THUDM/glm-4-9b-chat", "context": 32768},
            {"id": "deepseek-ai/DeepSeek-R1-0528-Qwen3-8B", "context": 131072},
        ],
    },
    {
        "name": "魔搭 ModelScope",
        "env": "MODELSCOPE_KEY",
        "base_url": "https://api-inference.modelscope.cn/v1",
        "console": "https://modelscope.cn/my/myaccesstoken",
        "quota": "每日 2000 次免费调用",
        "lifetime": "长期免费",
        "models": [
            {"id": "Qwen/Qwen3-8B", "context": 32768},
            {"id": "deepseek-ai/DeepSeek-R1-Distill-Qwen-7B", "context": 65536},
            {"id": "Qwen/Qwen2.5-7B-Instruct", "context": 32768},
        ],
    },
    {
        "name": "腾讯混元 Hunyuan",
        "env": "HUNYUAN_KEY",
        "base_url": "https://api.hunyuan.cloud.tencent.com/v1",
        "console": "https://console.cloud.tencent.com/hunyuan/api-key",
        "quota": "新用户赠送免费额度",
        "lifetime": "额度用尽即止",
        "models": [
            {"id": "hunyuan-turbos-latest", "context": 32768},
            {"id": "hunyuan-lite", "context": 32768},
        ],
    },
    {
        "name": "百度千帆 Qianfan",
        "env": "QIANFAN_KEY",
        "base_url": "https://qianfan.baidubce.com/v2",
        "console": "https://console.bce.baidu.com/iam/#/iam/apikey/list",
        "quota": "ERNIE Speed 系列免费",
        "lifetime": "长期免费（限速）",
        "models": [
            {"id": "ernie-speed-128k", "context": 131072},
            {"id": "ernie-4.5-turbo-128k", "context": 131072},
        ],
    },
    {
        "name": "火山方舟 Volcengine Ark",
        "env": "VOLC_ARK_KEY",
        "base_url": "https://ark.cn-beijing.volces.com/api/v3",
        "console": "https://console.volcengine.com/ark",
        "quota": "新用户每个模型 50 万 tokens 免费额度",
        "lifetime": "额度用尽即止",
        "models": [
            {"id": "doubao-seed-1-6-250615", "context": 262144},
            {"id": "doubao-1-5-lite-32k-250115", "context": 32768},
        ],
    },
    {
        "name": "讯飞星火 Spark",
        "env": "SPARK_KEY",
        "base_url": "https://spark-api-open.xf-yun.com/v1",
        "console": "https://console.xfyun.cn/services/bmx1",
        "quota": "Lite 版免费不限量（限速）",
        "lifetime": "长期免费",
        "models": [
            {"id": "lite", "context": 8192},
            {"id": "generalv3.5", "context": 8192},
        ],
    },
    {
        "name": "MiniMax",
        "env": "MINIMAX_KEY",
        "base_url": "https://api.minimax.chat/v1",
        "console": "https://platform.minimaxi.com/user-center/basic-information/interface-key",
        "quota": "注册赠送额度",
        "lifetime": "额度用尽即止",
        "models": [
            {"id": "MiniMax-Text-01", "context": 1000000},
            {"id": "abab6.5s-chat", "context": 245760},
        ],
    },
    {
        "name": "阶跃星辰 StepFun",
        "env": "STEPFUN_KEY",
        "base_url": "https://api.stepfun.com/v1",
        "console": "https://platform.stepfun.com/interface-key",
        "quota": "Flash 系列免费（限速）",
        "lifetime": "长期免费",
        "models": [
            {"id": "step-1-flash", "context": 8192},
            {"id": "step-2-mini", "context": 32768},
        ],
    },
    {
        "name": "零一万物 Yi",
        "env": "YI_KEY",
        "base_url": "https://api.lingyiwanwu.com/v1",
        "console": "https://platform.lingyiwanwu.com/apikeys",
        "quota": "注册赠送额度",
        "lifetime": "额度用尽即止",
        "models": [
            {"id": "yi-lightning", "context": 16384},
        ],
    },
    {
        "name": "百川智能 Baichuan",
        "env": "BAICHUAN_KEY",
        "base_url": "https://api.baichuan-ai.com/v1",
        "console": "https://platform.baichuan-ai.com/console/apikey",
        "quota": "新用户赠送 tokens",
        "lifetime": "额度用尽即止",
        "models": [
            {"id": "Baichuan4-Turbo", "context": 32768},
        ],
    },
    {
        "name": "OpenRouter",
        "env": "OPENROUTER_KEY",
        "base_url": "https://openrouter.ai/api/v1",
        "console": "https://openrouter.ai/keys",
        "quota": "免费模型每日次数受限（随账户余额放宽）",
        "lifetime": "长期免费（:free 名单会轮换）",
        "models": [
            {"id": "meta-llama/llama-3.3-70b-instruct:free", "context": 131072},
            {"id": "deepseek/deepseek-r1:free", "context": 163840},
            {"id": "google/gemini-2.0-flash-exp:free", "context": 1000000},
        ],
    },
    {
        "name": "Groq",
        "env": "GROQ_KEY",
        "base_url": "https://api.groq.com/openai/v1",
        "console": "https://console.groq.com/keys",
        "quota": "免费层按 RPM/TPM/每日限额",
        "lifetime": "长期免费",
        "models": [
            {"id": "llama-3.3-70b-versatile", "context": 131072},
            {"id": "llama-3.1-8b-instant", "context": 131072},
            {"id": "openai/gpt-oss-120b", "context": 131072},
        ],
    },
    {
        "name": "Google Gemini",
        "env": "GEMINI_KEY",
        "base_url": "https://generativelanguage.googleapis.com/v1beta/openai",
        "console": "https://aistudio.google.com/app/apikey",
        "quota": "免费层按 RPM/RPD 限速",
        "lifetime": "长期免费",
        "models": [
            {"id": "gemini-2.5-flash", "context": 1048576},
            {"id": "gemini-2.5-flash-lite", "context": 1048576},
            {"id": "gemini-2.0-flash", "context": 1048576},
        ],
    },
    {
        "name": "Cerebras",
        "env": "CEREBRAS_KEY",
        "base_url": "https://api.cerebras.ai/v1",
        "console": "https://cloud.cerebras.ai/",
        "quota": "免费层每日 100 万 tokens",
        "lifetime": "长期免费",
        "models": [
            {"id": "llama3.3-70b", "context": 131072},
            {"id": "qwen-3-32b", "context": 131072},
            {"id": "gpt-oss-120b", "context": 131072},
        ],
    },
    {
        "name": "Mistral AI",
        "env": "MISTRAL_KEY",
        "base_url": "https://api.mistral.ai/v1",
        "console": "https://console.mistral.ai/api-keys/",
        "quota": "Experiment 免费层（需手机验证，限速）",
        "lifetime": "长期免费（限速）",
        "models": [
            {"id": "mistral-small-latest", "context": 131072},
            {"id": "open-mistral-nemo", "context": 131072},
        ],
    },
    {
        "name": "Together AI",
        "env": "TOGETHER_KEY",
        "base_url": "https://api.together.xyz/v1",
        "console": "https://api.together.xyz/settings/api-keys",
        "quota": "新用户赠送额度 + 少量 free 模型",
        "lifetime": "额度用尽即止（free 名单会轮换）",
        "models": [
            {"id": "meta-llama/Llama-Vision-Free", "context": 131072},
            {"id": "deepseek-ai/DeepSeek-R1-Distill-Llama-70B-free", "context": 131072},
        ],
    },
    {
        "name": "NVIDIA NIM",
        "env": "NVIDIA_KEY",
        "base_url": "https://integrate.api.nvidia.com/v1",
        "console": "https://build.nvidia.com/settings/api-keys",
        "quota": "注册赠送 1000 credits",
        "lifetime": "额度用尽即止",
        "models": [
            {"id": "deepseek-ai/deepseek-r1", "context": 131072},
            {"id": "meta/llama-3.3-70b-instruct", "context": 131072},
        ],
    },
    {
        "name": "SambaNova",
        "env": "SAMBANOVA_KEY",
        "base_url": "https://api.sambanova.ai/v1",
        "console": "https://cloud.sambanova.ai/apis",
        "quota": "免费层限速",
        "lifetime": "长期免费（限速）",
        "models": [
            {"id": "Meta-Llama-3.3-70B-Instruct", "context": 131072},
            {"id": "DeepSeek-R1-Distill-Llama-70B", "context": 131072},
        ],
    },
    {
        "name": "Hyperbolic",
        "env": "HYPERBOLIC_KEY",
        "base_url": "https://api.hyperbolic.xyz/v1",
        "console": "https://app.hyperbolic.xyz/settings",
        "quota": "注册赠送约 $1 额度",
        "lifetime": "额度用尽即止",
        "models": [
            {"id": "Qwen/Qwen3-235B-A22B", "context": 131072},
            {"id": "meta-llama/Llama-3.3-70B-Instruct", "context": 131072},
        ],
    },
    {
        "name": "Nebius AI Studio",
        "env": "NEBIUS_KEY",
        "base_url": "https://api.studio.nebius.com/v1",
        "console": "https://studio.nebius.com/settings/api-keys",
        "quota": "注册赠送试用额度",
        "lifetime": "额度用尽即止",
        "models": [
            {"id": "Qwen/Qwen3-235B-A22B", "context": 131072},
            {"id": "meta-llama/Llama-3.3-70B-Instruct", "context": 131072},
        ],
    },
    {
        "name": "Novita AI",
        "env": "NOVITA_KEY",
        "base_url": "https://api.novita.ai/v3/openai",
        "console": "https://novita.ai/settings/key-management",
        "quota": "注册赠送试用额度",
        "lifetime": "额度用尽即止",
        "models": [
            {"id": "deepseek/deepseek-v3-0324", "context": 131072},
            {"id": "meta-llama/llama-3.3-70b-instruct", "context": 131072},
        ],
    },
    {
        "name": "Chutes",
        "env": "CHUTES_KEY",
        "base_url": "https://llm.chutes.ai/v1",
        "console": "https://chutes.ai/app/api",
        "quota": "注册赠送少量额度",
        "lifetime": "额度用尽即止",
        "models": [
            {"id": "deepseek-ai/DeepSeek-V3-0324", "context": 131072},
            {"id": "Qwen/Qwen3-32B", "context": 131072},
        ],
    },
    {
        "name": "GitHub Models",
        "env": "GITHUB_MODELS_TOKEN",
        "base_url": "https://models.inference.ai.azure.com",
        "console": "https://github.com/settings/tokens",
        "quota": "免费层按 RPM/RPD 限速",
        "lifetime": "长期免费（限速）",
        "models": [
            {"id": "gpt-4o-mini", "context": 131072},
            {"id": "Llama-3.3-70B-Instruct", "context": 131072},
        ],
    },
    {
        "name": "Cloudflare Workers AI",
        "env": "CLOUDFLARE_API_TOKEN",
        "requires": ["CLOUDFLARE_ACCOUNT_ID"],
        "base_url": "https://api.cloudflare.com/client/v4/accounts/{CLOUDFLARE_ACCOUNT_ID}/ai/v1",
        "console": "https://dash.cloudflare.com/profile/api-tokens",
        "quota": "每日 10000 neurons 免费额度",
        "lifetime": "长期免费（每日重置）",
        "models": [
            {"id": "@cf/meta/llama-3.3-70b-instruct-fp8-fast", "context": 24000},
            {"id": "@cf/meta/llama-3.1-8b-instruct", "context": 8000},
        ],
    },
]


# --------------------------------------------------------------------------- #
# 工具函数
# --------------------------------------------------------------------------- #

def log(msg: str) -> None:
    print(msg, flush=True)


def shorten(text: object, limit: int = 180) -> str:
    s = re.sub(r"\s+", " ", str(text or "")).strip()
    return s if len(s) <= limit else s[: limit - 1] + "…"


def fmt_context(value: object) -> str:
    if isinstance(value, str):
        return value
    try:
        n = int(value)
    except (TypeError, ValueError):
        return "-"
    if n >= 1_000_000:
        millions = n / 1_000_000
        if abs(millions - round(millions)) < 0.05:
            return f"{round(millions)}M"
        return f"{millions:.3g}M"
    if n >= 1000:
        return f"{n // 1000}K"
    return str(n)


def fmt_ms(ms: object) -> str:
    try:
        return f"{int(ms)} ms"
    except (TypeError, ValueError):
        return "-"


def expand_env(text: str) -> str:
    """把 {ENV_NAME} 占位符替换为环境变量值。"""
    return re.sub(r"\{([A-Z0-9_]+)\}", lambda m: os.environ.get(m.group(1), "").strip(), text)


def extract_message(body: str) -> str:
    """从响应体里尽量抽出一句人话的错误信息。"""
    body = (body or "").strip()
    if not body:
        return ""
    try:
        data = json.loads(body)
    except (ValueError, TypeError):
        return shorten(body)
    if not isinstance(data, dict):
        return shorten(body)

    candidates: list[object] = []
    err = data.get("error")
    if isinstance(err, dict):
        candidates += [err.get("message"), err.get("code"), err.get("type")]
    elif isinstance(err, str):
        candidates.append(err)
    candidates.append(data.get("error_msg"))
    for key in ("message", "msg", "detail", "reason"):
        value = data.get(key)
        if isinstance(value, (str, int, float)):
            candidates.append(value)
        elif isinstance(value, dict):
            candidates += [value.get("message"), value.get("status_msg"), value.get("status_code")]
    base_resp = data.get("base_resp")
    if isinstance(base_resp, dict):
        candidates += [base_resp.get("status_msg"), base_resp.get("status_code")]
    for key in ("code", "status"):
        if key in data and isinstance(data[key], (str, int)):
            candidates.append(data[key])

    for item in candidates:
        if item not in (None, "", 0, "0"):
            return shorten(item)
    return ""


def has_quota_hint(text: str) -> bool:
    low = (text or "").lower()
    return any(hint in low for hint in QUOTA_HINTS)


def classify(code: int, body: str) -> str:
    if code == 200:
        return "ok"
    if code == 429:
        return "rate_limited"
    if code == 404:
        return "not_found"
    if code in (401, 403):
        return "rate_limited" if has_quota_hint(body) else "auth_error"
    if 500 <= code < 600:
        return "server_error"
    if code in (400, 402, 406, 422):
        return "rate_limited" if has_quota_hint(body) else "bad_request"
    return "unknown"


def aggregate_status(statuses: list[str]) -> str:
    """把一个平台下多个模型的状态汇总成一个平台状态。"""
    for status in STATUS_ORDER:
        if status in statuses:
            return status
    return "unknown"


# --------------------------------------------------------------------------- #
# 检测
# --------------------------------------------------------------------------- #

def probe(base_url: str, model: dict, key: str, provider: dict, timeout: float,
          retries: int) -> dict:
    """对单个模型发一条极短请求，返回检测结果字典。"""
    url = base_url.rstrip("/") + "/chat/completions"
    token_field = model.get("max_tokens_field", "max_tokens")
    payload = {
        "model": model["id"],
        "messages": [{"role": "user", "content": "ping"}],
        "temperature": 0,
        "stream": False,
        token_field: 1,
    }
    data = json.dumps(payload).encode("utf-8")

    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "User-Agent": UA,
    }
    auth = provider.get("auth", "bearer")
    if auth == "api-key":
        headers["api-key"] = key
    elif auth == "x-api-key":
        headers["x-api-key"] = key
    else:
        headers["Authorization"] = f"Bearer {key}"
    headers.update(provider.get("headers", {}))

    attempt = 0
    last_error = ""
    started = time.perf_counter()

    while True:
        attempt += 1
        request = urllib.request.Request(url, data=data, headers=headers, method="POST")
        try:
            with urllib.request.urlopen(request, timeout=timeout) as resp:
                body = resp.read(4096).decode("utf-8", "replace")
                elapsed = int((time.perf_counter() - started) * 1000)
                status = classify(resp.status, body)
                return {
                    "status": status, "http": resp.status, "latency_ms": elapsed,
                    "note": "" if status == "ok" else extract_message(body),
                }
        except urllib.error.HTTPError as exc:
            body = ""
            try:
                body = exc.read(4096).decode("utf-8", "replace")
            except Exception:  # noqa: BLE001 - 读取失败不影响状态判定
                body = ""
            elapsed = int((time.perf_counter() - started) * 1000)
            status = classify(exc.code, body)
            note = extract_message(body) or str(exc.reason or "")
            if exc.code == 429:
                retry_after = exc.headers.get("Retry-After") if exc.headers else None
                if retry_after:
                    note = f"{note}（Retry-After: {retry_after}）".strip("（）")
            if status == "server_error" and attempt <= retries:
                time.sleep(min(2 ** attempt, 5) + random.uniform(0, 0.5))
                continue
            return {"status": status, "http": exc.code, "latency_ms": elapsed,
                    "note": shorten(note)}
        except (urllib.error.URLError, socket.timeout, TimeoutError, ConnectionError, OSError) as exc:
            last_error = f"{type(exc).__name__}: {exc}"
            if attempt <= retries:
                time.sleep(min(2 ** attempt, 5) + random.uniform(0, 0.5))
                continue
            elapsed = int((time.perf_counter() - started) * 1000)
            status = "network_error"
            if "timed out" in last_error.lower() or isinstance(exc, (socket.timeout, TimeoutError)):
                status = "network_error"
            return {"status": status, "http": None, "latency_ms": elapsed,
                    "note": shorten(last_error)}


def build_providers(custom_path: Path | None, only: list[str]) -> list[dict]:
    """内置模型池 + 自定义模型池合并，并按 --only 过滤。"""
    providers: list[dict] = json.loads(json.dumps(PROVIDER_POOL, ensure_ascii=False))

    if custom_path:
        if not custom_path.exists():
            raise SystemExit(f"自定义模型池不存在：{custom_path}")
        raw = json.loads(custom_path.read_text(encoding="utf-8"))
        entries = raw.get("providers", []) if isinstance(raw, dict) else raw
        index = {p["env"]: p for p in providers}
        for entry in entries:
            env = entry.get("env")
            if not env:
                log(f"[warn] 自定义条目缺少 env，已忽略：{shorten(entry, 80)}")
                continue
            target = index.get(env)
            if target is None:
                providers.append(entry)
                index[env] = entry
                continue
            merged = {m["id"]: m for m in target.get("models", [])}
            for model in entry.get("models", []):
                merged[model["id"]] = {**merged.get(model["id"], {}), **model}
            target["models"] = list(merged.values())
            for key, value in entry.items():
                if key != "models":
                    target[key] = value

    if only:
        wanted = {name.upper() for name in only}
        providers = [p for p in providers if p["env"].upper() in wanted]
        if not providers:
            raise SystemExit(f"--only 未匹配到任何平台：{', '.join(sorted(wanted))}")
    return providers


def check_providers(providers: list[dict], timeout: float, retries: int, workers: int,
                    checked_at: str) -> list[dict]:
    """逐平台检测，返回结构化结果。"""
    results: list[dict] = []
    tasks: list[tuple[dict, dict, str, str]] = []

    for provider in providers:
        key_env = provider["env"]
        key = os.environ.get(key_env, "").strip()
        template_vars = sorted(set(re.findall(r"\{([A-Z0-9_]+)\}", provider.get("base_url", ""))))
        needed = list(dict.fromkeys([key_env, *provider.get("requires", []), *template_vars]))
        missing = [name for name in needed if not os.environ.get(name, "").strip()]

        base_url = expand_env(provider.get("base_url", ""))
        entry = {
            "name": provider["name"],
            "env": key_env,
            "requires": provider.get("requires", []),
            "base_url": base_url or provider.get("base_url", ""),
            "console": provider.get("console", ""),
            "quota": provider.get("quota", ""),
            "lifetime": provider.get("lifetime", ""),
            "has_key": not missing,
            "missing_env": missing,
            "models": [],
        }

        for model in provider["models"]:
            item = {
                "id": model["id"],
                "context": model.get("context", provider.get("context", "")),
                "quota": model.get("quota", provider.get("quota", "")),
                "lifetime": model.get("lifetime", provider.get("lifetime", "")),
                "note": model.get("note", ""),
                "checked_at": checked_at,
            }
            if missing:
                item.update({"status": "skipped", "http": None, "latency_ms": None,
                             "note": f"缺少环境变量 {', '.join(missing)}"})
                entry["models"].append(item)
            else:
                entry["models"].append(item)
                tasks.append((entry, item, base_url, key))

        results.append(entry)

    if tasks:
        log(f"开始检测 {len(tasks)} 个模型（并发 {workers}，超时 {timeout:g}s，重试 {retries} 次）…")
        with ThreadPoolExecutor(max_workers=max(1, workers)) as pool:
            futures = {
                pool.submit(probe, base_url, {"id": item["id"]}, key, entry, timeout, retries): (entry, item)
                for entry, item, base_url, key in tasks
            }
            for future in as_completed(futures):
                entry, item = futures[future]
                try:
                    outcome = future.result()
                except Exception as exc:  # noqa: BLE001 - 单点失败不影响整体
                    outcome = {"status": "unknown", "http": None, "latency_ms": None,
                               "note": f"{type(exc).__name__}: {exc}"}
                item.update(outcome)
                meta = STATUS_META.get(item["status"], STATUS_META["unknown"])
                log(f"  {meta['icon']} [{entry['name']}] {item['id']} "
                    f"-> {item['status']} (HTTP {item.get('http')})")

    for entry in results:
        statuses = [m["status"] for m in entry["models"]]
        entry["status"] = aggregate_status(statuses)
        entry["available"] = sum(1 for s in statuses if s == "ok")
        entry["total"] = len(statuses)
    return results


# --------------------------------------------------------------------------- #
# 输出：status.json / csv / README.md / history.jsonl
# --------------------------------------------------------------------------- #

def summarize(providers: list[dict]) -> dict:
    counts = {status: 0 for status in STATUS_META}
    for provider in providers:
        for model in provider["models"]:
            counts[model["status"]] = counts.get(model["status"], 0) + 1
    counts["providers_total"] = len(providers)
    counts["providers_configured"] = sum(1 for p in providers if p["has_key"])
    counts["providers_available"] = sum(1 for p in providers if p["status"] == "ok")
    counts["models_total"] = sum(len(p["models"]) for p in providers)
    counts["models_available"] = counts.get("ok", 0)
    return counts


def diff_status(previous: dict | None, providers: list[dict]) -> list[dict]:
    """对比上一次 status.json，找出状态变化。"""
    if not previous:
        return []
    old: dict[tuple[str, str], str] = {}
    for provider in previous.get("providers", []):
        for model in provider.get("models", []):
            old[(provider.get("env", provider.get("name", "")), model.get("id", ""))] = model.get("status", "")
    changes = []
    for provider in providers:
        for model in provider["models"]:
            key = (provider["env"], model["id"])
            was = old.get(key)
            now = model["status"]
            if was != now:
                changes.append({"provider": provider["name"], "env": provider["env"],
                                "model": model["id"], "from": was or "new", "to": now})
    return changes


def read_json(path: Path) -> dict | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def write_text_lf(path: Path, text: str, encoding: str = "utf-8") -> None:
    """强制 LF 写入：Windows 本地跑和 Linux Actions 跑产出才会字节一致，避免换行符来回抖动。"""
    with path.open("w", encoding=encoding, newline="\n") as fh:
        fh.write(text)


def write_json(path: Path, data: object) -> None:
    write_text_lf(path, json.dumps(data, ensure_ascii=False, indent=2) + "\n")


def write_csv(path: Path, providers: list[dict]) -> None:
    # utf-8-sig：让 Excel 双击打开不乱码；lineterminator 用 \n 保持跨平台一致
    with path.open("w", newline="", encoding="utf-8-sig") as fh:
        writer = csv.writer(fh, lineterminator="\n")
        writer.writerow(["平台", "密钥变量名", "模型ID", "BaseURL", "上下文", "额度类型",
                         "预期有效期", "状态", "状态码", "延迟(ms)", "备注", "检测时间"])
        for provider in providers:
            for model in provider["models"]:
                meta = STATUS_META.get(model["status"], STATUS_META["unknown"])
                writer.writerow([
                    provider["name"], provider["env"], model["id"], provider["base_url"],
                    fmt_context(model.get("context")), model.get("quota", ""),
                    model.get("lifetime", ""), f"{meta['icon']} {meta['label']}",
                    model.get("http") if model.get("http") is not None else "-",
                    model.get("latency_ms") if model.get("latency_ms") is not None else "-",
                    model.get("note", ""), model.get("checked_at", ""),
                ])


def append_history(path: Path, snapshot: dict, keep: int = 500) -> None:
    lines = []
    if path.exists():
        lines = [ln for ln in path.read_text(encoding="utf-8").splitlines() if ln.strip()]
    lines.append(json.dumps(snapshot, ensure_ascii=False, separators=(",", ":")))
    write_text_lf(path, "\n".join(lines[-keep:]) + "\n")


def status_cell(status: str) -> str:
    meta = STATUS_META.get(status, STATUS_META["unknown"])
    return f"{meta['icon']} {meta['label']}"


def render_readme(providers: list[dict], summary: dict, changes: list[dict],
                  generated_at: datetime, elapsed: float, cron: str, history: list[dict]) -> str:
    ok_providers = [p for p in providers if p["status"] == "ok"]
    first_base = ok_providers[0]["base_url"] if ok_providers else "https://api.example.com/v1"
    first_model = ok_providers[0]["models"][0]["id"] if ok_providers else "model-id"
    first_env = ok_providers[0]["env"] if ok_providers else "YOUR_API_KEY"

    sample_config = {
        "apiProvider": "openai",
        "openAiBaseUrl": first_base,
        "openAiApiKey": f"${first_env}",
        "openAiModelId": first_model,
    }

    out: list[str] = []
    add = out.append

    add("# 免费 LLM API 状态清单")
    add("")
    add("自动巡检各大平台免费大模型接口的可用性，每 4 小时更新一次。")
    add("密钥只存放在 GitHub Secrets 中，脚本不落地、不外传，仓库里只留下状态结果。")
    add("")
    add(f"- **最后更新**：{generated_at.strftime('%Y-%m-%d %H:%M:%S')} (北京时间 UTC+8)")
    add(f"- **本次耗时**：{elapsed:.1f} 秒　|　**巡检频率**：`{cron}`")
    add(f"- **可用模型**：**{summary.get('ok', 0)} / {summary.get('models_total', 0)}**"
        f"　|　**已配置平台**：{summary.get('providers_configured', 0)} / {summary.get('providers_total', 0)}")
    add("")
    add("| 状态 | 数量 | 说明 |")
    add("| --- | ---: | --- |")
    for status in STATUS_ORDER:
        meta = STATUS_META[status]
        add(f"| {meta['icon']} {meta['label']} | {summary.get(status, 0)} | {meta['desc']} |")
    add("")

    if changes:
        add("## 本次状态变化")
        add("")
        add("| 平台 | 模型 | 变化 |")
        add("| --- | --- | --- |")
        for change in changes[:60]:
            old = STATUS_META.get(change["from"], {}).get("icon", "") + " " + \
                STATUS_META.get(change["from"], {}).get("label", change["from"])
            new = STATUS_META.get(change["to"], {}).get("icon", "") + " " + \
                STATUS_META.get(change["to"], {}).get("label", change["to"])
            add(f"| {change['provider']} | `{change['model']}` | {old.strip()} → {new.strip()} |")
        add("")

    add("## 平台总览")
    add("")
    add("| 平台 | 状态 | 可用模型 | 密钥变量 | 额度类型 | 申请地址 |")
    add("| --- | --- | ---: | --- | --- | --- |")
    for provider in providers:
        console = f"[控制台]({provider['console']})" if provider["console"] else "-"
        add(f"| {provider['name']} | {status_cell(provider['status'])} | "
            f"{provider['available']}/{provider['total']} | `{provider['env']}` | "
            f"{provider.get('quota', '')} | {console} |")
    add("")

    add("## 模型明细")
    add("")
    add("| 平台 | 模型 ID | 上下文 | 额度类型 | 预期有效期 | 状态 | HTTP | 延迟 | 备注 |")
    add("| --- | --- | ---: | --- | --- | --- | ---: | ---: | --- |")
    for provider in providers:
        for model in provider["models"]:
            note = model.get("note", "") or ""
            note = note.replace("|", "\\|")
            add(f"| {provider['name']} | `{model['id']}` | {fmt_context(model.get('context'))} | "
                f"{model.get('quota', '')} | {model.get('lifetime', '')} | "
                f"{status_cell(model['status'])} | "
                f"{model.get('http') if model.get('http') is not None else '-'} | "
                f"{fmt_ms(model.get('latency_ms')) if model.get('latency_ms') is not None else '-'} | "
                f"{note} |")
    add("")

    add("## 客户端配置示例")
    add("")
    add("任意支持 OpenAI 兼容协议的客户端（Cline / Cherry Studio / NextChat / One API / Roo Code …）")
    add("填上表中「正常可用」那行的 `BaseURL`、你申请的 Key 和 `模型 ID` 即可：")
    add("")
    add("```json")
    add(json.dumps(sample_config, ensure_ascii=False, indent=2))
    add("```")
    add("")
    add("> Cline 里对应字段：API Provider 选 `OpenAI Compatible`，Base URL 填上表的 BaseURL，")
    add("> API Key 填你的密钥，Model ID 填模型 ID。")
    add("")

    add("## 部署到自己的仓库（5 分钟）")
    add("")
    add("1. **新建仓库**：GitHub 上新建一个仓库（公开私有都可以），把本目录的文件推上去：")
    add("")
    add("   ```bash")
    add("   git init && git add . && git commit -m \"init: 免费 LLM API 状态清单\"")
    add("   git branch -M main")
    add("   git remote add origin https://github.com/<你的用户名>/free-llm-api-list.git")
    add("   git push -u origin main")
    add("   ```")
    add("")
    add("2. **加密钥**：仓库 **Settings → Secrets and variables → Actions → New repository secret**，")
    add("   Name 填上表里的「密钥变量」（如 `ZHIPU_KEY`），Secret 填平台控制台申请的 Key。")
    add("   只加你实际有的平台即可。")
    add("3. **确认写权限**：**Settings → Actions → General → Workflow permissions** 选")
    add("   *Read and write permissions*（工作流里已经声明 `permissions: contents: write`，")
    add("   但如果这一步被组织策略限制，push 会失败）。")
    add("4. **手动跑一次**：**Actions → 更新免费 LLM API 状态 → Run workflow**，")
    add("   之后每 4 小时会自动更新，也可以在触发时填 `only` 只检查某几个平台。")
    add("")
    add("> 想降低提交频率，把 `.github/workflows/update.yml` 里的 `cron` 改成 `0 2 * * *`（每天一次）即可。")
    add("")
    add("## 自动更新原理")
    add("")
    add("GitHub Actions 每 4 小时启动一次云环境，运行 `update_list.py`，全程不需要服务器：")
    add("")
    add("1. 读取内置免费模型池（平台 / 模型 ID / BaseURL / 上下文 / 额度类型 / 预期有效期）")
    add("2. 对每个模型发 **1 条**极短测试请求（`max_tokens=1`），几乎不消耗免费额度")
    add("3. 按返回状态码归类：`200` 可用、`429` 限流/额度耗尽、`404` 模型下架、`401/403` 密钥失效")
    add("4. 生成 `README.md`、`free_llm_api.csv`、`status.json`，状态变化时追加 `history.jsonl`")
    add("5. 自动 commit & push 回本仓库，历史全部可回溯")
    add("")
    add("脚本只用 Python 标准库，**不需要 pip install**，也不需要任何第三方依赖。")
    add("")
    add("### 产出文件")
    add("")
    add("| 文件 | 用途 |")
    add("| --- | --- |")
    add("| `README.md` | 本文件，可读表格版，GitHub 直接预览 |")
    add("| `free_llm_api.csv` | 可下载表格（带 BOM，Excel 双击不乱码） |")
    add("| `status.json` | 结构化数据，供程序调用（例如自动切换代理） |")
    add("| `history.jsonl` | 状态**变化**历史，一行一次变更快照 |")
    add("")
    add("`status.json` 每次都会因为时间戳变化而提交一次（相当于心跳，能看出定时任务有没有在跑）；")
    add("`history.jsonl` 只在状态变化时追加，所以历史记录是干净的。")
    add("")

    add("## 如何添加 / 更换密钥")
    add("")
    add("1. 打开仓库 **Settings → Secrets and variables → Actions → New repository secret**")
    add("2. Name 填上表里的「密钥变量」（如 `ZHIPU_KEY`），Secret 填平台控制台申请的 Key")
    add("3. 到 **Actions → 更新免费 LLM API 状态 → Run workflow** 手动跑一次，或等下一次定时任务")
    add("")
    add("没配密钥的平台会显示 ⏭️ 未配置密钥，不影响其他平台检测；换 Key 直接编辑同名 Secret 即可。")
    add("")
    add("### 想增删模型")
    add("")
    add("复制 `models.custom.example.json` 为 `models.custom.json` 后修改并提交，工作流会自动带上：")
    add("")
    add("- 同 `env` 的条目：覆盖该平台字段，`models` 按 `id` 追加或合并")
    add("- 新 `env` 的条目：作为新平台追加")
    add("")
    add("也可以直接改 `update_list.py` 顶部的 `PROVIDER_POOL`，格式一目了然。")
    add("")
    add("### 本地运行")
    add("")
    add("```bash")
    add("python update_list.py                              # 检测全部已配置密钥的平台")
    add("python update_list.py --only ZHIPU_KEY,GROQ_KEY     # 只检测指定平台")
    add("python update_list.py --list                        # 只看内置模型池，不发任何请求")
    add("python update_list.py --custom models.custom.json   # 带上自定义模型池")
    add("```")
    add("")
    add("环境变量就是上表的密钥变量名，本地可以临时设：")
    add("")
    add("```bash")
    add("ZHIPU_KEY=xxxx python update_list.py --only ZHIPU_KEY     # Linux / macOS")
    add("$env:ZHIPU_KEY=\"xxxx\"; python update_list.py --only ZHIPU_KEY  # Windows PowerShell")
    add("```")
    add("")

    add("## 常见问题")
    add("")
    add("| 现象 | 原因与处理 |")
    add("| --- | --- |")
    add("| 全部显示 ⏭️ 未配置密钥 | Secrets 名字拼错，或没在 Actions 里手动跑过；对一下上表「密钥变量」列 |")
    add("| 几百个模型全变成 🔑 | 该平台的 Secret 放错平台了，或 Key 被吊销 / 重置 |")
    add("| 一直是 ⚠️ 限流 | 免费额度确实用完了（或账号在共享 IP 上被限速），等下个周期再看 |")
    add("| 报 `HttpError: 403` 且没提交 | 仓库的 Workflow permissions 还是只读，参考「部署到自己的仓库」第 3 步 |")
    add("| 某模型一直 ❌ 已下架 | 平台下线或改名了，改 `PROVIDER_POOL` / `models.custom.json` 里的 `id` |")
    add("| 大量 📡 网络超时 | GitHub Runner 出口或被墙平台连通性问题，脚本会自动重试，偶发可忽略 |")
    add("")

    if history:
        add("## 历史更新记录（最近 10 次）")
        add("")
        add("| 时间 | 可用模型 | 状态变化 |")
        add("| --- | ---: | ---: |")
        for item in history[-10:][::-1]:
            add(f"| {item.get('at', '')} | {item.get('ok', 0)}/{item.get('total', 0)} | "
                f"{len(item.get('changes', []))} |")
        add("")
        add("完整记录见 `history.jsonl`。")
        add("")

    add("---")
    add("")
    add("## 说明与免责")
    add("")
    add("- 「免费」指平台公开的免费额度 / 免费模型，各平台政策随时可能调整，请以官方控制台为准。")
    add("- `429` 只代表**此刻**限流或额度用尽，不代表模型永久失效；隔一段时间会自动恢复。")
    add("- 上下文长度、额度类型、预期有效期来自公开文档，仅作参考，不作为计费依据。")
    add("- 本仓库只做可用性探测，不代理、不分发任何模型能力，也不存储任何密钥。")
    add("")
    return "\n".join(out)


# --------------------------------------------------------------------------- #
# 主流程
# --------------------------------------------------------------------------- #

def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="检测免费 LLM API 可用性并生成 README.md / CSV / status.json")
    parser.add_argument("--only", default="",
                        help="只检测指定平台，逗号分隔的密钥变量名，例如 ZHIPU_KEY,GROQ_KEY")
    parser.add_argument("--custom", default="models.custom.json",
                        help="自定义模型池文件（默认 models.custom.json，不存在则忽略）")
    parser.add_argument("--timeout", type=float, default=30.0, help="单次请求超时秒数，默认 30")
    parser.add_argument("--retries", type=int, default=2, help="网络错误/5xx 重试次数，默认 2")
    parser.add_argument("--workers", type=int, default=6, help="并发数，默认 6")
    parser.add_argument("--out-dir", default=".", help="输出目录，默认脚本所在目录")
    parser.add_argument("--cron", default="0 */4 * * *", help="写入 README 的巡检频率展示值")
    parser.add_argument("--list", action="store_true", help="只打印内置模型池，不发请求")
    parser.add_argument("--no-history", action="store_true", help="不写入 history.jsonl")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)

    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        except (ValueError, OSError):
            pass

    out_dir = Path(args.out_dir)
    if not out_dir.is_absolute():
        out_dir = ROOT / out_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    custom_path = None
    if args.custom:
        custom_path = Path(args.custom)
        if not custom_path.is_absolute():
            custom_path = ROOT / custom_path
        if not custom_path.exists():
            custom_path = None

    only = [name.strip() for name in args.only.split(",") if name.strip()]
    providers = build_providers(custom_path, only)

    if args.list:
        total = 0
        for provider in providers:
            log(f"{provider['name']}  [{provider['env']}]  {provider['base_url']}")
            for model in provider["models"]:
                total += 1
                log(f"    - {model['id']}  ({fmt_context(model.get('context'))})")
        log(f"\n共 {len(providers)} 个平台 / {total} 个模型")
        return 0

    readme_path = out_dir / "README.md"
    csv_path = out_dir / "free_llm_api.csv"
    json_path = out_dir / "status.json"
    history_path = out_dir / "history.jsonl"

    previous = read_json(json_path)
    started = time.perf_counter()
    generated_at = datetime.now(CST)
    checked_at = generated_at.strftime("%Y-%m-%d %H:%M:%S")

    results = check_providers(providers, args.timeout, args.retries, args.workers, checked_at)
    elapsed = time.perf_counter() - started

    summary = summarize(results)
    changes = diff_status(previous, results)
    if previous is None:
        log("未找到上一次的 status.json，本次作为基线，不记录变化。")
    elif changes:
        log(f"检测到 {len(changes)} 处状态变化。")
    else:
        log("状态与上次一致，无变化。")

    history: list[dict] = []
    if history_path.exists():
        for line in history_path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                try:
                    history.append(json.loads(line))
                except ValueError:
                    continue

    payload = {
        "generated_at": generated_at.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "generated_at_cst": checked_at,
        "elapsed_seconds": round(elapsed, 2),
        "cron": args.cron,
        "summary": summary,
        "changes": changes,
        "providers": [
            {
                "name": p["name"], "env": p["env"], "base_url": p["base_url"],
                "console": p["console"], "quota": p["quota"], "lifetime": p["lifetime"],
                "has_key": p["has_key"], "missing_env": p["missing_env"],
                "status": p["status"], "available": p["available"], "total": p["total"],
                "models": p["models"],
            }
            for p in results
        ],
    }

    readme = render_readme(results, summary, changes, generated_at, elapsed,
                           args.cron, history)
    write_text_lf(readme_path, readme)
    write_csv(csv_path, results)
    write_json(json_path, payload)

    if not args.no_history:
        if not history_path.exists():
            write_text_lf(history_path, "")
        if changes or previous is None:
            append_history(history_path, {
                "at": checked_at,
                "ok": summary.get("ok", 0),
                "total": summary.get("models_total", 0),
                "changes": changes,
            })

    log("")
    log(f"✅ 可用 {summary.get('ok', 0)} / {summary.get('models_total', 0)} 个模型"
        f"（限流 {summary.get('rate_limited', 0)}，未配置 {summary.get('skipped', 0)}）")
    log(f"已生成：{readme_path}")
    log(f"已生成：{csv_path}")
    log(f"已生成：{json_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
