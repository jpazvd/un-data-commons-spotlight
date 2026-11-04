"""Save every UN System Data Commons and World Bank Data360 call of the data checks, verbatim.

The calls were made through MCP tools in Claude sessions (the main session and the sub-agents that ran the
call batches in data/batches/). Their results are stored in the session transcripts (JSON lines). This script
reads those transcripts and writes, for each call, data/raw/<id>.json with the tool name, the exact arguments,
the time of the result and the response text exactly as returned. No value is parsed or changed here.

Usage: python extract_calls.py <transcript.jsonl or folder> [...]
"""
import hashlib
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
OUT = HERE / "data" / "raw"
SERVERS = ("mcp__UN_System_Data_Commons__", "mcp__World_Bank_Data360__")


def text_of(content):
    if isinstance(content, str):
        return content
    parts = []
    for b in content or []:
        if b.get("type") == "text":
            parts.append(b["text"])
    return "".join(parts)


def main(paths):
    OUT.mkdir(parents=True, exist_ok=True)
    files = []
    for p in map(pathlib.Path, paths):
        files += sorted(p.rglob("*.jsonl")) if p.is_dir() else [p]
    index, seen = [], set()
    for f in files:
        uses = {}
        for line in open(f, encoding="utf-8"):
            d = json.loads(line)
            c = (d.get("message") or {}).get("content")
            if not isinstance(c, list):
                continue
            for b in c:
                if b.get("type") == "tool_use" and b.get("name", "").startswith(SERVERS):
                    uses[b["id"]] = b
                elif b.get("type") == "tool_result" and b.get("tool_use_id") in uses:
                    u = uses[b["tool_use_id"]]
                    resp = text_of(b.get("content"))
                    if "too large" in resp[:400].lower() or "saved to" in resp[:400].lower():
                        print("WARNING: truncated or redirected result", u["id"], resp[:200], file=sys.stderr)
                    key = hashlib.sha1(json.dumps([u["name"], u["input"], resp], sort_keys=True).encode()).hexdigest()[:16]
                    if key in seen:
                        continue
                    seen.add(key)
                    rec = {"id": key, "tool": u["name"].split("__")[-1], "server": u["name"].split("__")[1],
                           "args": u["input"], "result_at": d.get("timestamp"), "is_error": bool(b.get("is_error")),
                           "transcript": f.name, "response": resp}
                    (OUT / f"{key}.json").write_text(json.dumps(rec, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
                    index.append({k: rec[k] for k in ("id", "server", "tool", "args", "result_at", "is_error", "transcript")})
    index.sort(key=lambda r: (r["result_at"] or "", r["id"]))
    (HERE / "data" / "calls_index.json").write_text(json.dumps(index, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"{len(index)} calls from {len(files)} transcripts -> {OUT}")


if __name__ == "__main__":
    main(sys.argv[1:])
