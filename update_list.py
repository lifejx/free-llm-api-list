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
import hashlib
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
from html import unescape as html_unescape
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

# 中国大陆用户拿到一个可用 key 的现实难度（官方核实，不是猜的）
DIFFICULTY_META: dict[str, dict[str, str]] = {
    "easy":    {"icon": "🟢", "label": "容易",     "desc": "注册即用，境内直接调用"},
    "medium":  {"icon": "🟡", "label": "要点技巧", "desc": "需要实名/邮箱/特定注册路径，但仍可搞定"},
    "hard":    {"icon": "🟠", "label": "较难",     "desc": "需要非中国出口或外币卡"},
    "blocked": {"icon": "⛔", "label": "不可用",   "desc": "官方按国家/地区封锁中国大陆"},
    "unknown": {"icon": "❔", "label": "未知",     "desc": "官方页面未说明"},
}

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

POOL_FILE = "providers.json"


def load_pool(path: Path | None = None) -> list[dict]:
    """平台与模型清单放在 providers.json 里，人工维护时不用改代码。

    文件里的每个平台可以带一个 policy 字段（免费性质、限流、申请门槛、来源 URL），
    这些数据来自 2026-09-30 的官方核实，会原样出现在 README / CSV / status.json 里。
    """
    target = path or (ROOT / POOL_FILE)
    if not target.exists():
        raise SystemExit(f"找不到平台清单：{target}（它应该和本脚本放在同一目录）")
    data = json.loads(target.read_text(encoding="utf-8"))
    providers = data.get("providers") if isinstance(data, dict) else data
    if not isinstance(providers, list) or not providers:
        raise SystemExit(f"{target} 里没有可用的 providers 数组")
    return providers


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


# 工具调用（function calling）探测 —— agent 工具（DSH/Cline/Roo）的命根子。
# 光有 200 不够：很多免费小模型要么 400 明说不支持，要么默默收下 tools 却从不吐 tool_calls。
TOOL_DEFINITION = [{
    "type": "function",
    "function": {
        "name": "get_weather",
        "description": "查询指定城市的当前天气",
        "parameters": {
            "type": "object",
            "properties": {"city": {"type": "string", "description": "城市名，例如 Beijing"}},
            "required": ["city"],
        },
    },
}]
TOOL_PROMPT = "What is the weather like in Beijing right now? Use the get_weather tool."
TOOL_MAX_TOKENS = 2048  # 思考模型要先烧推理 token，给小预算会误判成「不调用」
TOOLS_META = {
    "yes": ("🔧", "原生工具调用"),
    "accepted": ("〽️", "收参不吐调用"),
    "no": ("—", "不支持工具"),
}


def tools_label(value) -> str:
    """CSV / 表格里展示工具调用实测结论。"""
    meta = TOOLS_META.get(value)
    if not meta:
        return "未测"
    return f"{meta[0]} {meta[1]}"


def extract_tool_calls(body: str) -> tuple[bool, str]:
    """从 chat/completions 200 响应里找原生 tool_calls。"""
    try:
        data = json.loads(body)
        choices = data.get("choices") or []
        msg = (choices[0] if choices else {}).get("message") or {}
    except (ValueError, AttributeError, IndexError):
        return False, ""
    for call in msg.get("tool_calls") or []:
        fn = (call or {}).get("function") or {}
        if fn.get("name"):
            return True, f"{fn['name']}({str(fn.get('arguments') or '')[:60]})"
    return False, ""


def probe_tools(base_url: str, model: dict, key: str, provider: dict,
                timeout: float) -> dict:
    """对已确认可用的模型再探一次工具调用，返回 {tools, tools_note}。

    tools: yes=端到端吐出 tool_calls；accepted=参数被接受但没吐调用（agent 不可靠）；
           no=明确不支持；None=限流/未知，本轮不判。
    """
    url = base_url.rstrip("/") + "/chat/completions"
    headers = {"Content-Type": "application/json", "Accept": "application/json",
               "User-Agent": UA}
    auth = provider.get("auth", "bearer")
    if auth == "api-key":
        headers["api-key"] = key
    elif auth == "x-api-key":
        headers["x-api-key"] = key
    else:
        headers["Authorization"] = f"Bearer {key}"
    headers.update(provider.get("headers", {}))

    def post(tool_choice: str) -> tuple[int | None, str]:
        payload = {
            "model": model["id"],
            "messages": [{"role": "user", "content": TOOL_PROMPT}],
            "temperature": 0, "stream": False, "max_tokens": TOOL_MAX_TOKENS,
            "tools": TOOL_DEFINITION, "tool_choice": tool_choice,
        }
        request = urllib.request.Request(
            url, data=json.dumps(payload).encode("utf-8"), headers=headers, method="POST")
        try:
            with urllib.request.urlopen(request, timeout=timeout) as resp:
                return resp.status, resp.read(16384).decode("utf-8", "replace")
        except urllib.error.HTTPError as exc:
            try:
                return exc.code, exc.read(4096).decode("utf-8", "replace")
            except Exception:  # noqa: BLE001
                return exc.code, ""
        except (urllib.error.URLError, socket.timeout, TimeoutError, OSError):
            return None, ""

    code, body = post("required")
    if code == 200:
        called, frag = extract_tool_calls(body)
        return {"tools": "yes" if called else "accepted",
                "tools_note": frag if called else ""}

    note = extract_message(body)
    if code in (429, 402) or has_quota_hint(body):
        return {"tools": None, "tools_note": "限流/额度不足，工具能力本轮未测"}
    if code in (400, 406, 422) and re.search(r"tool_choice|required|\bany\b", note, re.I):
        # 部分平台只接受 tool_choice=auto，降级再试
        code2, body2 = post("auto")
        if code2 == 200:
            called, frag = extract_tool_calls(body2)
            return {"tools": "yes" if called else "accepted", "tools_note": ""}
        if code2 in (429, 402) or has_quota_hint(body2):
            return {"tools": None, "tools_note": "限流/额度不足，工具能力本轮未测"}
        code, body, note = code2, body2, (extract_message(body2) or note)
    if code in (400, 406, 422) and re.search(r"tool|function|工具", note, re.I):
        return {"tools": "no", "tools_note": shorten(note)}
    return {"tools": None, "tools_note": ""}


def probe_with_tools(base_url: str, model: dict, key: str, provider: dict,
                     timeout: float, retries: int) -> dict:
    """常规实测通过后追加一次工具调用探测（只有真实密钥的实测会走到这里）。"""
    outcome = probe(base_url, model, key, provider, timeout, retries)
    if outcome.get("status") == "ok":
        try:
            outcome.update(probe_tools(base_url, model, key, provider, timeout))
        except Exception as exc:  # noqa: BLE001 - 工具探测失败不影响可用性结论
            outcome.update({"tools": None,
                            "tools_note": f"工具探测异常：{type(exc).__name__}"})
    return outcome


# --------------------------------------------------------------------------- #
# 匿名探活 与 目录同步
# --------------------------------------------------------------------------- #

def probe_platform(base_url: str, first_model: str, provider: dict, timeout: float) -> dict:
    """用一个明显无效的密钥探一次平台，判断接口还活着没有。

    因为鉴权通常发生在解析模型之前，无效密钥会稳定地拿到 401/403，
    这就足以证明「服务在线、地址没变」，而且完全不需要真实密钥。
    """
    result = probe(base_url, {"id": first_model}, BOGUS_KEY, provider,
                   timeout=timeout, retries=0)
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
                  "lyria", "veo", "imagen", "dall-e", "sdxl",
                  "ocr", "asr", "sensevoice", "reranker")


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


