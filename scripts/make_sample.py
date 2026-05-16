"""로컬 개발용 샘플 데이터 생성 (pykrx 불필요)"""
import json, random, math
from pathlib import Path
from datetime import datetime, timedelta

random.seed(42)
OUT = Path(__file__).parent.parent / "public" / "data"
OUT.mkdir(parents=True, exist_ok=True)
TODAY = datetime.now().strftime("%Y-%m-%d")

ETFS = [
    ("069500","KODEX 200","국내주식",28000,8,18,5500),
    ("102110","TIGER 200","국내주식",27000,7,18,1200),
    ("091160","KODEX 반도체","국내주식",35000,15,28,800),
    ("091180","KODEX 은행","국내주식",8200,9,20,300),
    ("229200","KODEX 코스닥150","국내주식",8500,4,25,600),
    ("360750","TIGER 미국S&P500","해외주식",19000,12,15,2800),
    ("379800","KODEX 미국S&P500TR","해외주식",18500,12,15,1500),
    ("371460","TIGER 미국나스닥100","해외주식",22000,14,18,1800),
    ("381180","KODEX 미국나스닥100TR","해외주식",21000,14,18,2200),
    ("133690","TIGER 미국S&P500레버리지","파생",12000,24,35,900),
    ("114260","KODEX 국채3년","채권",52000,2,3,400),
    ("148070","KOSEF 국고채10년","채권",11000,4,6,250),
    ("273130","KODEX 종합채권(AA-)액티브","채권",10200,3,4,350),
    ("214980","KODEX 단기채권PLUS","채권",100500,1,1,1200),
    ("385720","TIGER 미국채10년선물","채권",9800,6,10,300),
    ("453850","ACE 미국30년국채액티브","채권",8500,8,14,280),
    ("284430","KODEX 구리선물(H)","원자재",5200,10,22,180),
    ("261220","KODEX WTI원유선물(H)","원자재",4800,15,28,220),
    ("261240","KODEX 미국반도체MV","해외주식",16000,18,22,650),
    ("360200","ACE 미국S&P500","해외주식",17500,11,15,900),
]

def gbm(s0, mu, sigma, n=65):
    dt = 1/252
    prices = [s0]
    for _ in range(n-1):
        r = random.gauss((mu - 0.5*sigma**2)*dt, sigma*math.sqrt(dt))
        prices.append(prices[-1] * math.exp(r))
    return prices

def make_bars(s0, mu, sigma, n=65):
    closes = gbm(s0, mu, sigma, n)
    bars = []
    base = datetime.now() - timedelta(days=n*1.4)
    d = base
    for c in closes:
        while d.weekday() >= 5:
            d += timedelta(days=1)
        o = c * random.uniform(0.997, 1.003)
        h = max(o, c) * random.uniform(1.001, 1.008)
        l = min(o, c) * random.uniform(0.992, 0.999)
        bars.append({"date": d.strftime("%Y-%m-%d"), "open": round(o), "high": round(h),
                     "low": round(l), "close": round(c), "volume": random.randint(100000, 3000000)})
        d += timedelta(days=1)
    return bars

etf_list = []
price_data = {}

for ticker, name, cat, price, mu_pct, sigma_pct, vol_억 in ETFS:
    mu = mu_pct / 100
    sigma = sigma_pct / 100
    bars = make_bars(price, mu, sigma)
    closes = [b["close"] for b in bars]

    mom_1m = round((closes[-1]/closes[-22]-1)*100, 2) if len(closes)>=22 else None
    mom_3m = round((closes[-1]/closes[0]-1)*100, 2)
    rets = [(closes[i]-closes[i-1])/closes[i-1] for i in range(1,len(closes))]
    import statistics
    vol_20d = round(statistics.stdev(rets[-20:])*math.sqrt(252)*100, 2)
    sharpe  = round((statistics.mean(rets)-0.035/252)/statistics.stdev(rets)*math.sqrt(252), 2)
    roll_max = closes[0]
    mdd_val = 0
    for c in closes:
        roll_max = max(roll_max, c)
        mdd_val  = min(mdd_val, (c-roll_max)/roll_max*100)
    mdd = round(mdd_val, 2)
    rsi_val = 50 + random.uniform(-20, 20)
    dist_yield = round(random.uniform(0,1)*2, 3) if cat in ("채권","부동산") else round(random.uniform(0,0.3), 3)

    etf_list.append({"ticker":ticker,"name":name,"category":cat,"aum_억":round(vol_억*0.8+random.uniform(-50,50),1),
                     "dist_yield":dist_yield,"nav":closes[-1],"price_last":closes[-1],
                     "mom_1m":mom_1m,"mom_3m":mom_3m,"vol_20d":vol_20d,"sharpe":sharpe,
                     "mdd":mdd,"rsi":round(rsi_val,1),"vol_avg_억":round(vol_억*random.uniform(0.8,1.2),1),"updated":TODAY})
    price_data[ticker] = bars

(OUT/"etf_summary.json").write_text(
    json.dumps({"updated":TODAY,"count":len(etf_list),"etfs":etf_list},ensure_ascii=False,indent=2),encoding="utf-8")
(OUT/"prices.json").write_text(
    json.dumps({"updated":TODAY,"data":price_data},ensure_ascii=False,indent=2),encoding="utf-8")

print(f"샘플 데이터 생성 완료: {len(etf_list)}개 ETF")

# Top3 생성
candidates = [e for e in etf_list if e["category"]!="파생"]
candidates.sort(key=lambda x: (x.get("mom_3m") or 0)*0.3+(x.get("sharpe") or 0)*25, reverse=True)
top3 = candidates[:3]
top3_out = {"date":TODAY,"strategy":"현재 시장은 완만한 회복 흐름을 보이고 있습니다. 샘플 데이터 기반 추천이며 실데이터 연동 후 갱신됩니다.",
            "picks":[{"rank":i+1,"ticker":e["ticker"],"name":e["name"],"category":e["category"],
                      "score":round((e.get("mom_3m") or 0)*0.3+(e.get("sharpe") or 0)*25,2),
                      "mom_3m":e.get("mom_3m"),"sharpe":e.get("sharpe"),"vol_avg_억":e.get("vol_avg_억"),
                      "rsi":e.get("rsi"),"mdd":e.get("mdd"),"dist_yield":e.get("dist_yield"),
                      "reason":f"샘플 데이터 기준 {i+1}순위. 실데이터 연동 시 AI 분석으로 대체됩니다."}
                     for i,e in enumerate(top3)]}
(OUT/"top3.json").write_text(json.dumps(top3_out,ensure_ascii=False,indent=2),encoding="utf-8")
print("Top3 생성 완료")
