#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
try_tools.py —— 实测「免费模型到底能不能驱动 agent」。

普通巡检只发 max_tokens=1 的 ping，回答不了最关键的问题：
这个模型支不支持 tools / function calling？agent 工具（DSH / Cline / Roo）
全靠这个参数活着，而很多「免费」模型（尤其小模型）根本不支持，
或者接口接受了参数但模型从不吐出 tool_calls。

测法（每个模型最多 2 条请求，都很短）：
  1. 带 tools + tool_choice="required"，强令模型调用 get_weather
     - 200 且 message.tool_calls 非空  -> ✅ 端到端支持（agent 可用）
     - 200 但没有 tool_calls           -> 🟡 接口收参数，模型没吐调用（不可靠）
  2. 400 且抱怨 tool_choice/required   -> 降级 tool_choice="auto" 再试一次
  3. 400 且明确说 tools/functions 不支持 -> ❌ 不支持
  4. 其余 400                         -> 补发一条无 tools 的对照请求：
                                         对照 200 = 工具参数被拒；对照也挂 = 模型另有问题
  429/402 -> ⚠️ 限流/额度，本轮无法判断

用法：
    python try_tools.py                          # 测全部能找到密钥的平台（完整免费集）
    python try_tools.py --only SILICONFLOW_KEY,MODELSCOPE_KEY
    python try_tools.py --list                   # 只看将测哪些模型，不发请求
    python try_tools.py --save research/tools.json

密钥解析顺序：同名环境变量 -> DSH 凭据文件（~/.dsh/.credentials.yaml）。
模型集：硅基取公开定价页「确证免费」的聊天模型；魔搭取 API-Inference 公开目录；
      其余平台取 providers.json + models.auto.json 池子里的模型。
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path

import update_list as ul

ROOT = Path(__file__).resolve().parent

# DSH 凭据文件里的名字 -> 本项目的平台 env 名
CRED_ALIASES = {
    "SILICONFLOW_KEY": "SI_API_KEY",
    "MODELSCOPE_KEY": "MD_API_KEY",
    "DEEPSEEK_KEY": "DEEPSEEK_API_KEY",
    "OPENROUTER_KEY": "OR_API_KEY",
}
DEFAULT_CREDENTIALS = Path.home() / ".dsh" / ".credentials.yaml"

WEATHER_TOOL = [{
    "type": "function",
    "function": {
        "name": "get_weather",
        "description": "查询指定城市的当前天气",
        "parameters": {
            "type": "object",
            "properties": {
                "city": {"type": "string", "description": "城市名，例如 Beijing"},
            },
            "required": ["city"],
        },
    },
}]
PROMPT = "What is the weather like in Beijing right now? Use the get_weather tool."

# 判定标签
YES = "yes"               # 200 且真的吐出了 tool_calls
ACCEPTED = "accepted"     # 200 但没吐 tool_calls
NO = "no"                 # 明确不支持 tools
NO_OTHER = "no_other"     # 带工具就 400、不带就 200（工具参数引发的拒绝，原因不明）
BROKEN = "broken"         # 带不带工具都失败
QUOTA = "quota"           # 429/402/额度提示
NOT_FOUND = "not_found"
AUTH = "auth"
SERVER = "server"
NETWORK = "network"
UNKNOWN = "unknown"

LABEL = {
    YES: "✅ 支持工具",
    ACCEPTED: "🟡 收参不调用",
    NO: "❌ 不支持",
    NO_OTHER: "🟠 工具参数被拒",
    BROKEN: "💔 模型本身报错",
    QUOTA: "⚠️ 限流/额度",
    NOT_FOUND: "⚪ 模型不存在",
    AUTH: "🔑 密钥问题",
    SERVER: "🌐 服务端异常",
    NETWORK: "📡 网络不通",
    UNKNOWN: "❔ 未知",
}

NO_TOOL_HINT = re.compile(r"tool|function|工具", re.I)
CHOICE_HINT = re.compile(r"tool_choice|required|\bany\b", re.I)
# 明显不是对话模型的 id（图片编辑、语音、向量等）
SKIP_HINT = re.compile(r"image-edit|inpaint|text-to-image|flux|sdxl|kolors", re.I)


def load_credentials(path: Path) -> dict:
    out: dict[str, str] = {}
    if path.exists():
        for m in re.finditer(r"^\s{2}([A-Z0-9_]+):\s*(\S+)",
                             path.read_text(encoding="utf-8"), re.M):
            out[m.group(1)] = m.group(2)
    return out


