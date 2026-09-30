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
    "ok":            {"icon": "✅", "label": "正常可用",        "desc": "用你的密钥实测返回 200"},
    "catalog_only":  {"icon": "🔵", "label": "目录已确认",      "desc": "未配密钥，但平台公开目录中确认该模型存在"},
    "rate_limited":  {"icon": "⚠️", "label": "限流/额度耗尽",   "desc": "返回 429 或提示配额/余额不足"},
    "bad_request":   {"icon": "🟠", "label": "请求被拒",        "desc": "返回 400，参数或模型不被支持"},
    "auth_error":    {"icon": "🔑", "label": "密钥失效/无权限", "desc": "返回 401/403，密钥无效或权限变更"},
    "missing":       {"icon": "⚪", "label": "目录中已消失",    "desc": "公开目录里查不到它了，疑似已下架"},
    "not_found":     {"icon": "❌", "label": "模型已下架",      "desc": "返回 404，模型 ID 不存在"},
    "server_error":  {"icon": "🌐", "label": "服务端异常",      "desc": "返回 5xx，平台侧故障"},
    "network_error": {"icon": "📡", "label": "网络超时/不可达", "desc": "连接失败或超时"},
    "unknown":       {"icon": "❔", "label": "未知状态",        "desc": "其他返回码"},
    "skipped":       {"icon": "⏭️", "label": "无法判断",        "desc": "未配密钥，且平台目录不公开，无从判断"},
}

STATUS_ORDER = ["ok", "catalog_only", "rate_limited", "bad_request", "auth_error",
                "missing", "not_found", "server_error", "network_error", "unknown", "skipped"]

# 平台级「匿名探活」结果：拿一个明显无效的密钥发一条请求，看接口还在不在
PROBE_META: dict[str, dict[str, str]] = {
    "online":      {"icon": "🟢", "label": "接口在线",     "desc": "鉴权层正常拒绝了无效密钥，说明服务活着、地址没变"},
    "open":        {"icon": "🔓", "label": "无需密钥",     "desc": "无效密钥竟然返回 200，接口可能不校验密钥"},
    "unstable":    {"icon": "🟠", "label": "接口异常",     "desc": "能连上，但返回 5xx / 410 等服务端错误"},
    "gone":        {"icon": "❌", "label": "接口已失效",   "desc": "返回 404，路径变更或服务已下线"},
    "unreachable": {"icon": "📡", "label": "域名不通",     "desc": "连接失败或超时"},
    "unknown":     {"icon": "❔", "label": "探活异常",     "desc": "返回码无法归类"},
    "skipped":     {"icon": "⏭️", "label": "未探活",       "desc": "缺少必要环境变量，或本次关闭了探活"},
}

PROBE_ORDER = ["online", "open", "unstable", "gone", "unreachable", "unknown", "skipped"]

# 探活专用的无效密钥（不是任何平台的真实密钥，只用来触发鉴权错误）
BOGUS_KEY = "sk-invalid-probe-not-a-real-key-000000"

# 「疑似免费」的名字特征，只在 aggressive 模式下用于自动纳入
FREE_HINTS = ("free", "flash", "lite", "turbo", "instant", "nano",
              "8b", "7b", "4b", "3b", "1.5b")

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


# --------------------------------------------------------------------------- #
# 匿名探活 与 目录同步
# --------------------------------------------------------------------------- #

def probe_platform(base_url: str, first_model: str, provider: dict, timeout: float) -> dict:
    """用一个明显无效的密钥探一次平台，判断接口还活着没有。

    因为鉴权通常发生在解析模型之前，无效密钥会稳定地拿到 401/403，
    这就足以证明「服务在线、地址没变」，而且完全不需要真实密钥。
    """
    result = probe(base_url, {"id": first_model}, BOGUS_KEY, provider,
                   timeout=min(timeout, 20.0), retries=0)
    status = result["status"]
    http = result.get("http")
    note = result.get("note", "")

    if status == "ok":
        state = "open"
    elif status == "network_error":
        state = "unreachable"
    elif http == 404:
        # 404 有两种可能：路径变了，或只是这个模型 ID 不被接受 —— 看错误信息提没提 model
        if re.search(r"model|模型", note, re.I):
            state = "online"
            note = f"接口在线，但该模型 ID 不被接受：{note}"
        else:
            state = "gone"
    elif http is not None and (http >= 500 or http == 410):
        state = "unstable"
    elif status in ("auth_error", "rate_limited", "bad_request"):
        state = "online"
    else:
        state = "unknown"

    return {"probe": state, "http": http, "note": shorten(note)}