def fetch_pricing_catalog(url: str, timeout: float) -> dict:
    """从「公开定价页」里抽出免费模型。

    有些平台的模型列表接口不返回定价，但官网定价页的 HTML 里内嵌着完整数据，
    字段形如 modelName / contextLen / price / type / subType。
    这里把它转成和 /models 一样的结构，下游的免费判定、自动纳入、上下文填充都不用改。
    """
    ok, body, note = fetch_raw(url, timeout)
    if not ok:
        return {"ok": False, "entries": {}, "note": note}

    # 页面里的 JSON 藏在 JS 字符串里，引号是转义过的，先反转义再解析
    body = body.replace('\\"', '"').replace("\\n", " ")

    entries: dict[str, dict] = {}
    starts = [m.start() for m in re.finditer(r'"modelName":"', body)]
    for i, pos in enumerate(starts):
        end = starts[i + 1] if i + 1 < len(starts) else min(len(body), pos + 4000)
        chunk = body[pos:end]
        name = re.search(r'"modelName":"([^"\\]+)"', chunk)
        if not name:
            continue
        mid = name.group(1)
        price = re.search(r'"price":"([\d.]+)"', chunk)
        ctx = re.search(r'"contextLen":(\d+)', chunk)
        mtype = re.search(r'"type":"([^"]*)"', chunk)
        subtype = re.search(r'"subType":"([^"]*)"', chunk)
        if not price or float(price.group(1)) != 0:
            continue                      # 不是免费模型
        if mtype and mtype.group(1) != "text":
            continue                      # 只收文本模型
        if subtype and subtype.group(1) not in ("chat", ""):
            continue                      # 只收对话模型，跳过 ASR/OCR/向量/图像
        entry: dict = {"id": mid, "pricing": {"prompt": "0", "completion": "0"},
                       "architecture": {"output_modalities": ["text"]}}
        if ctx:
            entry["context_length"] = int(ctx.group(1))
        entries[mid] = entry

    return {"ok": bool(entries), "entries": entries,
            "note": "" if entries else "定价页里没解析出免费模型（页面结构可能变了）"}


# 公开定价页作为「目录」来源：不需要密钥，但只对配了密钥的平台生效
PRICING_SOURCES: dict[str, dict] = {
    "SILICONFLOW_KEY": {
        "url": "https://siliconflow.cn/pricing",
        "note": "官网定价页内嵌 RSC 载荷，含 modelName / price / contextLen / subType",
    },
}


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
                "连续 3 轮实测失败会自动剔除。人工请改 providers.json 或 models.custom.json。",
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
    """平台清单（providers.json）+ 自定义模型池合并，并按 --only 过滤。"""
    providers: list[dict] = json.loads(json.dumps(load_pool(), ensure_ascii=False))

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


def select_batch(models: list[dict], previous_map: dict, run_index: int, batch: int) -> set[int]:
    """按轮次挑一批要实测的模型，避免每轮把所有模型都打一遍。

    优先测「从没测过的」，剩下的按轮次轮换 —— 这样巡检本身不会把免费额度烧光。
    batch <= 0 表示不轮换，全测。
    """
    if batch <= 0 or batch >= len(models):
        return set(range(len(models)))

    fresh = [i for i, m in enumerate(models) if m["id"] not in previous_map]
    rest = [i for i in range(len(models)) if i not in fresh]
    pick: set[int] = set(fresh[:batch])
    remaining = batch - len(pick)
    if remaining > 0 and rest:
        start = (run_index * remaining) % len(rest)
        for k in range(min(remaining, len(rest))):
            pick.add(rest[(start + k) % len(rest)])
    return pick


def check_providers(providers: list[dict], timeout: float, retries: int, workers: int,
                    checked_at: str, do_probe: bool = True, do_discover: bool = True,
                    adopt_mode: str = "safe", max_auto: int = 20,
                    auto_pool: dict | None = None, previous: dict | None = None,
                    run_index: int = 0, batch: int = 3) -> tuple[list[dict], dict[str, dict], dict]:
    """四阶段检测：① 匿名探活 ② 同步平台目录 ③ 自动发现并入池 ④ 逐模型实测。

    返回 (平台结果, {ENV: 目录条目}, 发现结果)
    """
    results: list[dict] = []
    catalogs: dict[str, dict] = {}
    keys: dict[str, str] = {}
    probe_jobs: list[tuple[dict, str, str, dict]] = []
    catalog_jobs: list[tuple[dict, str, str, dict]] = []
    pricing_jobs: list[tuple[dict, dict]] = []
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
            "policy": provider.get("policy") or {},
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
                "note": model.get("note", ""),
                "auto": bool(model.get("auto")),
                "source": "自动发现" if model.get("auto") else "人工登记",
                "status": None,
                "http": None,
                "latency_ms": None,
                "tools": None,
                "tools_note": "",
                "checked_at": checked_at,
            })

        if base_url and provider["models"] and not url_missing:
            if do_probe:
                probe_jobs.append((entry, base_url, provider["models"][0]["id"], provider))
            if do_discover:
                catalog_jobs.append((entry, base_url, key, provider))
                price_src = PRICING_SOURCES.get(key_env)
                if price_src:
                    pricing_jobs.append((entry, price_src))
        elif url_missing:
            entry["probe"] = "skipped"
            entry["probe_note"] = f"缺少环境变量 {', '.join(url_missing)}，地址不完整，无法探测"
            entry["catalog"] = {"ok": False, "count": 0, "public": False,
                                "note": f"缺少环境变量 {', '.join(url_missing)}"}
        results.append(entry)

    # ---- 阶段一 & 二：匿名探活 + 目录同步（并发） ----
    if probe_jobs or catalog_jobs:
        log(f"匿名探活 {len(probe_jobs)} 个平台、同步目录 {len(catalog_jobs)} 个平台"
            f"{'、解析定价页 ' + str(len(pricing_jobs)) + ' 个' if pricing_jobs else ''}…")
        with ThreadPoolExecutor(max_workers=max(1, workers)) as pool:
            p_futures = {pool.submit(probe_platform, bu, mid, pv, timeout): e
                         for e, bu, mid, pv in probe_jobs}
            c_futures = {pool.submit(fetch_catalog, bu, k, pv, timeout): e
                         for e, bu, k, pv in catalog_jobs}
            price_futures = {pool.submit(fetch_pricing_catalog, src["url"], timeout): e
                             for e, src in pricing_jobs}
            for future in as_completed(list(p_futures) + list(c_futures) + list(price_futures)):
                if future in price_futures:
                    entry = price_futures[future]
                    try:
                        out = future.result()
                    except Exception as exc:  # noqa: BLE001
                        out = {"ok": False, "entries": {}, "note": str(exc)}
                    found = out.get("entries", {})
                    if found:
                        merged = dict(catalogs.get(entry["env"]) or {})
                        merged.update(found)      # 定价页数据更准，覆盖 /models 的结果
                        catalogs[entry["env"]] = merged
                        entry["catalog"] = {"ok": True, "count": len(merged),
                                            "public": True, "note": "含公开定价页"}
                        log(f"  💰 [定价页] {entry['name']} 解析出 {len(found)} 个免费模型"
                            f"（含上下文长度）")
                    continue
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
                "note": f"自动发现（{rec['basis']}）",
                "auto": True,
                "source": "自动发现",
                "status": None,
                "http": None,
                "latency_ms": None,
                "tools": None,
                "tools_note": "",
                "checked_at": checked_at,
            })
        newly_adopted.append(rec)
        log(f"  ➕ [自动纳入] {rec['provider']} {rec['model']}（{rec['basis']}）")
    discovery["newly_adopted"] = newly_adopted

    # ---- 阶段四：判定初始状态，能实测的排进队列 ----
    prev_by_env: dict[str, dict] = {}
    for pv in ((previous or {}).get("providers") or []):
        prev_by_env[pv.get("env", "")] = {m.get("id"): m for m in (pv.get("models") or [])}

    rotated_count = 0
    for entry in results:
        cat = catalogs.get(entry["env"]) or {}
        if entry["has_key"]:
            prev_map = prev_by_env.get(entry["env"]) or {}
            pick = select_batch(entry["models"], prev_map, run_index, batch)
            for i, item in enumerate(entry["models"]):
                if i in pick:
                    test_jobs.append((entry, item, entry["base_url"], keys[entry["env"]]))
                    continue
                old = prev_map.get(item["id"])
                rotated_count += 1
                if old:
                    # 去掉历史轮次追加过的后缀，避免每轮无限叠加
                    base_note = re.sub(r"（轮换中，沿用上轮结果）+\s*$", "",
                                       old.get("note") or "").strip()
                    item.update({
                        "status": old.get("status") or "unknown",
                        "http": old.get("http"),
                        "latency_ms": old.get("latency_ms"),
                        "tools": old.get("tools"),
                        "tools_note": old.get("tools_note", ""),
                        "note": (base_note + "（轮换中，沿用上轮结果）").strip(),
                        "rotated": True,
                    })
                else:
                    item.update({"status": "skipped", "http": None, "latency_ms": None,
                                 "tools": None,
                                 "note": "轮换中，本轮未实测", "rotated": True})
        for item in entry["models"]:
            if item["status"] is not None:
                continue
            if cat:
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

    if rotated_count:
        log(f"轮换实测：本轮测 {len(test_jobs)} 个，其余 {rotated_count} 个沿用上轮结果")

    if test_jobs:
        log(f"开始实测 {len(test_jobs)} 个模型（并发 {workers}，超时 {timeout:g}s，重试 {retries} 次）…")
        with ThreadPoolExecutor(max_workers=max(1, workers)) as pool:
            futures = {
                pool.submit(probe_with_tools, base_url, {"id": item["id"]}, key,
                            entry, timeout, retries): (entry, item)
                for entry, item, base_url, key in test_jobs
            }
            for future in as_completed(futures):
                entry, item = futures[future]
                try:
                    outcome = future.result()
                except Exception as exc:  # noqa: BLE001 - 单点失败不影响整体
                    outcome = {"status": "unknown", "http": None, "latency_ms": None,
                               "tools": None, "note": f"{type(exc).__name__}: {exc}"}
                item.update(outcome)
                meta = STATUS_META.get(item["status"], STATUS_META["unknown"])
                tool_icon = TOOLS_META.get(item.get("tools"), ("", ""))[0]
                log(f"  {meta['icon']} [{entry['name']}] {item['id']} "
                    f"-> {item['status']} (HTTP {item.get('http')}) {tool_icon}")

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
# 打分
#   原则：只用「能确证」的维度。缺数据的维度不计入，权重自动重新归一化，
#   并在表里把缺失的维度标出来 —— 绝不用「未知」冒充中位数。
# --------------------------------------------------------------------------- #