def resolve_key(env: str, creds: dict) -> str:
    key = os.environ.get(env, "").strip()
    if key:
        return key
    return creds.get(CRED_ALIASES.get(env, env), "").strip()


def post_chat(base_url: str, payload: dict, key: str, provider: dict,
              timeout: float = 90.0) -> dict:
    url = base_url.rstrip("/") + "/chat/completions"
    headers = {"Content-Type": "application/json", "Accept": "application/json",
               "User-Agent": ul.UA}
    auth = provider.get("auth", "bearer")
    if auth == "api-key":
        headers["api-key"] = key
    elif auth == "x-api-key":
        headers["x-api-key"] = key
    else:
        headers["Authorization"] = f"Bearer {key}"
    headers.update(provider.get("headers", {}))

    req = urllib.request.Request(
        url, data=json.dumps(payload).encode("utf-8"), headers=headers, method="POST")
    started = time.perf_counter()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = resp.read(16384).decode("utf-8", "replace")
            return {"http": resp.status, "body": body,
                    "ms": int((time.perf_counter() - started) * 1000)}
    except urllib.error.HTTPError as exc:
        body = ""
        try:
            body = exc.read(4096).decode("utf-8", "replace")
        except Exception:  # noqa: BLE001
            pass
        return {"http": exc.code, "body": body,
                "ms": int((time.perf_counter() - started) * 1000)}
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        return {"http": None, "body": "", "error": f"{type(exc).__name__}: {exc}",
                "ms": int((time.perf_counter() - started) * 1000)}


def make_payload(model_id: str, with_tools: bool, tool_choice: str | None,
                 max_tokens: int = 64) -> dict:
    payload = {
        "model": model_id,
        "messages": [{"role": "user", "content": PROMPT}],
        "temperature": 0,
        "max_tokens": max_tokens,
        "stream": False,
    }
    if with_tools:
        payload["tools"] = WEATHER_TOOL
        if tool_choice:
            payload["tool_choice"] = tool_choice
    return payload


def parse_tool_calls(body: str) -> tuple[bool, str, str]:
    """从 200 响应里找 tool_calls，返回 (是否真的带了函数调用, 片段, finish_reason)。"""
    try:
        data = json.loads(body)
    except ValueError:
        return False, "", ""
    choices = data.get("choices") or []
    if not choices:
        return False, "", ""
    ch0 = choices[0]
    msg = ch0.get("message") or {}
    calls = msg.get("tool_calls")
    if isinstance(calls, list):
        for c in calls:
            fn = (c or {}).get("function") or {}
            if fn.get("name"):
                args = str(fn.get("arguments") or "")[:80]
                return True, f"{fn.get('name')}({args})", str(ch0.get("finish_reason") or "")
    return False, ((msg.get("content") or "")[:60].replace("\n", " ")), \
        str(ch0.get("finish_reason") or "")