def fetch_catalog(base_url: str, key: str, provider: dict, timeout: float) -> dict:
    """尝试读取平台的模型目录（GET /models）。有密钥就用密钥，没有就匿名试。

    返回 {"ok": bool, "entries": {模型ID: 原始条目}, "http": ..., "note": ...}
    """
    url = base_url.rstrip("/") + "/models"
    headers = {"Accept": "application/json", "User-Agent": UA}
    if key:
        auth = provider.get("auth", "bearer")
        if auth == "api-key":
            headers["api-key"] = key
        elif auth == "x-api-key":
            headers["x-api-key"] = key
        else:
            headers["Authorization"] = f"Bearer {key}"
    headers.update(provider.get("headers", {}))

    request = urllib.request.Request(url, headers=headers, method="GET")
    try:
        with urllib.request.urlopen(request, timeout=timeout) as resp:
            body = resp.read(8 * 1024 * 1024).decode("utf-8", "replace")
    except urllib.error.HTTPError as exc:
        return {"ok": False, "entries": {}, "http": exc.code,
                "note": f"HTTP {exc.code}：目录不可读"}
    except (urllib.error.URLError, socket.timeout, TimeoutError, ConnectionError, OSError) as exc:
        return {"ok": False, "entries": {}, "http": None,
                "note": shorten(f"{type(exc).__name__}: {exc}")}
    except ValueError as exc:
        return {"ok": False, "entries": {}, "http": 200, "note": shorten(str(exc))}

    try:
        data = json.loads(body)
    except ValueError:
        return {"ok": False, "entries": {}, "http": 200, "note": "返回的不是 JSON"}

    items = data.get("data") if isinstance(data, dict) else data
    if not isinstance(items, list):
        return {"ok": False, "entries": {}, "http": 200, "note": "目录结构无法识别"}

    entries: dict[str, dict] = {}
    for item in items:
        if isinstance(item, dict) and item.get("id"):
            entries[str(item["id"])] = item
        elif isinstance(item, str):
            entries[item] = {}
    return {"ok": True, "entries": entries, "http": 200, "note": ""}


# 明显不是聊天模型的 id 特征（向量、重排、审核、语音、图像/音乐生成）
NON_CHAT_HINTS = ("embed", "rerank", "moderation", "content-safety", "guard",
                  "whisper", "tts", "text-to-speech", "stable-diffusion",
                  "lyria", "veo", "imagen", "dall-e", "sdxl")


def looks_like_chat_model(entry: dict, model_id: str) -> bool:
    """只把「输出纯文本」的模型当聊天模型，过滤掉音频/图像生成、向量、审核模型。"""
    mid = str(model_id).lower()
    if any(hint in mid for hint in NON_CHAT_HINTS):
        return False
    if not isinstance(entry, dict):
        return True
    arch = entry.get("architecture")
    if isinstance(arch, dict):
        out = arch.get("output_modalities")
        if isinstance(out, list) and out and any(m != "text" for m in out):
            return False
        modality = arch.get("modality")
        if isinstance(modality, str) and "->" in modality:
            outs = [x.strip() for x in modality.split("->", 1)[1].split("+")]
            if any(x != "text" for x in outs):
                return False
    return True


def classify_free(entry: dict, model_id: str) -> str:
    """判断一个模型是否免费：confirmed（机器确证）/ likely（名字像）/ unknown。"""
    mid = str(model_id).lower()

    if not looks_like_chat_model(entry if isinstance(entry, dict) else {}, model_id):
        return "unknown"

    if mid.endswith(":free") or mid.startswith("free/") or "/free" in mid:
        return "confirmed"

    if isinstance(entry, dict):
        # 阶梯计费时单价字段没有意义 —— 有些平台把首档写成 0，实际按量收费
        if entry.get("is_tiered_billing"):
            return "unknown"

        pricing = entry.get("pricing")
        if isinstance(pricing, dict):
            try:
                if float(pricing.get("prompt", 1)) == 0 and float(pricing.get("completion", 1)) == 0:
                    return "confirmed"
            except (TypeError, ValueError):
                pass

        # 扁平单价字段：必须输入价和输出价同时为 0 才算确证
        for in_field, out_field in (("input_token_price_per_m", "output_token_price_per_m"),
                                    ("input_price", "output_price"),
                                    ("prompt_price", "completion_price")):
            if in_field in entry or out_field in entry:
                try:
                    price_in = float(entry.get(in_field, 0) or 0)
                    price_out = float(entry.get(out_field, 0) or 0)
                except (TypeError, ValueError):
                    continue
                if price_in == 0 and price_out == 0:
                    return "confirmed"

    if any(hint in mid for hint in FREE_HINTS):
        return "likely"
    return "unknown"


def find_similar_ids(model_id: str, catalog_ids, limit: int = 3) -> list[str]:
    """在目录里找名字相近的 ID，用来提示「模型改名了」而不是「下架了」。"""
    base = str(model_id).split("/")[-1].split(":")[0].lower()
    if len(base) < 4:
        return []
    stem = base[:12]
    return [i for i in sorted(catalog_ids) if stem in str(i).lower()][:limit]


def model_context(meta: dict) -> object:
    """从目录条目里尽量取上下文长度。"""
    if not isinstance(meta, dict):
        return ""
    for field in ("context_length", "context_size", "max_model_len", "max_context_length"):
        if meta.get(field):
            return meta[field]
    return ""


# --------------------------------------------------------------------------- #
# 自动纳管的模型池 models.auto.json
# --------------------------------------------------------------------------- #

def load_auto_pool(path: Path) -> dict:
    """结构：{ENV: {模型ID: {context, basis, adopted_at, fail_streak}}}"""
    data = read_json(path)
    if not isinstance(data, dict):
        return {}
    pool = data.get("providers")
    return pool if isinstance(pool, dict) else {}


def save_auto_pool(path: Path, pool: dict, adopted_note: str) -> None:
    write_json(path, {
        "note": "本文件由 update_list.py 自动维护：只收录能被机器确证免费的模型，"
                "连续 3 轮实测失败会自动剔除。人工请改 PROVIDER_POOL 或 models.custom.json。",
        "last_action": adopted_note,
        "updated_at": datetime.now(CST).strftime("%Y-%m-%d %H:%M:%S"),
        "providers": pool,
    })


