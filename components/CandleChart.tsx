"use client";

import { useEffect, useRef } from "react";

interface Bar {
  date: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

export default function CandleChart({ ticker, bars }: { ticker: string; bars: Bar[] }) {
  const chartRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!chartRef.current || bars.length === 0) return;

    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    let chart: any = null;

    (async () => {
      const { createChart, ColorType, CandlestickSeries, HistogramSeries } = await import("lightweight-charts");

      const el = chartRef.current!;
      chart = createChart(el, {
        width:  el.clientWidth,
        height: 380,
        layout: {
          background: { type: ColorType.Solid, color: "#0f172a" },
          textColor:  "#94a3b8",
        },
        grid: {
          vertLines:  { color: "#1e293b" },
          horzLines:  { color: "#1e293b" },
        },
        crosshair: { mode: 1 },
        rightPriceScale: { borderColor: "#334155" },
        timeScale:       { borderColor: "#334155", timeVisible: true },
      });

      // 캔들 시리즈
      const candleSeries = chart.addSeries(CandlestickSeries, {
        upColor:          "#ef4444",
        downColor:        "#3b82f6",
        borderUpColor:    "#ef4444",
        borderDownColor:  "#3b82f6",
        wickUpColor:      "#ef4444",
        wickDownColor:    "#3b82f6",
      });

      candleSeries.setData(
        bars.map(b => ({
          time:  b.date as `${number}-${number}-${number}`,
          open:  b.open,
          high:  b.high,
          low:   b.low,
          close: b.close,
        }))
      );

      // 거래량 히스토그램
      const volSeries = chart.addSeries(HistogramSeries, {
        color:   "#334155",
        priceFormat: { type: "volume" },
        priceScaleId: "vol",
      });
      chart.priceScale("vol").applyOptions({ scaleMargins: { top: 0.8, bottom: 0 } });

      volSeries.setData(
        bars.map(b => ({
          time:  b.date as `${number}-${number}-${number}`,
          value: b.volume,
          color: b.close >= b.open ? "#7f1d1d60" : "#1e3a5f60",
        }))
      );

      chart.timeScale().fitContent();

      // 리사이즈 대응
      const ro = new ResizeObserver(() => {
        if (chartRef.current && chart) {
          chart.applyOptions({ width: chartRef.current.clientWidth });
        }
      });
      ro.observe(el);

      return () => { ro.disconnect(); };
    })();

    return () => { chart?.remove(); };
  }, [bars]);

  if (bars.length === 0) {
    return <div className="flex items-center justify-center h-48 text-gray-500">차트 데이터 없음</div>;
  }

  return <div ref={chartRef} className="w-full" />;
}
