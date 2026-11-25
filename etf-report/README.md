# 국내 ETF 수익률 랭킹 리포트

전일 거래량 50만 주 이상 국내 상장 ETF를 매일 수집해 1·3·6개월 수익률, 배당수익률, 장기투자 점수로 정리합니다.

```bash
python3 etf-report/fetch_etf.py      # data/etf_latest.json + data/etf_YYYYMMDD.json
python3 etf-report/build_html.py     # etf_report.html 생성
```

- 데이터: 네이버 금융 (finance.naver.com, fchart.stock.naver.com, m.stock.naver.com) — 네트워크 허용 필요
- `content/analysis.html`: 전문가 토론·최종 결론 (수동/Claude 작성)
- `content/daily_note.html`: 매일 갱신되는 '오늘의 변화' 코멘트