def merge_auto_pool(providers: list[dict], auto_pool: dict) -> int:
    """把自动池里的模型并进平台清单（已人工登记的跳过）。"""
    index = {p["env"]: p for p in providers}
    added = 0
    for env, models in (auto_pool or {}).items():
        target = index.get(env)
        if target is None or not isinstance(models, dict):
            continue
        have = {m["id"] for m in target.get("models", [])}
        for mid, meta in models.items():
            if mid in have:
                continue
            meta = meta if isinstance(meta, dict) else {}
            target["models"].append({
                "id": mid,
                "context": meta.get("context", ""),
                "auto": True,
                "note": meta.get("note", "自动发现"),
            })
            have.add(mid)
            added += 1
    return added


# 自动纳入的模型连续多少轮判为失败就剔除
AUTO_DROP_STREAK = 3
# 判定为「失败」的状态（网络类问题不算，避免误杀）
AUTO_FAIL_STATES = {"missing", "not_found", "bad_request", "auth_error"}
# 判定为「健康」的状态
AUTO_OK_STATES = {"ok", "catalog_only", "rate_limited"}


def update_auto_pool_streaks(auto_pool: dict, results: list[dict]) -> tuple[dict, list[dict]]:
    """按实测结果维护失败计数，连续失败的自动剔除。返回（新池, 被剔除清单）。"""
    dropped: list[dict] = []
    tested: list[tuple[str, str]] = []

    for entry in results:
        env = entry["env"]
        models = auto_pool.get(env) or {}
        for item in entry["models"]:
            if not item.get("auto") or item["id"] not in models:
                continue
            tested.append((env, item["id"]))
            meta = models[item["id"]]
            status = item["status"]
            if status in AUTO_OK_STATES:
                meta["fail_streak"] = 0
            elif status in AUTO_FAIL_STATES:
                meta["fail_streak"] = int(meta.get("fail_streak", 0)) + 1
                meta["last_fail"] = f"{checked_at_stamp()} {status}"
            meta["last_status"] = status

    # 只有本轮真正测过的才可能被剔除，避免 --only 之类把没测的误删
    for env, mid in tested:
        meta = (auto_pool.get(env) or {}).get(mid)
        if meta and int(meta.get("fail_streak", 0)) >= AUTO_DROP_STREAK:
            dropped.append({"env": env, "model": mid,
                            "reason": f"连续 {AUTO_DROP_STREAK} 轮实测失败"
                                      f"（最近：{meta.get('last_status', '')}）"})
            del auto_pool[env][mid]

    for env in list(auto_pool.keys()):
        if not auto_pool[env]:
            del auto_pool[env]
    return auto_pool, dropped


def checked_at_stamp() -> str:
    return datetime.now(CST).strftime("%Y-%m-%d %H:%M")