SCORE_WEIGHTS = {
    "free_kind": 30,      # 免费性质：长期免费 / 一次性赠送 / 无免费
    "access": 25,         # 中国大陆可用性：能不能拿到 key
    "rate_limit": 20,     # 官方公布的限速宽不宽松
    "context": 15,        # 上下文长度
    "breadth": 10,        # 免费模型数量
}

SCORE_LABELS = {
    "free_kind": "免费性质", "access": "大陆门槛", "rate_limit": "限速",
    "context": "上下文", "breadth": "模型数",
}

FREE_KIND_SCORE = {"长期免费": 10.0, "一次性赠送": 6.0, "无免费": 0.0, "未知": 3.0}
DIFFICULTY_SCORE = {"easy": 10.0, "medium": 7.0, "hard": 3.0, "blocked": 0.0, "unknown": 4.0}


def clean_number(text: object) -> int | None:
    """只接受「就是个数字」的字段。长句子里的数字容易被误读，一律不认。"""
    s = str(text or "").strip()
    if not s or len(s) > 20 or not s[:1].isdigit():
        return None
    m = re.match(r"([\d,]+)\s*$", s)
    if not m:
        return None
    try:
        return int(m.group(1).replace(",", ""))
    except ValueError:
        return None


def _score_rpm(v: int) -> float:
    return 10.0 if v >= 1000 else 8.0 if v >= 100 else 6.0 if v >= 40 else 4.0 if v >= 20 else 2.0


def _score_rpd(v: int) -> float:
    return 10.0 if v >= 10000 else 8.0 if v >= 1000 else 5.0 if v >= 100 else 2.0


def _score_tpd(v: int) -> float:
    return 10.0 if v >= 10_000_000 else 8.0 if v >= 1_000_000 else 5.0 if v >= 100_000 else 2.0


def _score_context(v: int) -> float:
    return (10.0 if v >= 1_000_000 else 8.0 if v >= 262_144 else 7.0 if v >= 131_072
            else 5.0 if v >= 32_768 else 3.0)


def score_provider(entry: dict) -> dict:
    """算一个平台的分数。返回总分、各分项、以及哪些维度缺数据。"""
    pol = entry.get("policy") or {}
    acc = pol.get("access") or {}
    lm = pol.get("limits") or {}
    parts: dict[str, float] = {}
    missing: list[str] = []

    kind = pol.get("free_kind")
    if kind in FREE_KIND_SCORE:
        parts["free_kind"] = FREE_KIND_SCORE[kind]
    else:
        missing.append("免费性质")

    difficulty = acc.get("difficulty_cn")
    if difficulty in DIFFICULTY_SCORE:
        parts["access"] = DIFFICULTY_SCORE[difficulty]
    else:
        missing.append("大陆门槛")

    rates = []
    for field, fn in (("rpm", _score_rpm), ("rpd", _score_rpd), ("tpd", _score_tpd)):
        value = clean_number(lm.get(field))
        if value is not None:
            rates.append(fn(value))
    if rates:
        parts["rate_limit"] = max(rates)
    else:
        missing.append("限速")

    contexts = [m.get("context") for m in entry["models"] if isinstance(m.get("context"), int)]
    if contexts:
        parts["context"] = _score_context(max(contexts))
    else:
        missing.append("上下文")

    count = len(entry["models"])
    parts["breadth"] = min(10.0, count * 2.0) if count else 0.0

    total_weight = sum(SCORE_WEIGHTS[k] for k in parts)
    total = (sum(parts[k] * SCORE_WEIGHTS[k] for k in parts) / total_weight) if total_weight else 0.0
    # 官方按国家封锁的平台，其他维度再好也没意义 —— 直接封顶
    blocked = difficulty == "blocked"
    if blocked:
        total = min(total, 3.0)
    return {
        "score": round(total, 1),
        "parts": {k: round(v, 1) for k, v in parts.items()},
        "missing": missing,
        "used_weight": total_weight,
        "blocked": blocked,
    }


def score_label(score: float, blocked: bool = False) -> str:
    if blocked:
        return "⛔ 不可用"
    return ("🟢 推荐" if score >= 7.5 else "🟡 可用" if score >= 5.5
            else "🟠 一般" if score >= 3.5 else "🔴 不建议")


# --------------------------------------------------------------------------- #
# 可选的 SOCKS5 代理支持
#   中国大陆本地直连国外平台常被 TLS 重置；把 socket.create_connection 接管掉，
#   urllib 和 ssl 都不用改。GitHub Actions 上直连即可，不需要开。
# --------------------------------------------------------------------------- #

def socks5_socket(proxy_host: str, proxy_port: int, dest_host: str, dest_port: int,
                  timeout: float) -> socket.socket:
    """手写 SOCKS5 握手，避免引入 PySocks 依赖。"""
    sock = socket.create_connection((proxy_host, proxy_port), timeout)
    sock.settimeout(timeout)
    sock.sendall(b"\x05\x01\x00")                     # 版本 5，一种方法：无认证
    if sock.recv(2) != b"\x05\x00":
        sock.close()
        raise OSError("SOCKS5 代理拒绝无认证连接")
    host = dest_host.encode("idna")
    sock.sendall(b"\x05\x01\x00\x03" + bytes([len(host)]) + host
                 + int(dest_port).to_bytes(2, "big"))
    head = sock.recv(4)
    if len(head) < 4 or head[1] != 0:
        sock.close()
        raise OSError(f"SOCKS5 连接失败（返回码 {head[1] if len(head) > 1 else '?'}）")
    atyp = head[3]
    if atyp == 1:
        sock.recv(4)
    elif atyp == 3:
        sock.recv(sock.recv(1)[0])
    elif atyp == 4:
        sock.recv(16)
    sock.recv(2)
    return sock


