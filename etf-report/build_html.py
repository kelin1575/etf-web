#!/usr/bin/env python3
"""data/etf_latest.json + content/*.html → etf_report.html"""
import json, os, glob, re, datetime as dt, html

HERE = os.path.dirname(os.path.abspath(__file__))
D = os.path.join(HERE, "data")

def load(p):
    with open(p, encoding="utf-8") as f:
        return json.load(f)

def read(p, default=""):
    try:
        with open(p, encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return default

def years_since(yyyymmdd, base):
    try:
        a = dt.datetime.strptime(yyyymmdd, "%Y%m%d"); b = dt.datetime.strptime(base, "%Y%m%d")
        return (b - a).days / 365.25
    except Exception:
        return 0

def diversification(i):
    n = i["name"]; cat = i.get("category", "")
    if "커버드콜" in n: return 6
    if any(k in n for k in ("TOP2", "TOP3", "단일종목", "채권혼합")): return 2
    if any(k in n for k in ("S&P500", "코스피", "머니마켓")) or re.search(r"(KODEX|TIGER|RISE|PLUS|ACE|SOL|HANARO|1Q) 200(TR)?$", n): return 20
    if any(k in n for k in ("나스닥100", "배당다우존스")) or cat == "채권": return 15
    if "금현물" in n: return 12
    return 6  # 섹터·테마

def long_term_score(i, base):
    """장기투자 적합도 0~100. 3인 토론 합의 기준:
    보수20 · 순자산15 · 추적오차10 · 운용이력10 · 분산도20 · 추세/낙폭15 · 장기실적10, 분배함정 -10.
    레버리지/인버스는 0점."""
    if i.get("leveraged"):
        return 0
    fee = i.get("fee") if i.get("fee") is not None else 1.0
    s = 20 if fee <= 0.05 else 16 if fee <= 0.1 else 10 if fee <= 0.25 else 5 if fee <= 0.5 else 0
    aum = i.get("aum") or 0
    s += 15 if aum >= 50000 else 11 if aum >= 10000 else 6 if aum >= 3000 else 3 if aum >= 500 else 0
    te = i.get("trackingError")
    s += 0 if te is None else 10 if te <= 0.3 else 7 if te <= 1 else 4 if te <= 2 else 0
    y = years_since(i.get("listedDate") or "", base)
    s += 10 if y >= 10 else 7 if y >= 5 else 4 if y >= 3 else 1 if y >= 1 else 0
    s += diversification(i)
    r6 = i.get("r6m")
    s += 5 if r6 is None else 15 if r6 > -10 else 8 if r6 > -25 else 0     # 하락 추세 자산 감점(모멘텀 측 비판 반영)
    r3 = i.get("r3y")
    s += 4 if r3 is None else 10 if r3 > 0 else 0                           # 장기실적 비중 축소(리스크 측 비판 반영)
    if (i.get("divYield") or 0) >= 10 and (i.get("r1y") is None or i["r1y"] < 0):
        s -= 10                                                              # 고분배+마이너스 총수익
    return max(0, min(100, round(s)))

def md_to_html(md):
    """간단 Markdown → HTML (제목/표/목록/굵게/인용)."""
    out, lines, i = [], md.splitlines(), 0
    inl = lambda t: re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", html.escape(t))
    while i < len(lines):
        l = lines[i].rstrip()
        if l.startswith("|"):
            rows = []
            while i < len(lines) and lines[i].startswith("|"):
                cells = [c.strip() for c in lines[i].strip().strip("|").split("|")]
                if not all(set(c) <= set("-: ") for c in cells):
                    rows.append(cells)
                i += 1
            t = "".join(("<tr>" + "".join(f"<{'th' if n == 0 else 'td'} class=\"l\">{inl(c)}</{'th' if n == 0 else 'td'}>" for c in r) + "</tr>") for n, r in enumerate(rows))
            out.append(f'<div class="tablebox"><table>{t}</table></div>'); continue
        if re.match(r"^\s*([-*]|\d+\.)\s", l):
            items = []
            while i < len(lines) and re.match(r"^\s*([-*]|\d+\.)\s", lines[i]):
                items.append(re.sub(r"^\s*([-*]|\d+\.)\s", "", lines[i])); i += 1
            out.append("<ul>" + "".join(f"<li>{inl(x)}</li>" for x in items) + "</ul>"); continue
        m = re.match(r"^(#{1,4})\s+(.*)", l)
        if m:
            out.append(f"<h3>{inl(m.group(2))}</h3>")
        elif l.startswith(">"):
            out.append(f'<p class="sub">{inl(l.lstrip("> "))}</p>')
        elif l.strip():
            out.append(f"<p>{inl(l)}</p>")
        i += 1
    return "\n".join(out)

def debate_html():
    names = [("r1_momentum", "1R 모멘텀"), ("r1_dividend", "1R 배당·장기"), ("r1_risk", "1R 리스크"),
             ("r2_momentum", "2R 모멘텀 반론"), ("r2_dividend", "2R 배당·장기 반론"), ("r2_risk", "2R 리스크 반론")]
    parts = []
    for fn, label in names:
        md = read(os.path.join(D, "debate", fn + ".md"))
        if md:
            parts.append(f'<details class="card"><summary>{label} 원문 보기</summary><div class="prose" style="margin-top:10px">{md_to_html(md)}</div></details>')
    if not parts:
        return ""
    return '<section><div><h2>토론 원문</h2><div class="sub">각 분석가 보고서 전문입니다.</div></div>' + "".join(parts) + "</section>"

def main():
    cur = load(os.path.join(D, "etf_latest.json"))
    base = cur["baseDate"]
    snaps = sorted(p for p in glob.glob(os.path.join(D, "etf_2*.json")) if os.path.basename(p) < f"etf_{base}.json")
    prev = load(snaps[-1]) if snaps else None
    prev_rank = {}
    if prev:
        for key in ("r1m", "r3m", "r6m"):
            ranked = sorted([x for x in prev["items"] if x.get(key) is not None], key=lambda x: -x[key])
            prev_rank[key] = {x["code"]: n + 1 for n, x in enumerate(ranked)}
    prev_codes = {x["code"] for x in prev["items"]} if prev else set()
    for i in cur["items"]:
        i["lt"] = long_term_score(i, base)
        i["illiquid"] = (i.get("aum") or 0) < 500 or (i.get("tradeValue") or 0) < 50
        i["new"] = bool(prev) and i["code"] not in prev_codes
        i["prevRank"] = {k: prev_rank.get(k, {}).get(i["code"]) for k in ("r1m", "r3m", "r6m")}
    payload = {"baseDate": base, "generatedAt": cur["generatedAt"], "minVolume": cur["minVolume"],
               "totalEtfs": cur["totalEtfs"], "prevDate": prev["baseDate"] if prev else None,
               "dropped": sorted([x["name"] for x in prev["items"] if x["code"] not in {i["code"] for i in cur["items"]}]) if prev else [],
               "items": cur["items"]}
    tpl = read(os.path.join(HERE, "template.html"))
    bd = f"{base[:4]}.{base[4:6]}.{base[6:]}"
    out = (tpl.replace("{{DATA}}", json.dumps(payload, ensure_ascii=False).replace("</", "<\\/"))
              .replace("{{BASE_DATE}}", bd)
              .replace("{{ANALYSIS}}", read(os.path.join(HERE, "content", "analysis.html")) + debate_html())
              .replace("{{DAILY_NOTE}}", read(os.path.join(HERE, "content", "daily_note.html"), "<p>첫 수집일입니다. 내일부터 전일 대비 순위 변동이 표시됩니다.</p>")))
    p = os.path.join(HERE, "etf_report.html")
    with open(p, "w", encoding="utf-8") as f:
        f.write(out)
    print(p)

if __name__ == "__main__":
    main()