def analyze_discovery(results: list[dict], catalogs: dict[str, dict],
                      adopt_mode: str, max_auto: int, auto_pool: dict,
                      max_candidates_per_provider: int = 8) -> dict:
    """对比「平台公开目录」和「我们已登记的模型」，产出候选与自动纳入清单。"""
    adopted: list[dict] = []
    candidates: list[dict] = []
    absent: list[dict] = []
    catalog_stats: list[dict] = []
    cand_count: dict[str, int] = {}

    for entry in results:
        cat = catalogs.get(entry["env"])
        if not cat:
            continue
        catalog_stats.append({"provider": entry["name"], "env": entry["env"],
                              "count": len(cat), "public": not entry["has_key"]})

        known = {m["id"] for m in entry["models"]}
        for mid in sorted(cat.keys()):
            if mid in known:
                continue
            meta = cat[mid]
            basis = classify_free(meta if isinstance(meta, dict) else {}, mid)
            if basis == "unknown":
                continue
            rec = {"provider": entry["name"], "env": entry["env"], "model": mid,
                   "basis": "确认免费" if basis == "confirmed" else "疑似免费",
                   "context": model_context(meta)}
            take = basis == "confirmed" or (adopt_mode == "aggressive" and basis == "likely")
            if take and adopt_mode != "off":
                already = sum(1 for a in adopted if a["env"] == entry["env"])
                if already < max_auto:
                    adopted.append(rec)
                    continue
            # 候选名单按平台限流，避免被某一家的几百个模型刷屏
            if cand_count.get(entry["env"], 0) < max_candidates_per_provider:
                cand_count[entry["env"]] = cand_count.get(entry["env"], 0) + 1
                candidates.append(rec)

        for item in entry["models"]:
            if item["status"] == "missing":
                absent.append({"provider": entry["name"], "env": entry["env"],
                               "model": item["id"], "auto": item.get("auto", False),
                               "similar": find_similar_ids(item["id"], cat.keys())})

    candidates.sort(key=lambda r: (r["basis"] != "确认免费", r["provider"], r["model"]))
    total_candidates = sum(cand_count.values())
    return {"adopted": adopted, "candidates": candidates, "candidates_total": total_candidates,
            "absent": absent, "catalogs": catalog_stats}


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
                    checked_at: str, do_probe: bool = True, do_discover: bool = True,
                    adopt_mode: str = "safe", max_auto: int = 20,
                    auto_pool: dict | None = None) -> tuple[list[dict], dict[str, dict], dict]:
    """四阶段检测：① 匿名探活 ② 同步平台目录 ③ 自动发现并入池 ④ 逐模型实测。

    返回 (平台结果, {ENV: 目录条目}, 发现结果)
    """
    results: list[dict] = []
    catalogs: dict[str, dict] = {}
    keys: dict[str, str] = {}
    probe_jobs: list[tuple[dict, str, str, dict]] = []
    catalog_jobs: list[tuple[dict, str, str, dict]] = []
    test_jobs: list[tuple[dict, dict, str, str]] = []

    for provider in providers:
        key_env = provider["env"]
        key = os.environ.get(key_env, "").strip()
        keys[key_env] = key
        # 地址里用到的额外变量（requires + {ENV} 占位符）缺了才叫「地址不完整」；
        # 单纯缺 API 密钥不影响匿名探活和读公开目录。
        template_vars = sorted(set(re.findall(r"\{([A-Z0-9_]+)\}", provider.get("base_url", ""))))
        url_vars = list(dict.fromkeys([*provider.get("requires", []), *template_vars]))
        url_missing = [name for name in url_vars if not os.environ.get(name, "").strip()]
        missing = ([key_env] if not key else []) + url_missing

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
            "probe": "skipped",
            "probe_http": None,
            "probe_note": "",
            "catalog": {"ok": False, "count": 0, "public": False, "note": ""},
            "models": [],
        }

        for model in provider["models"]:
            entry["models"].append({
                "id": model["id"],
                "context": model.get("context", provider.get("context", "")),
                "quota": model.get("quota", provider.get("quota", "")),
                "lifetime": model.get("lifetime", provider.get("lifetime", "")),
                "note": model.get("note", ""),
                "auto": bool(model.get("auto")),
                "source": "自动发现" if model.get("auto") else "人工登记",
                "status": None,
                "http": None,
                "latency_ms": None,
                "checked_at": checked_at,
            })

        if base_url and provider["models"] and not url_missing:
            if do_probe:
                probe_jobs.append((entry, base_url, provider["models"][0]["id"], provider))
            if do_discover:
                catalog_jobs.append((entry, base_url, key, provider))
        elif url_missing:
            entry["probe"] = "skipped"
            entry["probe_note"] = f"缺少环境变量 {', '.join(url_missing)}，地址不完整，无法探测"
            entry["catalog"] = {"ok": False, "count": 0, "public": False,
                                "note": f"缺少环境变量 {', '.join(url_missing)}"}
        results.append(entry)

    # ---- 阶段一 & 二：匿名探活 + 目录同步（并发） ----
    if probe_jobs or catalog_jobs:
        log(f"匿名探活 {len(probe_jobs)} 个平台、同步目录 {len(catalog_jobs)} 个平台…")
        with ThreadPoolExecutor(max_workers=max(1, workers)) as pool:
            p_futures = {pool.submit(probe_platform, bu, mid, pv, timeout): e
                         for e, bu, mid, pv in probe_jobs}
            c_futures = {pool.submit(fetch_catalog, bu, k, pv, timeout): e
                         for e, bu, k, pv in catalog_jobs}
            for future in as_completed(list(p_futures) + list(c_futures)):
                if future in p_futures:
                    entry = p_futures[future]
                    try:
                        out = future.result()
                    except Exception as exc:  # noqa: BLE001
                        out = {"probe": "unknown", "http": None, "note": str(exc)}
                    entry["probe"] = out["probe"]
                    entry["probe_http"] = out.get("http")
                    entry["probe_note"] = out.get("note", "")
                    meta = PROBE_META.get(entry["probe"], PROBE_META["unknown"])
                    log(f"  {meta['icon']} [探活] {entry['name']} -> {entry['probe']}")
                else:
                    entry = c_futures[future]
                    try:
                        out = future.result()
                    except Exception as exc:  # noqa: BLE001
                        out = {"ok": False, "entries": {}, "http": None, "note": str(exc)}
                    entries = out.get("entries", {})
                    if out["ok"]:
                        catalogs[entry["env"]] = entries
                    entry["catalog"] = {
                        "ok": out["ok"],
                        "count": len(entries),
                        "public": out["ok"] and not entry["has_key"],
                        "note": out.get("note", ""),
                    }
                    if out["ok"]:
                        log(f"  📚 [目录] {entry['name']} 读到 {len(entries)} 个模型"
                            f"{'（无需密钥）' if not entry['has_key'] else ''}")

    # ---- 阶段三：自动发现 —— 把目录里能确证免费的模型并进池子，让它们本轮就参与实测 ----
    discovery = analyze_discovery(results, catalogs, adopt_mode, max_auto, auto_pool or {})
    newly_adopted: list[dict] = []
    index = {e["env"]: e for e in results}
    for rec in discovery["adopted"]:
        entry = index.get(rec["env"])
        if entry is None:
            continue
        have = {m["id"] for m in entry["models"]}
        already_known = rec["model"] in have
        if rec["env"] in (auto_pool or {}) and rec["model"] in (auto_pool or {}).get(rec["env"], {}):
            continue  # 早就在自动池里了，merge_auto_pool 已经带进来
        if not already_known:
            entry["models"].append({
                "id": rec["model"],
                "context": rec.get("context", ""),
                "quota": entry.get("quota", ""),
                "lifetime": entry.get("lifetime", ""),
                "note": f"自动发现（{rec['basis']}）",
                "auto": True,
                "source": "自动发现",
                "status": None,
                "http": None,
                "latency_ms": None,
                "checked_at": checked_at,
            })
        newly_adopted.append(rec)
        log(f"  ➕ [自动纳入] {rec['provider']} {rec['model']}（{rec['basis']}）")
    discovery["newly_adopted"] = newly_adopted

    # ---- 阶段四：判定初始状态，能实测的排进队列 ----
    for entry in results:
        cat = catalogs.get(entry["env"]) or {}
        for item in entry["models"]:
            if entry["has_key"]:
                test_jobs.append((entry, item, entry["base_url"], keys[entry["env"]]))
            elif cat:
                if item["id"] in cat:
                    item.update({"status": "catalog_only", "http": 200, "latency_ms": None,
                                 "note": "公开目录中存在；未配密钥，无法验证可用性"})
                else:
                    item.update({"status": "missing", "http": None, "latency_ms": None,
                                 "note": "平台公开目录里已经找不到这个模型了"})
            else:
                reason = (f"缺少环境变量 {', '.join(entry['missing_env'])}"
                          if entry["missing_env"] else "未配密钥，且平台目录不公开")
                item.update({"status": "skipped", "http": None, "latency_ms": None, "note": reason})

    if test_jobs:
        log(f"开始实测 {len(test_jobs)} 个模型（并发 {workers}，超时 {timeout:g}s，重试 {retries} 次）…")
        with ThreadPoolExecutor(max_workers=max(1, workers)) as pool:
            futures = {
                pool.submit(probe, base_url, {"id": item["id"]}, key, entry, timeout, retries): (entry, item)
                for entry, item, base_url, key in test_jobs
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
        for item in entry["models"]:
            if item["status"] is None:
                item["status"] = "unknown"
        statuses = [m["status"] for m in entry["models"]]
        entry["status"] = aggregate_status(statuses)
        entry["available"] = sum(1 for s in statuses if s == "ok")
        entry["confirmed"] = sum(1 for s in statuses if s in ("ok", "catalog_only"))
        entry["total"] = len(statuses)
    return results, catalogs, discovery


# --------------------------------------------------------------------------- #
# 输出：status.json / csv / README.md / history.jsonl
# --------------------------------------------------------------------------- #

def summarize(providers: list[dict]) -> dict:
    counts = {status: 0 for status in STATUS_META}
    for status in PROBE_META:
        counts[f"probe_{status}"] = 0
    for provider in providers:
        counts[f"probe_{provider.get('probe', 'skipped')}"] = \
            counts.get(f"probe_{provider.get('probe', 'skipped')}", 0) + 1
        for model in provider["models"]:
            counts[model["status"]] = counts.get(model["status"], 0) + 1
    counts["providers_total"] = len(providers)
    counts["providers_configured"] = sum(1 for p in providers if p["has_key"])
    counts["providers_available"] = sum(1 for p in providers if p["status"] == "ok")
    counts["providers_probed"] = sum(1 for p in providers if p.get("probe") != "skipped")
    counts["providers_catalog_public"] = sum(
        1 for p in providers if (p.get("catalog") or {}).get("ok") and not p["has_key"])
    counts["providers_catalog_ok"] = sum(1 for p in providers if (p.get("catalog") or {}).get("ok"))
    counts["models_total"] = sum(len(p["models"]) for p in providers)
    counts["models_available"] = counts.get("ok", 0)
    counts["models_confirmed"] = counts.get("ok", 0) + counts.get("catalog_only", 0)
    counts["models_auto"] = sum(1 for p in providers for m in p["models"] if m.get("auto"))
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
        writer.writerow(["平台", "接口探活", "密钥变量名", "模型ID", "来源", "BaseURL", "上下文",
                         "额度类型", "预期有效期", "状态", "状态码", "延迟(ms)", "备注", "检测时间"])
        for provider in providers:
            probe = PROBE_META.get(provider.get("probe", "skipped"), PROBE_META["skipped"])
            probe_text = f"{probe['icon']} {probe['label']}"
            for model in provider["models"]:
                meta = STATUS_META.get(model["status"], STATUS_META["unknown"])
                writer.writerow([
                    provider["name"], probe_text, provider["env"], model["id"],
                    model.get("source", "人工登记"), provider["base_url"],
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
                  generated_at: datetime, elapsed: float, cron: str, history: list[dict],
                  discovery: dict | None = None, adopt_mode: str = "safe") -> str:
    discovery = discovery or {}
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
    add(f"- **实测可用**：**{summary.get('ok', 0)} / {summary.get('models_total', 0)}**"
        f"（未配密钥但目录已确认存在 🔵 {summary.get('catalog_only', 0)} 个）"
        f"　|　**已配置平台**：{summary.get('providers_configured', 0)} / {summary.get('providers_total', 0)}")
    add(f"- **接口探活**：{summary.get('providers_probed', 0)} 个平台已探活"
        f"（🟢 在线 {summary.get('probe_online', 0)}，❌ 失效 {summary.get('probe_gone', 0)}，"
        f"📡 不通 {summary.get('probe_unreachable', 0)}）"
        f"　|　**可读目录**：{summary.get('providers_catalog_ok', 0)} 个平台"
        f"（其中 {summary.get('providers_catalog_public', 0)} 个无需密钥）")
    add("")
    add("> 这套清单是**自己维护自己**的：平台接口死活靠「匿名探活」（用一个无效密钥试，")
    add("> 401 说明服务活着），模型增删靠拉平台公开的 `/models` 目录，")
    add("> 能被机器确证免费的模型会自动纳入 `models.auto.json`，连续 3 轮实测失败会自动剔除。")
    add("")
    add("| 状态 | 数量 | 说明 |")
    add("| --- | ---: | --- |")
    for status in STATUS_ORDER:
        meta = STATUS_META[status]
        add(f"| {meta['icon']} {meta['label']} | {summary.get(status, 0)} | {meta['desc']} |")
    add("")
    add("**平台级「接口探活」**（不需要任何密钥，用无效密钥试出来的）：")
    add("")
    add("| 探活结果 | 平台数 | 说明 |")
    add("| --- | ---: | --- |")
    for state in PROBE_ORDER:
        meta = PROBE_META[state]
        add(f"| {meta['icon']} {meta['label']} | {summary.get('probe_' + state, 0)} | {meta['desc']} |")
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
    add("| 平台 | 接口探活 | 模型状态 | 密钥变量 | 目录 | 额度类型 | 申请地址 |")
    add("| --- | --- | --- | --- | ---: | --- | --- |")
    for provider in providers:
        console = f"[控制台]({provider['console']})" if provider["console"] else "-"
        probe = PROBE_META.get(provider.get("probe", "skipped"), PROBE_META["skipped"])
        cat = provider.get("catalog") or {}
        if cat.get("ok"):
            catalog_cell = f"{cat['count']}" + ("（公开）" if cat.get("public") else "")
        else:
            catalog_cell = "-"
        add(f"| {provider['name']} | {probe['icon']} {probe['label']} | "
            f"{status_cell(provider['status'])} {provider['available']}/{provider['total']} | "
            f"`{provider['env']}` | {catalog_cell} | "
            f"{provider.get('quota', '')} | {console} |")
    add("")

    # ---------------- 自动发现 ----------------
    adopted = discovery.get("newly_adopted") or discovery.get("adopted") or []
    candidates = discovery.get("candidates") or []
    absent = discovery.get("absent") or []
    dropped = discovery.get("dropped") or []

    add("## 自动发现")
    add("")
    add("这一节的内容**全部由脚本自动产生**，不需要人工维护：")
    add("")
    add("- **自动纳入**：从平台公开目录里读到、且能被机器确证免费的模型 → 自动进 `models.auto.json`")
    add("- **候选**：名字看起来免费但无法确证的 → 只列在这里，等你确认后才进池子")
    add("- **目录中消失**：我们登记了、但平台目录里已经查不到 → 大概率被下架了")
    add("")
    add(f"> 当前自动纳入模式：**{adopt_mode}**"
        f"（`safe` = 只收机器确证免费的；`aggressive` = 名字像的也收；`off` = 只记候选）")
    add("")

    if adopted:
        add(f"### 本轮自动纳入 {len(adopted)} 个模型")
        add("")
        add("| 平台 | 模型 | 依据 | 上下文 |")
        add("| --- | --- | --- | ---: |")
        for rec in adopted[:40]:
            add(f"| {rec['provider']} | `{rec['model']}` | {rec['basis']} | {fmt_context(rec.get('context'))} |")
        if len(adopted) > 40:
            add(f"| … | 其余 {len(adopted) - 40} 个见 `models.auto.json` | | |")
        add("")

    if dropped:
        add(f"### 本轮自动剔除 {len(dropped)} 个模型")
        add("")
        add("| 平台 | 模型 | 原因 |")
        add("| --- | --- | --- |")
        for rec in dropped[:20]:
            add(f"| {rec['env']} | `{rec['model']}` | {rec['reason']} |")
        add("")

    if absent:
        add(f"### ⚠️ 目录中已消失 {len(absent)} 个（疑似下架或改名）")
        add("")
        add("| 平台 | 原先登记的模型 | 来源 | 目录里相近的 ID（可能只是改名） |")
        add("| --- | --- | --- | --- |")
        for rec in absent[:30]:
            similar = "、".join(f"`{s}`" for s in rec.get("similar", [])) or "-"
            add(f"| {rec['provider']} | `{rec['model']}` | "
                f"{'自动纳入' if rec.get('auto') else '人工登记'} | {similar} |")
        add("")

    if candidates:
        add(f"### 候选（未自动纳入，共 {discovery.get('candidates_total', len(candidates))} 个）")
        add("")
        add("名字看起来是免费档、但平台没给出可机器核对的定价信息，所以只列在这里。")
        add("想收进来就把对应 `id` 加到 `models.custom.json`，或者手动跑 `--adopt aggressive`。")
        add("")
        add("| 平台 | 模型 | 依据 | 上下文 |")
        add("| --- | --- | --- | ---: |")
        for rec in candidates[:30]:
            add(f"| {rec['provider']} | `{rec['model']}` | {rec['basis']} | {fmt_context(rec.get('context'))} |")
        if len(candidates) > 30:
            add(f"| … | 其余 {len(candidates) - 30} 个已截断 | | |")
        add("")

    if not (adopted or dropped or absent or candidates):
        add("本轮没有发现新增、消失或候选模型。")
        add("")
        add("> 目录不公开的平台（智谱、Kimi、硅基流动等需要密钥才能读 `/models`）")
        add("> 只有配上密钥才能参与自动发现；没配密钥的平台本轮不产生任何发现。")
        add("")

    add("## 模型明细")
    add("")
    add("| 平台 | 模型 ID | 来源 | 上下文 | 额度类型 | 预期有效期 | 状态 | HTTP | 延迟 | 备注 |")
    add("| --- | --- | --- | ---: | --- | --- | --- | ---: | ---: | --- |")
    for provider in providers:
        for model in provider["models"]:
            note = (model.get("note", "") or "").replace("|", "\\|")
            add(f"| {provider['name']} | `{model['id']}` | {model.get('source', '人工登记')} | "
                f"{fmt_context(model.get('context'))} | "
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
    add("GitHub Actions 每 4 小时启动一次云环境，运行 `update_list.py`，全程不需要服务器。")
    add("脚本只用 Python 标准库，**不需要 pip install**。每一轮跑四件事：")
    add("")
    add("1. **匿名探活**：给每个平台发一条用「无效密钥」的请求。鉴权通常发生在解析模型之前，")
    add("   所以返回 `401/403/400` 就说明 **服务活着、地址没变**；`404` 说明路径变了或服务下线；")
    add("   连不上说明域名不通。**这一步完全不需要真实密钥**，28 个平台全都有状态。")
    add("2. **同步目录**：请求各平台的 `GET /models`。有 7 家的目录是公开可读的（不需要密钥），")
    add("   其余需要密钥。读到之后和本地清单对比，就能发现**模型增删和改名**。")
    add("3. **自动发现**：目录里能被机器确证免费的模型（定价字段为 0、或 ID 带 `:free`）")
    add("   自动写进 `models.auto.json` 并纳入下一轮检测；名字像但无法确证的只进「候选区」。")
    add("   自动收进来的模型如果连续 3 轮实测失败，会被自动剔除（自净）。")
    add("4. **逐模型实测**：对**配了密钥**的平台，每个模型发一条 `max_tokens=1` 的极短请求，")
    add("   几乎不消耗免费额度，按返回码判定可用性。")
    add("")
    add("然后把结果写成 README / CSV / status.json，状态有变化时追加 history.jsonl，最后 commit & push。")
    add("")
    add("### 产出文件")
    add("")
    add("| 文件 | 用途 |")
    add("| --- | --- |")
    add("| `README.md` | 本文件，可读表格版，GitHub 直接预览 |")
    add("| `free_llm_api.csv` | 可下载表格（带 BOM，Excel 双击不乱码） |")
    add("| `status.json` | 结构化数据，供程序调用（例如自动切换代理） |")
    add("| `models.auto.json` | **脚本自己维护**的自动纳管模型池（确证免费的才进，连续失败自动剔除） |")
    add("| `history.jsonl` | 状态**变化**历史，一行一次变更快照 |")
    add("")
    add("三层模型池的关系：")
    add("")
    add("| 文件 | 谁写 | 作用 |")
    add("| --- | --- | --- |")
    add("| `update_list.py` 里的 `PROVIDER_POOL` | 人工 | 骨架：平台地址、申请入口、免费额度说明 |")
    add("| `models.custom.json` | 人工 | 你自己增删的模型（可选，默认没有这个文件） |")
    add("| `models.auto.json` | **脚本** | 自动发现的模型，不用管它，它会自己长也会自己瘦 |")
    add("")
    add("`status.json` 每次都会因为时间戳变化而提交一次（相当于心跳，能看出定时任务有没有在跑）；")
    add("`history.jsonl` 只在状态变化或发现增减时追加，所以历史记录是干净的。")
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
    add("python update_list.py                              # 检测全部平台（探活 + 目录 + 实测）")
    add("python update_list.py --only ZHIPU_KEY,GROQ_KEY     # 只检测指定平台")
    add("python update_list.py --list                        # 只看模型池，不发任何请求")
    add("python update_list.py --no-probe --no-discover      # 只实测，不探活不同步目录")
    add("python update_list.py --adopt off                   # 只把发现记进候选区，不自动纳入")
    add("python update_list.py --adopt aggressive            # 名字像免费的也自动收进来")
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
    add("| 全部显示 ⏭️ 无法判断 | 没配密钥，且该平台目录不公开 —— 这是正常的，平台级「接口探活」仍然有效 |")
    add("| 平台是 🟢 但模型全是 🔑 | 接口活着，是密钥不对（复制错了、被吊销、或没开通对应模型） |")
    add("| 平台是 ❌ 接口已失效 | 该平台的接口路径返回 404，可能已下线或改地址，需要改 `PROVIDER_POOL` 里的 `base_url` |")
    add("| 某个模型 ⚪ 目录中已消失 | 平台目录里查不到这个 ID 了；看「相近的 ID」列，多半只是改了名 |")
    add("| 一直是 ⚠️ 限流 | 免费额度确实用完了（或账号在共享 IP 上被限速），等下个周期再看 |")
    add("| 自动纳入了奇怪的模型 | 把 `--adopt` 改成 `off` 或 `safe`，并在 `models.auto.json` 里删掉它 |")
    add("| 报 `HttpError: 403` 且没提交 | 仓库的 Workflow permissions 还是只读，参考「部署到自己的仓库」第 3 步 |")
    add("| 大量 📡 域名不通 | GitHub Runner 出口或被墙平台连通性问题，脚本会自动重试，偶发可忽略 |")
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
    parser.add_argument("--probe", action=argparse.BooleanOptionalAction, default=True,
                        help="是否做匿名探活（用无效密钥判断接口是否在线），默认开启")
    parser.add_argument("--discover", action=argparse.BooleanOptionalAction, default=True,
                        help="是否同步平台公开目录并自动发现模型，默认开启")
    parser.add_argument("--adopt", choices=["safe", "aggressive", "off"], default="safe",
                        help="自动纳入尺度：safe=只收机器确证免费的（默认）；"
                             "aggressive=名字像的也收；off=只记候选不纳入")
    parser.add_argument("--max-auto", type=int, default=20,
                        help="每个平台每轮最多自动纳入多少个模型，默认 20")
    parser.add_argument("--auto-file", default="models.auto.json",
                        help="自动纳管的模型池文件，默认 models.auto.json")
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

    auto_path = Path(args.auto_file)
    if not auto_path.is_absolute():
        auto_path = ROOT / auto_path
    auto_pool = load_auto_pool(auto_path)

    only = [name.strip() for name in args.only.split(",") if name.strip()]
    providers = build_providers(custom_path, only)
    auto_merged = merge_auto_pool(providers, auto_pool)
    if auto_merged:
        log(f"从 {auto_path.name} 自动纳入了 {auto_merged} 个模型")

    if args.list:
        total = 0
        for provider in providers:
            log(f"{provider['name']}  [{provider['env']}]  {provider['base_url']}")
            for model in provider["models"]:
                total += 1
                tag = "  (自动)" if model.get("auto") else ""
                log(f"    - {model['id']}  ({fmt_context(model.get('context'))}){tag}")
        log(f"\n共 {len(providers)} 个平台 / {total} 个模型"
            f"（其中自动纳入 {auto_merged} 个）")
        return 0

    readme_path = out_dir / "README.md"
    csv_path = out_dir / "free_llm_api.csv"
    json_path = out_dir / "status.json"
    history_path = out_dir / "history.jsonl"

    previous = read_json(json_path)
    started = time.perf_counter()
    generated_at = datetime.now(CST)
    checked_at = generated_at.strftime("%Y-%m-%d %H:%M:%S")

    results, catalogs, discovery = check_providers(
        providers, args.timeout, args.retries, args.workers, checked_at,
        do_probe=args.probe, do_discover=args.discover,
        adopt_mode=args.adopt, max_auto=args.max_auto, auto_pool=auto_pool)
    elapsed = time.perf_counter() - started

    # ---- 把本轮新纳入的模型写进自动池，并做自净 ----
    newly = 0
    for rec in discovery.get("newly_adopted", []):
        env_models = auto_pool.setdefault(rec["env"], {})
        if rec["model"] in env_models:
            continue
        env_models[rec["model"]] = {
            "context": rec.get("context", ""),
            "basis": rec["basis"],
            "adopted_at": checked_at,
            "fail_streak": 0,
            "note": f"自动发现（{rec['basis']}）",
        }
        newly += 1
    if newly:
        log(f"已写入自动池：{newly} 个新模型（模式 {args.adopt}）")

    auto_pool, dropped = update_auto_pool_streaks(auto_pool, results)
    discovery["dropped"] = dropped
    if dropped:
        log(f"自动剔除 {len(dropped)} 个连续失败的模型")
    if args.discover and args.adopt != "off":
        save_auto_pool(auto_path, auto_pool, f"本轮新纳入 {newly} 个，剔除 {len(dropped)} 个")

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
        "adopt_mode": args.adopt,
        "summary": summary,
        "changes": changes,
        "discovery": {
            "newly_adopted": newly,
            "adopted": discovery.get("newly_adopted", []),
            "dropped": discovery["dropped"],
            "absent": discovery["absent"],
            "candidates_total": discovery.get("candidates_total", 0),
            "candidates": discovery["candidates"],
            "catalogs": discovery["catalogs"],
        },
        "providers": [
            {
                "name": p["name"], "env": p["env"], "base_url": p["base_url"],
                "console": p["console"], "quota": p["quota"], "lifetime": p["lifetime"],
                "has_key": p["has_key"], "missing_env": p["missing_env"],
                "probe": p["probe"], "probe_http": p["probe_http"], "probe_note": p["probe_note"],
                "catalog": p["catalog"],
                "status": p["status"], "available": p["available"],
                "confirmed": p["confirmed"], "total": p["total"],
                "models": p["models"],
            }
            for p in results
        ],
    }

    readme = render_readme(results, summary, changes, generated_at, elapsed,
                           args.cron, history, discovery, args.adopt)
    write_text_lf(readme_path, readme)
    write_csv(csv_path, results)
    write_json(json_path, payload)

    if not args.no_history:
        if not history_path.exists():
            write_text_lf(history_path, "")
        if changes or previous is None or newly or dropped:
            append_history(history_path, {
                "at": checked_at,
                "ok": summary.get("ok", 0),
                "catalog_only": summary.get("catalog_only", 0),
                "total": summary.get("models_total", 0),
                "adopted": newly,
                "dropped": len(dropped),
                "changes": changes,
            })

    log("")
    log(f"接口探活：在线 {summary.get('probe_online', 0)}，失效 {summary.get('probe_gone', 0)}，"
        f"不通 {summary.get('probe_unreachable', 0)}")
    log(f"模型：✅ 裸测可用 {summary.get('ok', 0)}，🔵 目录已确认 {summary.get('catalog_only', 0)}，"
        f"⚪ 目录消失 {summary.get('missing', 0)}，⏭️ 无法判断 {summary.get('skipped', 0)}"
        f"（共 {summary.get('models_total', 0)}）")
    log(f"自动发现：本轮新纳入 {newly}，剔除 {len(dropped)}，"
        f"候选 {discovery.get('candidates_total', 0)}")
    log(f"已生成：{readme_path}")
    log(f"已生成：{csv_path}")
    log(f"已生成：{json_path}")
    if args.discover and args.adopt != "off":
        log(f"已更新：{auto_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