def enable_socks_proxy(proxy: str) -> str:
    """把 socket.create_connection 接管成走 SOCKS5。返回一句话说明，便于日志确认。"""
    match = re.match(r"socks5h?://([^:/]+):(\d+)", (proxy or "").strip())
    if not match:
        return ""
    proxy_host, proxy_port = match.group(1), int(match.group(2))
    original = socket.create_connection

    def patched(address, *args, **kwargs):
        host, port = address[0], address[1]
        if host in ("127.0.0.1", "localhost", "::1"):
            return original(address, *args, **kwargs)
        timeout = kwargs.get("timeout")
        if timeout is None and args:
            timeout = args[0]
        return socks5_socket(proxy_host, proxy_port, host, port, timeout or 30)

    socket.create_connection = patched
    return f"已启用 SOCKS5 代理 {proxy_host}:{proxy_port}（本地地址仍直连）"


# --------------------------------------------------------------------------- #
# 外部清单源 与 官方文档变更检测
#   政策数字很难解析，但「页面变了」很容易检测 —— 存一个内容摘要就够。
#   页面一变就报警，然后人工去看，把「永远追不上」变成「只在变化时追」。
# --------------------------------------------------------------------------- #

EXTERNAL_SOURCES = [
    {"name": "Cline 模型目录", "url": "https://api.cline.bot/api/v1/models",
     "note": "Cline 用量计费通道的目录；实测与 OpenRouter 一致（464 个），用来交叉验证"},
    {"name": "HuggingFace Router 目录", "url": "https://router.huggingface.co/v1/models",
     "kind": "hf_router",
     "note": "HF 聚合 15+ 家供应商的实时路由目录，匿名即可读，每个「模型×供应商」组合自带定价、"
             "supports_tools、上下文。is_free 或定价 0/0 的 live 组合记为「0 元组合」，"
             "是发现「谁家又上新免费模型」最灵敏的传感器；调用本身走 HF 免费账号每月 $0.10 额度"},
]


def parse_hf_router(body: str) -> tuple[list[str], dict[str, bool]]:
    """解析 HF router 目录：返回 (模型ID列表, {模型@供应商: 是否支持工具调用})。

    0 元组合的判定和 HF 自己的口径一致：is_free=true，或定价 input/output 均为 0。
    """
    data = json.loads(body)
    items = data.get("data") if isinstance(data, dict) else data
    ids: list[str] = []
    free_pairs: dict[str, bool] = {}
    for m in items or []:
        if not isinstance(m, dict) or not m.get("id"):
            continue
        ids.append(str(m["id"]))
        for p in m.get("providers") or []:
            if not isinstance(p, dict) or p.get("status") != "live":
                continue
            pr = p.get("pricing") or {}
            if p.get("is_free") or (pr.get("input") == 0 and pr.get("output") == 0):
                free_pairs[f"{m['id']}@{p.get('provider')}"] = bool(p.get("supports_tools"))
    return sorted(ids), dict(sorted(free_pairs.items()))


DOC_WATCH = [
    {"name": "OpenRouter 限流", "url": "https://openrouter.ai/docs/api_reference/limits"},
    {"name": "Groq 限流", "url": "https://console.groq.com/docs/rate-limits"},
    {"name": "Gemini 限流", "url": "https://ai.google.dev/gemini-api/docs/rate-limits"},
    {"name": "Gemini 定价", "url": "https://ai.google.dev/gemini-api/docs/pricing"},
    {"name": "Cerebras 限流", "url": "https://inference-docs.cerebras.ai/support/rate-limits"},
    {"name": "Cloudflare 定价", "url": "https://developers.cloudflare.com/workers-ai/platform/pricing/"},
    {"name": "SambaNova 限流", "url": "https://docs.sambanova.ai/docs/en/models/rate-limits"},
    {"name": "Mistral 价格", "url": "https://mistral.ai/pricing"},
    {"name": "Cline 免费模型", "url": "https://docs.cline.bot/getting-started/free-models.md"},
    {"name": "智谱限流", "url": "https://docs.bigmodel.cn/cn/api/rate-limit"},
    {"name": "智谱价格", "url": "https://docs.bigmodel.cn/cn/guide/start/pricing"},
    {"name": "Kimi 限流", "url": "https://platform.kimi.com/docs/pricing/limits"},
    {"name": "MiniMax 限流", "url": "https://platform.minimaxi.com/docs/guides/rate-limits.md"},
    {"name": "硅基流动限流", "url": "https://api-docs.siliconflow.cn/docs/userguide/faqs/rate-limit-and-upgradation"},
    {"name": "阶跃星辰定价", "url": "https://platform.stepfun.com/docs/pricing/details"},
    {"name": "百川限流", "url": "https://platform.baichuan-ai.com/docs-v2/rate-limit"},
]

SOURCES_FILE = "sources.json"


def fetch_raw(url: str, timeout: float) -> tuple[bool, str, str]:
    """返回（成功, 内容, 说明）。"""
    request = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "*/*"})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as resp:
            return True, resp.read(4 * 1024 * 1024).decode("utf-8", "replace"), ""
    except urllib.error.HTTPError as exc:
        return False, "", f"HTTP {exc.code}"
    except Exception as exc:  # noqa: BLE001
        return False, "", shorten(f"{type(exc).__name__}: {exc}")


def text_digest(text: str) -> tuple[str, int]:
    """归一化后取内容摘要：去掉脚本/样式/标签和多余空白，降低噪声。"""
    body = re.sub(r"<script.*?</script>|<style.*?</style>", " ", text, flags=re.S | re.I)
    body = html_unescape(re.sub(r"<[^>]+>", " ", body))
    body = re.sub(r"\s+", " ", body).strip()
    return hashlib.sha1(body.encode("utf-8", "replace")).hexdigest()[:16], len(body)


def load_sources(path: Path) -> dict:
    data = read_json(path)
    if not isinstance(data, dict):
        return {"external": {}, "docs": {}}
    data.setdefault("external", {})
    data.setdefault("docs", {})
    return data


def check_external_sources(state: dict, timeout: float, workers: int) -> tuple[dict, list[dict]]:
    """抓外部清单，和上次的模型 ID 列表对比。"""
    report: list[dict] = []
    if not EXTERNAL_SOURCES:
        return state, report

    def job(src):
        ok, body, note = fetch_raw(src["url"], timeout)
        if not ok:
            return src, None, None, {}, note
        try:
            if src.get("kind") == "hf_router":
                ids, free_pairs = parse_hf_router(body)
            else:
                data = json.loads(body)
                items = data.get("data") if isinstance(data, dict) else data
                if not isinstance(items, list):
                    return src, None, None, {}, "结构无法识别"
                ids = sorted(str(m.get("id")) for m in items
                             if isinstance(m, dict) and m.get("id"))
                free_pairs = {}
        except ValueError:
            return src, None, None, {}, "返回的不是 JSON"
        digest_src = ids + [f"{k}={int(v)}" for k, v in free_pairs.items()]
        return src, ids, hashlib.sha1("\n".join(digest_src).encode()).hexdigest()[:16], \
            free_pairs, ""

    with ThreadPoolExecutor(max_workers=max(1, workers)) as pool:
        for src, ids, digest, free_pairs, note in pool.map(job, EXTERNAL_SOURCES):
            old = state["external"].get(src["url"]) or {}
            rec = {"name": src["name"], "url": src["url"], "note": src.get("note", ""),
                   "count": len(ids) if ids else 0, "added": [], "removed": [],
                   "free_count": len(free_pairs), "free_pairs": free_pairs,
                   "free_added": [], "free_removed": [],
                   "changed": False, "error": note,
                   "checked_at": datetime.now(CST).strftime("%Y-%m-%d %H:%M")}
            if ids is not None:
                old_ids = set(old.get("ids") or [])
                if old_ids:
                    rec["added"] = sorted(set(ids) - old_ids)
                    rec["removed"] = sorted(old_ids - set(ids))
                old_free = old.get("free_pairs") or {}
                if old_free:
                    rec["free_added"] = sorted(set(free_pairs) - set(old_free))
                    rec["free_removed"] = sorted(set(old_free) - set(free_pairs))
                rec["changed"] = bool(rec["added"] or rec["removed"]
                                      or rec["free_added"] or rec["free_removed"])
                state["external"][src["url"]] = {
                    "name": src["name"], "count": len(ids), "hash": digest,
                    "ids": ids, "free_pairs": free_pairs,
                    "checked_at": rec["checked_at"], "note": src.get("note", ""),
                }
            report.append(rec)
    return state, report


