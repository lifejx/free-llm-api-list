#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
try_key.py —— 拿到 key 之后，立刻验证它到底能不能用。

它会做两件事，跟自动巡检不一样：
  1. 真的发一条完整请求（不是 max_tokens=1 的探测），把模型的**回答**打出来给你看
  2. 逐个免费模型试一遍，告诉你哪几个能用、哪几个不行、不行是为什么

用法：
    python try_key.py SILICONFLOW_KEY sk-你的key
    python try_key.py SILICONFLOW_KEY                # 从同名环境变量读
    python try_key.py --list                         # 看看有哪些平台可以测
    python try_key.py SILICONFLOW_KEY sk-xxx --all    # 连非免费模型也一起测

想走代理（大陆直连国外平台不稳时）：
    set FREE_LLM_PROXY=socks5h://127.0.0.1:10808    （Windows）
    export FREE_LLM_PROXY=socks5h://127.0.0.1:10808 （Linux/macOS）
"""

from __future__ import annotations

import json
import os
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

import update_list as ul

ROOT = Path(__file__).resolve().parent
QUESTION = "用一句话回答：1+1 等于几？"


def ask(base_url: str, model_id: str, key: str, provider: dict,
        timeout: float = 60.0) -> dict:
    """发一条真实请求，把回答也取回来。"""
    url = base_url.rstrip("/") + "/chat/completions"
    payload = {
        "model": model_id,
        "messages": [{"role": "user", "content": QUESTION}],
        "max_tokens": 64,
        "temperature": 0,
    }
    headers = {"Content-Type": "application/json", "User-Agent": ul.UA}
    auth = provider.get("auth", "bearer")
    if auth == "api-key":
        headers["api-key"] = key
    elif auth == "x-api-key":
        headers["x-api-key"] = key
    else:
        headers["Authorization"] = f"Bearer {key}"

    started = time.perf_counter()
    request = urllib.request.Request(
        url, data=json.dumps(payload).encode("utf-8"), headers=headers, method="POST")
    try:
        with urllib.request.urlopen(request, timeout=timeout) as resp:
            body = resp.read().decode("utf-8", "replace")
        elapsed = int((time.perf_counter() - started) * 1000)
        try:
            data = json.loads(body)
            choices = data.get("choices") or []
            answer = ""
            if choices:
                answer = (choices[0].get("message") or {}).get("content") or ""
            usage = data.get("usage") or {}
        except ValueError:
            answer, usage = body[:120], {}
        return {"ok": True, "status": resp.status, "ms": elapsed,
                "answer": (answer or "").strip().replace("\n", " ")[:120], "usage": usage}
    except urllib.error.HTTPError as exc:
        body = ""
        try:
            body = exc.read(4000).decode("utf-8", "replace")
        except Exception:  # noqa: BLE001
            pass
        return {"ok": False, "status": exc.code, "ms": int((time.perf_counter() - started) * 1000),
                "reason": ul.extract_message(body) or str(exc.reason or "")}
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "status": None, "ms": int((time.perf_counter() - started) * 1000),
                "reason": f"{type(exc).__name__}: {exc}"}


def explain(status: int | None, reason: str) -> str:
    if status is None:
        return "连不上（网络问题，或需要走代理）"
    if status == 400:
        return "请求被拒：模型 ID 可能已不支持，或参数不对"
    if status == 401:
        return "密钥无效：复制错了，或这个 key 属于别的平台"
    if status == 403:
        return "被拒绝：可能是账号没实名、没开通这个模型、或地区限制"
    if status == 404:
        return "模型不存在：这个 ID 已经下架或改名了"
    if status == 429:
        return "限流或额度用尽：等一会儿，或检查免费额度还剩多少"
    if status and status >= 500:
        return "平台侧故障，跟你的 key 无关"
    return reason or "未知错误"


def main(argv: list[str]) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        except (ValueError, OSError):
            pass

    if not argv or argv[0] in ("-h", "--help"):
        print(__doc__)
        return 0

    if argv[0] == "--list":
        for p in ul.load_pool():
            kind = ((p.get("policy") or {}).get("free_kind")) or "-"
            print(f"  {p['env']:<22} {p['name']:<26} {kind:<10} "
                  f"{len(p.get('models') or [])} 个模型")
        print("\n用法：python try_key.py <密钥变量名> <你的key>")
        return 0

    env = argv[0].strip()
    proxy = os.environ.get("FREE_LLM_PROXY", "")
    if proxy:
        print(ul.enable_socks_proxy(proxy) or "代理地址无法识别")

    pool = {p["env"]: p for p in ul.load_pool()}
    provider = pool.get(env)
    if not provider:
        print(f"× providers.json 里没有 {env}；用 --list 看看有哪些")
        return 2

    key = argv[1].strip() if len(argv) > 1 and not argv[1].startswith("--") else ""
    key = key or os.environ.get(env, "").strip()
    if not key:
        print(f"× 没提供 key。用法：python try_key.py {env} sk-你的key")
        return 2

    base_url = ul.expand_env(provider.get("base_url", ""))
    missing = [v for v in (provider.get("requires") or []) if not os.environ.get(v, "").strip()]
    if missing or not base_url:
        print(f"× 这个平台还需要环境变量：{', '.join(missing) or '地址不完整'}")
        return 2

    policy = provider.get("policy") or {}
    access = policy.get("access") or {}
    print(f"平台：{provider['name']}")
    print(f"地址：{base_url}")
    print(f"免费性质：{policy.get('free_kind', '-')}　"
          f"大陆门槛：{access.get('difficulty_cn', '-')}")
    limits = policy.get("limits") or {}
    print(f"官方限速：RPM {limits.get('rpm', '-')}　RPD {limits.get('rpd', '-')}　"
          f"TPD {limits.get('tpd', '-')}　重置 {limits.get('reset', '-')}")
    print(f"测法：发一条真实提问「{QUESTION}」，max_tokens=64\n")

    ok_models, bad_models = [], []
    for model in provider["models"]:
        mid = model["id"]
        if model.get("auto") and "--all" not in argv:
            pass  # 自动发现的也测，它们同样是免费模型
        result = ask(base_url, mid, key, provider)
        if result["ok"] and result.get("answer"):
            ok_models.append(mid)
            ctx = ul.fmt_context(model.get("context"))
            print(f"  ✅ {mid}")
            print(f"     回答：{result['answer'][:80]}")
            print(f"     延迟 {result['ms']}ms　上下文 {ctx}　"
                  f"tokens {result['usage'].get('total_tokens', '?')}")
        elif result["ok"]:
            ok_models.append(mid)
            print(f"  🟠 {mid} —— 返回 200 但内容是空的")
        else:
            bad_models.append((mid, result))
            print(f"  ❌ {mid} —— HTTP {result['status']}："
                  f"{explain(result['status'], result.get('reason', ''))}")

    print()
    print(f"结果：{len(ok_models)} 个可用 / {len(bad_models)} 个不可用")
    if ok_models:
        print("\n可以直接用的模型 ID（填到客户端里的就是这一串）：")
        for mid in ok_models:
            print(f"   {mid}")
        print(f"\n客户端里填：")
        print(f"   接口地址 Base URL：{base_url}")
        print(f"   API Key：{'（就是你刚填的那个）'}")
        print(f"   模型 ID：{ok_models[0]}")
    if bad_models and all(r["status"] == 401 for _, r in bad_models):
        print("\n全部 401 —— 先确认 key 没复制错、也没有多余空格。")
    return 0 if ok_models else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
