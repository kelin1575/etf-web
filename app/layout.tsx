import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "ETF 인사이트 — 국내 거래량 상위 100",
  description: "국내 ETF 거래량 상위 100개 분석 · AI Top3 추천 · 매일 자동 갱신",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="ko">
      <body className="bg-gray-950 text-gray-100 min-h-screen">
        <header className="border-b border-gray-800 px-6 py-4">
          <div className="max-w-7xl mx-auto flex items-center justify-between">
            <div>
              <h1 className="text-xl font-bold text-white">📊 ETF 인사이트</h1>
              <p className="text-xs text-gray-400 mt-0.5">국내 거래량 상위 100 · AI 추천 · 매일 갱신</p>
            </div>
            <span className="text-xs text-gray-500">데이터: KRX 공식 · 투자 참고용</span>
          </div>
        </header>
        <main className="max-w-7xl mx-auto px-4 py-6">{children}</main>
        <footer className="border-t border-gray-800 px-6 py-4 mt-12 text-center text-xs text-gray-600">
          본 사이트의 정보는 투자 참고용이며 실제 투자 조언이 아닙니다.
        </footer>
      </body>
    </html>
  );
}