def test_model(base_url: str, model_id: str, key: str, provider: dict,
               max_tokens: int = 64) -> dict:
    """对一个模型做工具调用实测，返回 {verdict, detail, http, ms, retries}。"""
    attempts = []

    def once(with_tools: bool, tool_choice: str | None) -> dict:
        r = post_chat(base_url, make_payload(model_id, with_tools, tool_choice,
                                             max_tokens), key, provider)
        attempts.append({"tools": with_tools, "tool_choice": tool_choice,
                         "http": r["http"]})
        return r

    # 第一轮：强制调用工具
    r = once(True, "required")
    http = r["http"]

    if http == 200:
        called, snippet, finish = parse_tool_calls(r["body"])
        if called:
            detail = snippet
        elif finish == "length":
            # 思考模型把预算全花在推理上，没轮到吐工具调用 —— 参数是被接受的
            detail = f"输出预算耗尽(finish=length)，未吐调用；{snippet[:40]}"
        else:
            detail = snippet
        return {"verdict": YES if called else ACCEPTED,
                "detail": detail, "http": 200, "ms": r["ms"],
                "finish": finish, "attempts": attempts}

    note = ul.extract_message(r.get("body", "")) or r.get("error", "")

    if http in (429, 402) or ul.has_quota_hint(r.get("body", "")):
        return {"verdict": QUOTA, "detail": note, "http": http, "ms": r["ms"],
                "attempts": attempts}
    if http == 404:
        return {"verdict": NOT_FOUND, "detail": note, "http": http, "ms": r["ms"],
                "attempts": attempts}
    if http in (401, 403):
        return {"verdict": AUTH, "detail": note, "http": http, "ms": r["ms"],
                "attempts": attempts}
    if http is None:
        return {"verdict": NETWORK, "detail": r.get("error", ""), "http": None,
                "ms": r["ms"], "attempts": attempts}
    if 500 <= (http or 0) < 600:
        return {"verdict": SERVER, "detail": note, "http": http, "ms": r["ms"],
                "attempts": attempts}

    # 400/422 等：先看是不是 tool_choice="required" 不被接受 -> 降级 auto
    if http in (400, 406, 422) and CHOICE_HINT.search(note):
        r2 = once(True, "auto")
        if r2["http"] == 200:
            called, snippet, finish2 = parse_tool_calls(r2["body"])
            tag = "（auto 模式）" if snippet else "（auto 模式未调用）"
            return {"verdict": YES if called else ACCEPTED,
                    "detail": (snippet + tag).strip(), "http": 200,
                    "ms": r2["ms"], "finish": finish2, "attempts": attempts}
        if r2["http"] in (429, 402) or ul.has_quota_hint(r2.get("body", "")):
            return {"verdict": QUOTA, "detail": ul.extract_message(r2.get("body", "")),
                    "http": r2["http"], "ms": r2["ms"], "attempts": attempts}
        note = ul.extract_message(r2.get("body", "")) or note
        http = r2["http"]
        if http == 200:
            pass
        elif not (http in (400, 406, 422) and NO_TOOL_HINT.search(note)):
            # auto 也 400 且错误不像 tools —— 走对照请求
            pass

    # 400 且错误信息直接点名为 tools/functions 不支持
    if http in (400, 406, 422) and NO_TOOL_HINT.search(note):
        return {"verdict": NO, "detail": note, "http": http, "ms": r["ms"],
                "attempts": attempts}

    # 其余 4xx：发不带工具的对照请求
    if http in (400, 406, 422):
        r3 = once(False, None)
        if r3["http"] == 200:
            return {"verdict": NO_OTHER,
                    "detail": f"带工具 400：{note[:100]}", "http": http,
                    "ms": r["ms"], "attempts": attempts}
        plain_note = ul.extract_message(r3.get("body", ""))
        return {"verdict": BROKEN,
                "detail": f"带/不带工具都失败：{plain_note or note[:100]}",
                "http": r3["http"], "ms": r3["ms"], "attempts": attempts}

    return {"verdict": UNKNOWN, "detail": note, "http": http, "ms": r["ms"],
            "attempts": attempts}


def gather_targets(env: str, provider: dict, key: str) -> list[dict]:
    """返回该平台本轮要测的免费模型 [{id, context, source}]。"""
    models: dict[str, dict] = {}

    # 1) 池子里的（providers.json 人工 + models.auto.json 自动）
    for m in provider.get("models") or []:
        models[m["id"]] = {"id": m["id"], "context": m.get("context", ""),
                           "source": "自动发现" if m.get("auto") else "人工登记"}

    # 2) 硅基：公开定价页里确证免费的聊天模型（比池子全，且能发现新上免费模型）
    if env == "SILICONFLOW_KEY":
        res = ul.fetch_pricing_catalog(ul.PRICING_SOURCES[env]["url"], timeout=30)
        for mid, ent in (res.get("entries") or {}).items():
            if ul.classify_free(ent, mid) == "confirmed":
                models.setdefault(mid, {
                    "id": mid,
                    "context": ent.get("context_length") or ent.get("contextLen") or "",
                    "source": "定价页确证免费",
                })

    # 3) 魔搭：API-Inference 整个服务免费，公开目录即免费全集
    if env == "MODELSCOPE_KEY":
        res = ul.fetch_catalog(ul.expand_env(provider["base_url"]), key,
                               provider, timeout=30)
        for mid in (res.get("entries") or {}):
            if SKIP_HINT.search(mid):
                continue
            models.setdefault(mid, {"id": mid, "context": "", "source": "公开目录(全免费)"})

    # 其他平台若以后要扩，同样可以在这里接公开目录/定价页
    return sorted(models.values(), key=lambda x: x["id"])