def check_doc_watch(state: dict, timeout: float, workers: int) -> tuple[dict, list[dict]]:
    """抓文档页，比对内容摘要；变了就记一笔。"""
    report: list[dict] = []
    if not DOC_WATCH:
        return state, report
    now = datetime.now(CST).strftime("%Y-%m-%d %H:%M")

    def job(doc):
        ok, body, note = fetch_raw(doc["url"], timeout)
        if not ok:
            return doc, None, 0, note
        digest, size = text_digest(body)
        return doc, digest, size, ""

    with ThreadPoolExecutor(max_workers=max(1, workers)) as pool:
        for doc, digest, size, note in pool.map(job, DOC_WATCH):
            old = state["docs"].get(doc["url"]) or {}
            rec = {"name": doc["name"], "url": doc["url"], "changed": False,
                   "last_changed": old.get("last_changed", ""), "size": size,
                   "first_seen": old.get("first_seen", now), "error": note}
            if digest is not None:
                if old.get("hash") and old["hash"] != digest:
                    rec["changed"] = True
                    rec["last_changed"] = now
                elif not old.get("hash"):
                    rec["last_changed"] = ""      # 第一次见到，算基线，不算变更
                else:
                    rec["last_changed"] = old.get("last_changed", "")
                state["docs"][doc["url"]] = {
                    "name": doc["name"], "hash": digest, "size": size,
                    "last_changed": rec["last_changed"],
                    "first_seen": rec["first_seen"], "checked_at": now,
                }
            else:
                rec["last_changed"] = old.get("last_changed", "")
            report.append(rec)
    return state, report


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
        writer.writerow(["平台", "综合分", "评价", "接口探活", "免费性质", "大陆门槛",
                         "RPM", "RPD", "TPM", "TPD", "重置",
                         "手机号", "实名认证", "外币卡", "政策来源数", "政策核实日",
                         "密钥变量名", "模型ID", "来源", "BaseURL", "上下文",
                         "状态", "状态码", "工具调用", "延迟(ms)", "备注", "检测时间"])
        for provider in providers:
            probe = PROBE_META.get(provider.get("probe", "skipped"), PROBE_META["skipped"])
            probe_text = f"{probe['icon']} {probe['label']}"
            pol = provider.get("policy") or {}
            lm = pol.get("limits") or {}
            sg = pol.get("signup") or {}
            signup_cn = {"required": "需要", "not_required": "不需要", "unknown": "未知"}
            for model in provider["models"]:
                meta = STATUS_META.get(model["status"], STATUS_META["unknown"])
                writer.writerow([
                    provider["name"], provider.get("score", "-"),
                    score_label(provider["score"], (provider.get("score_detail") or {}).get("blocked")) if provider.get("score") is not None else "-",
                    probe_text, pol.get("free_kind", "-"),
                    ((pol.get("access") or {}).get("difficulty_cn") or "-"),
                    lm.get("rpm", "-"), lm.get("rpd", "-"), lm.get("tpm", "-"), lm.get("tpd", "-"),
                    lm.get("reset", "-"),
                    signup_cn.get(sg.get("phone"), "-"),
                    signup_cn.get(sg.get("realname"), "-"),
                    signup_cn.get(sg.get("foreign_card"), "-"),
                    len(pol.get("sources") or []), pol.get("verified_at", "-"),
                    provider["env"], model["id"],
                    model.get("source", "人工登记"), provider["base_url"],
                    fmt_context(model.get("context")), f"{meta['icon']} {meta['label']}",
                    model.get("http") if model.get("http") is not None else "-",
                    tools_label(model.get("tools")),
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


# --------------------------------------------------------------------------- #
# 可用性时间线 uptime.jsonl
#   每轮巡检追加一行，用来回答文档回答不了的问题：
#   「哪个平台在哪个时段容易被限流」「额度大概几点重置」
# --------------------------------------------------------------------------- #

UPTIME_KEEP = 2190            # 每 8 小时一轮 => 约两年
PROBE_SHORT = {"online": "on", "open": "op", "unstable": "un", "gone": "go",
               "unreachable": "ur", "unknown": "uk", "skipped": "sk"}
PROBE_SHORT_BACK = {v: k for k, v in PROBE_SHORT.items()}


def load_uptime(path: Path) -> list[dict]:
    if not path.exists():
        return []
    out: list[dict] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            try:
                out.append(json.loads(line))
            except ValueError:
                continue
    return out


def append_uptime(path: Path, record: dict, keep: int = UPTIME_KEEP) -> None:
    lines: list[str] = []
    if path.exists():
        lines = [ln for ln in path.read_text(encoding="utf-8").splitlines() if ln.strip()]
    lines.append(json.dumps(record, ensure_ascii=False, separators=(",", ":")))
    write_text_lf(path, "\n".join(lines[-keep:]) + "\n")


def build_uptime_record(results: list[dict], generated_at: datetime) -> dict:
    """一行一次巡检。每平台记：探活状态 + 限流数 + 实测成功数 + 目录确认数 + 目录消失数 + 密钥错误数。"""
    providers: dict[str, list] = {}
    for entry in results:
        counts = {"rl": 0, "ok": 0, "co": 0, "ms": 0, "au": 0}
        for model in entry["models"]:
            status = model["status"]
            if status == "ok":
                counts["ok"] += 1
            elif status == "rate_limited":
                counts["rl"] += 1
            elif status == "auth_error":
                counts["au"] += 1
            elif status in ("missing", "not_found"):
                counts["ms"] += 1
            elif status == "catalog_only":
                counts["co"] += 1
        providers[entry["env"]] = [
            PROBE_SHORT.get(entry.get("probe", "skipped"), "uk"),
            counts["rl"], counts["ok"], counts["co"], counts["ms"], counts["au"],
        ]
    return {"t": generated_at.strftime("%Y-%m-%d %H:%M"),
            "h": generated_at.hour, "w": generated_at.weekday(),
            "p": providers}


def summarize_uptime(records: list[dict], providers: list[dict]) -> dict:
    """按平台聚合时间线：巡检轮次、限流累计、实测成功累计、最容易限流的时段。"""
    name_of = {p["env"]: p["name"] for p in providers}
    agg: dict[str, dict] = {}
    for rec in records:
        hour = rec.get("h")
        for env, val in (rec.get("p") or {}).items():
            if not isinstance(val, list) or len(val) < 6:
                continue
            a = agg.setdefault(env, {"runs": 0, "rl": 0, "ok": 0, "co": 0, "ms": 0,
                                     "au": 0, "bad_probe": 0, "hours": {}})
            a["runs"] += 1
            a["rl"] += val[1]
            a["ok"] += val[2]
            a["co"] += val[3]
            a["ms"] += val[4]
            a["au"] += val[5]
            if PROBE_SHORT_BACK.get(val[0], "unknown") in ("gone", "unreachable", "unstable", "unknown"):
                a["bad_probe"] += 1
            if val[1]:
                a["hours"][hour] = a["hours"].get(hour, 0) + val[1]

    rows = []
    for env, a in agg.items():
        peak = max(a["hours"].items(), key=lambda kv: kv[1])[0] if a["hours"] else None
        rows.append({"env": env, "name": name_of.get(env, env), "runs": a["runs"],
                     "rate_limited": a["rl"], "ok": a["ok"], "catalog_only": a["co"],
                     "missing": a["ms"], "auth_error": a["au"],
                     "probe_bad": a["bad_probe"], "peak_hour": peak})
    rows.sort(key=lambda r: (-r["rate_limited"], -r["ok"], r["name"]))
    return {"records": len(records),
            "since": records[0].get("t", "") if records else "",
            "until": records[-1].get("t", "") if records else "",
            "providers": rows}


def render_readme(providers: list[dict], summary: dict, changes: list[dict],
                  generated_at: datetime, elapsed: float, cron: str, history: list[dict],
                  discovery: dict | None = None, adopt_mode: str = "safe",
                  uptime: dict | None = None, sources_report: dict | None = None) -> str:
    discovery = discovery or {}
    uptime = uptime or {}
    sources_report = sources_report or {}
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
    add("自动巡检各大平台免费大模型接口的可用性，每 8 小时更新一次。")
    add("密钥只存放在 GitHub Secrets 中，脚本不落地、不外传，仓库里只留下状态结果。")
    add("")
    add("---")
    add("")
    add("## ⚠️ 先读这段，能帮你省钱")
    add("")
    add("**这些免费额度适合「轻量调用」，不适合「驱动 AI 编程工具」。**")
    add("")
    add("2026-10-01 实测结论：把免费模型接到 **DSH / Cline / Roo Code** 这类 agent 工具上，")
    add("**8B 到 72B 全线失败**。它们能通过「能调用工具」的单次测试，但撑不住真实的 agent 场景")
    add("（几万 token 的系统提示词 + 反复多轮工具调用）。典型表现：输出格式跑偏、中途吐空、")
    add("被限速截断、或直接报工具错误。")
    add("")
    add("| 用途 | 免费额度够吗 |")
    add("| --- | --- |")
    add("| 单独问问题、看段代码、翻译、写小片段 | ✅ **完全够用** |")
    add("| 让 agent 自主读写文件、跑命令、多步完成任务 | ❌ **请用付费 API** |")
    add("")
    add("**别为了省这点钱，花一整天去试错。** 这份清单的价值是告诉你")
    add("「谁还有免费额度、额度多少、怎么申请、卡在哪」，**不是承诺它们能干重活**。")
    add("")
    add("> 我们踩过的坑，你不用再踩一遍：清单上标着「免费」的模型，实测可能是")
    add("> 「账户余额不足」「只对特定用户开放」「不支持工具调用」——")
    add("> 这些只有真调用才知道，本仓库的巡检就是在做这件事。")
    add("")
    add("---")
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
    add("| 平台 | 接口探活 | 模型状态 | 免费性质 | 大陆可用性 | 密钥变量 | 目录 | 申请地址 |")
    add("| --- | --- | --- | --- | --- | --- | ---: | --- |")
    for provider in providers:
        console = f"[控制台]({provider['console']})" if provider["console"] else "-"
        probe = PROBE_META.get(provider.get("probe", "skipped"), PROBE_META["skipped"])
        cat = provider.get("catalog") or {}
        if cat.get("ok"):
            catalog_cell = f"{cat['count']}" + ("（公开）" if cat.get("public") else "")
        else:
            catalog_cell = "-"
        pol = provider.get("policy") or {}
        kind = pol.get("free_kind", "-")
        diff = (pol.get("access") or {}).get("difficulty_cn")
        diff_cell = (f"{DIFFICULTY_META[diff]['icon']} {DIFFICULTY_META[diff]['label']}"
                     if diff in DIFFICULTY_META else "-")
        add(f"| {provider['name']} | {probe['icon']} {probe['label']} | "
            f"{status_cell(provider['status'])} {provider['available']}/{provider['total']} | "
            f"{kind} | {diff_cell} | "
            f"`{provider['env']}` | {catalog_cell} | {console} |")
    add("")

    # ---------------- 免费政策与限流（官方核实数据） ----------------
    with_policy = [p for p in providers if (p.get("policy") or {}).get("limits")]
    if with_policy:
        add("## 免费政策与限流")
        add("")
        add("这一节是**人工核实的官方数据**，不是实测值 —— 全部来自研究员实际读到的官方页面，")
        add("查不到的一律写「未公布」。核实日期见末列，来源链接在 `providers.json` 里。")
        add("")
        add("| 平台 | 免费性质 | RPM | RPD | TPM | TPD | 并发 | 重置 | 闲时/忙时 | 手机号 | 实名 | 外币卡 | 置信度 | 核实日 |")
        add("| --- | --- | ---: | ---: | ---: | ---: | ---: | --- | --- | :-: | :-: | :-: | :-: | --- |")
        need = {"required": "✅", "not_required": "—", "unknown": "?"}
        for p in sorted(with_policy, key=lambda x: (x.get("policy") or {}).get("free_kind", "")):
            pol = p["policy"]
            lm = pol.get("limits") or {}
            sg = pol.get("signup") or {}
            add(f"| {p['name']} | {pol.get('free_kind', '-')} | "
                f"{lm.get('rpm', '-')} | {lm.get('rpd', '-')} | {lm.get('tpm', '-')} | "
                f"{lm.get('tpd', '-')} | {lm.get('concurrency', '-')} | "
                f"{lm.get('reset', '-')} | {lm.get('time_window', '-')} | "
                f"{need.get(sg.get('phone'), '?')} | {need.get(sg.get('realname'), '?')} | "
                f"{need.get(sg.get('foreign_card'), '?')} | {pol.get('confidence', '?')} | "
                f"{pol.get('verified_at', '-')} |")
        add("")
        add("> 门槛列：✅ = 需要，— = 不需要，? = 官方页面未说明。")
        add("> 「未公布」不代表没有限制 —— 大部分平台的限速数字只在登录后的控制台可见。")
        add("")

    # ---------------- 中国大陆可用性 ----------------
    with_access = [p for p in providers if (p.get("policy") or {}).get("access")]
    if with_access:
        add("## 中国大陆可用性")
        add("")
        add("这一节回答的是「**身在墙内能不能拿到并调用它**」，数据来自官方条款与实测。")
        add("对我们来说，**地区封锁和非中国出口往往比外币卡更早成为障碍**。")
        add("")
        add("| 平台 | 拿到密钥的难度 | 原因 | 封锁大陆 | 需非中国出口 | 拿免费额度要绑卡 |")
        add("| --- | --- | --- | :-: | :-: | :-: |")
        yn = {"yes": "⛔ 是", "no": "—", "unknown": "?"}
        rank = {"easy": 0, "medium": 1, "hard": 2, "blocked": 3, "unknown": 4}
        for p in sorted(with_access,
                        key=lambda x: rank.get(((x["policy"]["access"]) or {}).get("difficulty_cn"), 9)):
            acc = p["policy"]["access"]
            diff = acc.get("difficulty_cn")
            cell = (f"{DIFFICULTY_META[diff]['icon']} {DIFFICULTY_META[diff]['label']}"
                    if diff in DIFFICULTY_META else "-")
            region = acc.get("region") or {}
            pay = acc.get("payment") or {}
            reason = (acc.get("difficulty_reason") or "").replace("|", "\\|")
            if len(reason) > 60:
                reason = reason[:59] + "…"
            add(f"| {p['name']} | {cell} | {reason} | "
                f"{yn.get(region.get('blocks_china'), '?')} | "
                f"{yn.get(region.get('needs_non_cn_ip'), '?')} | "
                f"{yn.get(pay.get('card_required_to_get_free'), '?')} |")
        add("")
        blocked = [p["name"] for p in with_access
                   if (p["policy"]["access"] or {}).get("difficulty_cn") == "blocked"]
        if blocked:
            add(f"> ⛔ **官方按国家/地区封锁中国大陆**：{'、'.join(blocked)}。这不是「难申请」，是根本进不去。")
            add("")

    # ---------------- 平台打分 ----------------
    scored = [p for p in providers if p.get("score") is not None]
    if scored:
        add("## 平台打分")
        add("")
        add("**打分原则：只用能确证的维度。** 缺数据的维度不计入总分，权重会自动重新归一化，")
        add("并在末列标出缺了什么 —— 我们没有用「未知」去冒充中位数。")
        add("")
        w = " / ".join(f"{SCORE_LABELS[k]} {v}" for k, v in SCORE_WEIGHTS.items())
        add(f"权重：{w}（满分 10）")
        add("")
        add("| # | 平台 | 综合分 | 评价 | 免费性质 | 大陆门槛 | 限速 | 上下文 | 模型数 | 缺数据 |")
        add("| ---: | --- | ---: | --- | ---: | ---: | ---: | ---: | ---: | --- |")
        for i, p in enumerate(sorted(scored, key=lambda x: -x["score"]), 1):
            det = p["score_detail"]
            parts = det.get("parts") or {}
            cell = lambda k: (f"{parts[k]:.1f}" if k in parts else "—")  # noqa: E731
            miss = "、".join(det.get("missing") or []) or "-"
            add(f"| {i} | {p['name']} | **{p['score']:.1f}** | {score_label(p['score'], (p.get('score_detail') or {}).get('blocked'))} | "
                f"{cell('free_kind')} | {cell('access')} | {cell('rate_limit')} | "
                f"{cell('context')} | {cell('breadth')} | {miss} |")
        add("")
        add("> **这个分数衡量的是「白嫖的性价比」，不是模型有多聪明。**")
        add("> 「限速」和「上下文」两列出现 `—` 是因为官方没有公布数值或没登记上下文，")
        add("> 不是它们不重要 —— 只是我们拒绝用猜的数字打分。")
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

    # ---------------- 外部清单与官方文档变更 ----------------
    ext = sources_report.get("external") or []
    docs = sources_report.get("docs") or []
    if ext or docs:
        add("## 外部清单与官方文档变更")
        add("")
        add("政策数字很难自动解析，但**「页面变了」很容易检测**。这一节只做变更提醒，不做解读。")
        add("")

    if ext:
        add("### 别家清单的变化")
        add("")
        add("| 来源 | 模型数 | 本轮变化 |")
        add("| --- | ---: | --- |")
        for rec in ext:
            if rec.get("error"):
                cell = f"抓取失败：{rec['error']}"
            elif rec.get("changed"):
                bits = []
                if rec.get("added"):
                    bits.append(f"➕ {len(rec['added'])} 个")
                if rec.get("removed"):
                    bits.append(f"➖ {len(rec['removed'])} 个")
                cell = "、".join(bits)
                sample = (rec.get("added") or [])[:3] or (rec.get("removed") or [])[:3]
                if sample:
                    cell += "：" + "、".join(f"`{x}`" for x in sample)
            else:
                cell = "无变化"
            if rec.get("free_count"):
                pair_txt = f"；🟢 0 元组合 {rec['free_count']} 个"
                if rec.get("free_added") or rec.get("free_removed"):
                    pair_txt += (f"（新增 {len(rec['free_added'])}、消失 "
                                 f"{len(rec['free_removed'])}）")
                cell += pair_txt
            add(f"| {rec['name']} | {rec.get('count', 0)} | {cell} |")
        add("")
        hf = next((r for r in ext if r.get("free_pairs")), None)
        if hf:
            add(f"**{hf['name']}当前的 0 元（live）组合**（✅=该供应商标注支持工具调用）：")
            add("")
            for pair, supports in list(hf["free_pairs"].items())[:15]:
                add(f"- {'✅' if supports else '❔'} `{pair}`")
            add("")
        for rec in ext:
            if rec.get("note"):
                add(f"> {rec['name']}：{rec['note']}")
        if any(r.get("note") for r in ext):
            add("")

    if docs:
        changed = [r for r in docs if r.get("changed")]
        add("### 官方文档页变更提醒")
        add("")
        if changed:
            add("**这些页面本轮内容变了，政策可能已经调整，建议去看一眼：**")
            add("")
            add("| 页面 | 变更时间 | 链接 |")
            add("| --- | --- | --- |")
            for rec in changed:
                add(f"| {rec['name']} | {rec.get('last_changed', '-')} | [打开]({rec['url']}) |")
            add("")
        else:
            add(f"本轮 {len(docs)} 个官方页面都没有变化。")
            add("")
        failed = [r for r in docs if r.get("error")]
        fresh = [r for r in docs if not r.get("last_changed") and not r.get("error")]
        if fresh:
            add(f"> 有 {len(fresh)} 个页面是第一次抓取，本轮只建立基线，不算变更。")
        if failed:
            add(f"> 有 {len(failed)} 个页面本轮抓取失败（{', '.join(r['name'] for r in failed[:5])}"
                f"{' 等' if len(failed) > 5 else ''}），不影响其他检测。")
        add("")
        add(f"共监控 {len(docs)} 个页面，摘要存放在 `sources.json`。")
        add("")

    # ---------------- 可用性时间线 ----------------
    up_rows = uptime.get("providers") or []
    if uptime.get("records", 0) >= 3:
        add("## 可用性时间线（自动累积）")
        add("")
        add(f"已累积 **{uptime['records']}** 次巡检（{uptime.get('since', '')} 起）。"
            "这一节是为了回答文档回答不了的问题：**哪个平台在哪个时段容易被限流**。")
        add("")
        add("| 平台 | 巡检轮次 | 实测成功累计 | 限流(429)累计 | 探活异常 | 最容易限流的时段 |")
        add("| --- | ---: | ---: | ---: | ---: | --- |")
        for row in up_rows[:20]:
            peak = (f"{row['peak_hour']:02d}:00 前后"
                    if row.get("peak_hour") is not None else "-")
            add(f"| {row['name']} | {row['runs']} | {row['ok']} | {row['rate_limited']} | "
                f"{row['probe_bad']} | {peak} |")
        add("")
        add("> **没配密钥的平台，限流列会一直是 0** —— 429 只有真正调用时才会出现，")
        add("> 匿名探活看不到它。想让这一节有数据，配一个密钥就行。")
        add("> 时段按北京时间（UTC+8）统计，每 8 小时一个采样点，数据越攒越准。")
        add("")

    add("## 模型明细")
    add("")
    agent_ready = [(p["name"], m) for p in providers for m in p["models"]
                   if m.get("tools") == "yes" and m.get("status") == "ok"]
    if agent_ready:
        add(f"### 🔧 工具调用实测通过的免费模型（{len(agent_ready)} 个）")
        add("")
        add("下面这些模型在真实请求里**端到端吐出了 `tool_calls`**，具备驱动 "
            "DSH / Cline / Roo 的**基本能力**（轻量任务可直接用；真实 agent 长跑仍受顶部警告里的")
        add("免费额度/限速约束，重活请上付费 API）：")
        add("")
        add("| 平台 | 模型 ID | 上下文 |")
        add("| --- | --- | ---: |")
        for name, m in agent_ready:
            add(f"| {name} | `{m['id']}` | {fmt_context(m.get('context'))} |")
        add("")
        add("> 判定方法：带 `tools` + `tool_choice=required` 发真实请求，返回里必须带原生 "
            "`tool_calls`。`〽️ 收参不吐调用` 的模型接口不报错但 agent 接不住，不要用；")
        add("> 思考型模型偶发「这轮调、下轮不调」，结论按最近一次实测滚动更新。")
        add("")
    add("| 平台 | 模型 ID | 来源 | 上下文 | 状态 | 工具调用 | HTTP | 延迟 | 备注 |")
    add("| --- | --- | --- | ---: | --- | --- | ---: | ---: | --- |")
    for provider in providers:
        for model in provider["models"]:
            note = (model.get("note", "") or "").replace("|", "\\|")
            add(f"| {provider['name']} | `{model['id']}` | {model.get('source', '人工登记')} | "
                f"{fmt_context(model.get('context'))} | "
                f"{status_cell(model['status'])} | "
                f"{tools_label(model.get('tools'))} | "
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
    add("   之后每 8 小时会自动更新，也可以在触发时填 `only` 只检查某几个平台。")
    add("")
    add("> 想降低提交频率，把 `.github/workflows/update.yml` 里的 `cron` 改成 `0 2 * * *`（每天一次）即可。")
    add("")
    add("## 自动更新原理")
    add("")
    add("GitHub Actions 每 8 小时启动一次云环境，运行 `update_list.py`，全程不需要服务器。")
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
    add("   几乎不消耗免费额度，按返回码判定可用性；可用的模型再带 `tools` 发一条真实请求，")
    add("   只有返回里**真的吐出 `tool_calls`** 才标 🔧 —— 这才是 agent（DSH/Cline/Roo）能用的模型。")
    add("   为省额度每轮只抽测一批，各模型轮流上，结论跨轮保留。")
    add("5. **看外部清单**：拉别家维护的模型目录（Cline 清单、HuggingFace Router），和上一轮比对，")
    add("   有增删、有新的 0 元组合就记下来 —— 用别人的清单当传感器。")
    add("6. **盯官方文档**：把十几个官方限流/定价页抓一遍，**只比对内容摘要，不解析数字**。")
    add("   页面一变就报警，然后人工去看一眼。政策数字难解析，但「页面变了」很容易检测。")
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
    add("| `providers.json` | 平台与模型清单 + 官方核实的政策数据（人工维护，改清单不用碰代码） |")
    add("| `models.auto.json` | **脚本自己维护**的自动纳管模型池（确证免费的才进，连续失败自动剔除） |")
    add("| `sources.json` | 外部清单的模型 ID 快照 + 官方文档页的内容摘要（用来做变更检测） |")
    add("| `history.jsonl` | 状态**变化**历史，一行一次变更快照 |")
    add("")
    add("三层模型池的关系：")
    add("")
    add("| 文件 | 谁写 | 作用 |")
    add("| --- | --- | --- |")
    add("| `providers.json` | 人工 | 骨架：平台地址、申请入口、模型清单、官方政策数据 |")
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
    add("也可以直接改 `providers.json` —— 平台与模型清单已经和代码分开了，改清单不用碰脚本。")
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
    add("| 平台是 ❌ 接口已失效 | 该平台的接口路径返回 404，可能已下线或改地址，需要改 `providers.json` 里的 `base_url` |")
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
    parser.add_argument("--timeout", type=float, default=45.0,
                        help="单次请求超时秒数，默认 45（部分平台 TLS 握手就要 20 秒以上）")
    parser.add_argument("--retries", type=int, default=2, help="网络错误/5xx 重试次数，默认 2")
    parser.add_argument("--workers", type=int, default=6, help="并发数，默认 6")
    parser.add_argument("--out-dir", default=".", help="输出目录，默认脚本所在目录")
    parser.add_argument("--cron", default="0 */8 * * *", help="写入 README 的巡检频率展示值")
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
    parser.add_argument("--proxy", default=os.environ.get("FREE_LLM_PROXY", ""),
                        help="可选 SOCKS5 代理，形如 socks5h://127.0.0.1:10808。"
                             "中国大陆本地直连国外平台常被重置时用得上；Actions 上不需要")
    parser.add_argument("--sources-file", default=SOURCES_FILE,
                        help="外部清单与文档摘要的状态文件，默认 sources.json")
    parser.add_argument("--probe-batch", type=int, default=3,
                        help="每个平台每轮最多实测几个模型（按轮次轮换），默认 3；"
                             "填 0 表示不轮换、每轮全测。调小它能省下你的免费额度")
    parser.add_argument("--docs", action=argparse.BooleanOptionalAction, default=True,
                        help="是否检测官方文档页有没有变化，默认开启")
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

    if args.proxy:
        note = enable_socks_proxy(args.proxy)
        log(note or f"代理地址无法识别，已忽略：{args.proxy}")

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
    uptime_path = out_dir / "uptime.jsonl"
    sources_path = Path(args.sources_file)
    if not sources_path.is_absolute():
        sources_path = ROOT / sources_path

    previous = read_json(json_path)
    started = time.perf_counter()
    generated_at = datetime.now(CST)
    checked_at = generated_at.strftime("%Y-%m-%d %H:%M:%S")

    run_index = len(load_uptime(out_dir / "uptime.jsonl"))

    # ---- 外部清单源 + 官方文档变更检测 ----
    sources_state = load_sources(sources_path)
    sources_state, external_report = check_external_sources(
        sources_state, args.timeout, args.workers)
    if args.docs:
        sources_state, doc_report = check_doc_watch(sources_state, args.timeout, args.workers)
    else:
        doc_report = []
    sources_state["updated_at"] = checked_at
    sources_state["note"] = ("外部清单的模型 ID 快照 + 官方文档页的内容摘要。"
                             "由 update_list.py 自动维护，用来发现「别家清单变了」和「官方政策页改了」。")
    write_json(sources_path, sources_state)
    changed_src = [r for r in external_report if r.get("changed")]
    changed_doc = [r for r in doc_report if r.get("changed")]
    if changed_src:
        log(f"外部清单有变化：{len(changed_src)} 个")
    if changed_doc:
        log(f"官方文档页有变化：{len(changed_doc)} 个 —— {', '.join(r['name'] for r in changed_doc)}")
    source_report = {"external": external_report, "docs": doc_report}

    results, catalogs, discovery = check_providers(
        providers, args.timeout, args.retries, args.workers, checked_at,
        do_probe=args.probe, do_discover=args.discover,
        adopt_mode=args.adopt, max_auto=args.max_auto, auto_pool=auto_pool,
        previous=previous, run_index=run_index, batch=args.probe_batch)
    elapsed = time.perf_counter() - started

    # --only 只跑了部分平台时，把上次结果里没跑的平台原样合并进来，
    # 避免一次局部运行把全量 README/status.json 冲掉。
    if only and isinstance(previous, dict):
        ran_envs = {p["env"] for p in results}
        carried = [p for p in previous.get("providers", [])
                   if p.get("env") not in ran_envs]
        if carried:
            log(f"--only 模式：{len(carried)} 个未运行的平台沿用上轮结果")
            results.extend(carried)

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
    for entry in results:
        entry["score_detail"] = score_provider(entry)
        entry["score"] = entry["score_detail"]["score"]
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

    # ---- 时间线：每轮追加一行，累积「哪个时段容易限流」 ----
    uptime_records = load_uptime(uptime_path)
    uptime_record = build_uptime_record(results, generated_at)
    uptime_records.append(uptime_record)
    append_uptime(uptime_path, uptime_record)
    uptime_summary = summarize_uptime(uptime_records, results)

    payload = {
        "generated_at": generated_at.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "generated_at_cst": checked_at,
        "elapsed_seconds": round(elapsed, 2),
        "cron": args.cron,
        "adopt_mode": args.adopt,
        "summary": summary,
        "changes": changes,
        "uptime": uptime_summary,
        "sources": source_report,
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
                "console": p["console"], "policy": p.get("policy") or {},
                "has_key": p["has_key"], "missing_env": p["missing_env"],
                "probe": p["probe"], "probe_http": p["probe_http"], "probe_note": p["probe_note"],
                "catalog": p["catalog"],
                "status": p["status"], "available": p["available"],
                "confirmed": p["confirmed"], "total": p["total"],
                "score": p.get("score"), "score_detail": p.get("score_detail"),
                "models": p["models"],
            }
            for p in results
        ],
    }

    readme = render_readme(results, summary, changes, generated_at, elapsed,
                           args.cron, history, discovery, args.adopt, uptime_summary,
                           source_report)
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
