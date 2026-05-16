import { promises as fs } from "fs";
import path from "path";
import Top3Section from "@/components/Top3Section";
import ETFTable from "@/components/ETFTable";

async function getData() {
  const dataDir = path.join(process.cwd(), "public", "data");
  try {
    const [summaryRaw, top3Raw] = await Promise.all([
      fs.readFile(path.join(dataDir, "etf_summary.json"), "utf-8"),
      fs.readFile(path.join(dataDir, "top3.json"), "utf-8"),
    ]);
    return {
      summary: JSON.parse(summaryRaw),
      top3: JSON.parse(top3Raw),
    };
  } catch {
    return { summary: null, top3: null };
  }
}

export const revalidate = 3600; // 1시간마다 ISR 재생성

export default async function Home() {
  const { summary, top3 } = await getData();

  if (!summary) {
    return (
      <div className="flex items-center justify-center h-64 text-gray-400">
        데이터를 불러오는 중입니다. GitHub Actions가 실행된 후 갱신됩니다.
      </div>
    );
  }

  return (
    <div className="space-y-8">
      {/* 갱신 시각 */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-white">국내 ETF 거래량 상위 {summary.count}개</h2>
          <p className="text-sm text-gray-400 mt-1">기준일: {summary.updated} · 3개월 가격 흐름 기반 분석</p>
        </div>
        <span className="text-xs bg-green-900/40 text-green-400 px-3 py-1 rounded-full border border-green-800">
          매일 자동 갱신
        </span>
      </div>

      {/* AI Top3 */}
      {top3 && <Top3Section top3={top3} />}

      {/* ETF 전체 테이블 */}
      <ETFTable etfs={summary.etfs} />
    </div>
  );
}