def main(argv: list[str]) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        except (ValueError, OSError):
            pass

    ap = argparse.ArgumentParser(description="实测免费模型的工具调用（agent）能力")
    ap.add_argument("--only", default="", help="只测指定平台 env，逗号分隔")
    ap.add_argument("--list", action="store_true", help="只列出待测模型，不发请求")
    ap.add_argument("--save", default="", help="把原始结果 JSON 存到指定路径")
    ap.add_argument("--max-tokens", type=int, default=64,
                    help="每条测试请求的 max_tokens；思考模型建议用 2048 以上（默认 64）")
    ap.add_argument("--creds", default=str(DEFAULT_CREDENTIALS),
                    help="凭据文件路径（默认 ~/.dsh/.credentials.yaml）")
    args = ap.parse_args(argv)

    proxy = os.environ.get("FREE_LLM_PROXY", "")
    if proxy:
        print(ul.enable_socks_proxy(proxy) or "代理地址无法识别")

    creds = load_credentials(Path(args.creds))
    only = {x.strip() for x in args.only.split(",") if x.strip()}
    pool = ul.load_pool()
    auto_path = ROOT / "models.auto.json"
    auto_pool = ul.load_auto_pool(auto_path) if auto_path.exists() else {}
    if auto_pool:
        ul.merge_auto_pool(pool, auto_pool)

    jobs = []  # (env, name, base_url, provider, key, models)
    for provider in pool:
        env = provider["env"]
        if only and env not in only:
            continue
        key = resolve_key(env, creds)
        if not key:
            continue
        base_url = ul.expand_env(provider.get("base_url", ""))
        missing = [v for v in (provider.get("requires") or [])
                   if not os.environ.get(v, "").strip()]
        if missing or not base_url:
            continue
        models = gather_targets(env, provider, key)
        models = [m for m in models if not SKIP_HINT.search(m["id"])]
        if models:
            jobs.append((env, provider["name"], base_url, provider, key, models))

    if not jobs:
        print("没有找到可测的平台：需要在环境变量或凭据文件里至少有一个平台的 key。")
        return 2

    total = sum(len(j[5]) for j in jobs)
    if args.list:
        for env, name, base_url, _, _, models in jobs:
            print(f"{name}（{env}）{len(models)} 个：")
            for m in models:
                print(f"   {m['id']}  [{m['source']}]")
        print(f"\n共 {total} 个模型，每个最多 2 条短请求。")
        return 0

    print(f"实测工具调用能力：{len(jobs)} 个平台 / {total} 个模型")
    print("判定：✅端到端调用  🟡收参不调用  ❌不支持  🟠工具参数被拒  "
          "⚠️限流  💔模型本身报错\n")

    started_all = time.time()
    report = []
    counts: dict[str, int] = {}
    for env, name, base_url, provider, key, models in jobs:
        print(f"== {name}（{len(models)} 个）==")
        for i, m in enumerate(models, 1):
            res = test_model(base_url, m["id"], key, provider,
                             max_tokens=args.max_tokens)
            verdict = res["verdict"]
            counts[verdict] = counts.get(verdict, 0) + 1
            row = {"env": env, "provider": name, "model": m["id"],
                   "context": m.get("context", ""), "source": m["source"],
                   **res}
            report.append(row)
            detail = (res.get("detail") or "").replace("\n", " ")
            print(f"  {LABEL.get(verdict, verdict):<10} {m['id']:<48} "
                  f"HTTP {res.get('http')}  {detail[:70]}")
            time.sleep(0.6)  # 温和一点，别触发 RPM
        print()

    elapsed = int(time.time() - started_all)
    print("=" * 70)
    print(f"汇总（耗时 {elapsed}s）：")
    for verdict in (YES, ACCEPTED, NO, NO_OTHER, QUOTA, BROKEN, NOT_FOUND,
                    AUTH, SERVER, NETWORK, UNKNOWN):
        if counts.get(verdict):
            print(f"  {LABEL[verdict]}：{counts[verdict]}")
    yes_models = [r for r in report if r["verdict"] == YES]
    if yes_models:
        print("\n🏆 agent 可直接用（端到端吐 tool_calls）：")
        for r in yes_models:
            print(f"   {r['provider']:<22} {r['model']}")

    if args.save:
        out = Path(args.save)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(
            {"checked_at": datetime.now().astimezone().isoformat(timespec="seconds"),
             "elapsed_s": elapsed, "counts": counts, "results": report},
            ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"\n原始结果已存：{out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
