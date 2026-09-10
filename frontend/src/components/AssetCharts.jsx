import React, { useState } from 'react';
import { PieChart, TrendingUp, Filter, BarChart2 } from 'lucide-react';

export default function AssetCharts({ categories, totalAssets }) {
  const [timeRange, setTimeRange] = useState('6M');

  const catList = categories && categories.length > 0 ? categories : [
    { category: 'Laptops', count: 260, percentage: 38.0 },
    { category: 'Desktops', count: 150, percentage: 22.0 },
    { category: 'Monitors', count: 103, percentage: 15.0 },
    { category: 'Mobile Phones', count: 82, percentage: 12.0 },
    { category: 'Accessories', count: 55, percentage: 8.0 },
    { category: 'Others', count: 34, percentage: 5.0 },
  ];

  const colors = [
    '#00e5ff', // Cyan
    '#2563eb', // Blue
    '#10b981', // Emerald
    '#a855f7', // Purple
    '#f59e0b', // Amber
    '#64748b', // Slate
  ];

  return (
    <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
      {/* Chart 1: Asset Trends (Multi-Series Area Glow Chart) - 7 cols */}
      <div className="lg:col-span-7 p-6 rounded-2xl bg-tracora-surface/80 border border-tracora-border relative overflow-hidden flex flex-col justify-between">
        <div className="flex flex-wrap items-center justify-between gap-4 mb-6">
          <div>
            <h3 className="text-base font-bold text-white tracking-tight">
              Asset Lifecycle & Movement Trend
            </h3>
            <p className="text-xs text-tracora-muted font-sans">
              Historical growth of total vs assigned hardware
            </p>
          </div>

          <div className="flex items-center gap-1 p-1 bg-tracora-card rounded-xl border border-tracora-border font-mono text-xs">
            {['6M', '3M', '1Y'].map((range) => (
              <button
                key={range}
                onClick={() => setTimeRange(range)}
                className={`px-3 py-1 rounded-lg transition-all ${
                  timeRange === range
                    ? 'bg-tracora-cyan/20 text-tracora-cyan border border-tracora-cyan/40 font-bold'
                    : 'text-slate-400 hover:text-white'
                }`}
              >
                {range}
              </button>
            ))}
          </div>
        </div>

        {/* Dynamic SVG Area Graph with Multi-Line Glow */}
        <div className="h-56 relative w-full pt-4">
          <svg className="w-full h-full overflow-visible" viewBox="0 0 500 180" preserveAspectRatio="none">
            <defs>
              <linearGradient id="cyanArea" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#00e5ff" stopOpacity="0.25" />
                <stop offset="100%" stopColor="#00e5ff" stopOpacity="0.0" />
              </linearGradient>
              <linearGradient id="blueArea" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#2563eb" stopOpacity="0.2" />
                <stop offset="100%" stopColor="#2563eb" stopOpacity="0.0" />
              </linearGradient>
            </defs>

            {/* Grid Guidelines */}
            <line x1="0" y1="30" x2="500" y2="30" stroke="rgba(255,255,255,0.04)" strokeDasharray="3 3" />
            <line x1="0" y1="80" x2="500" y2="80" stroke="rgba(255,255,255,0.04)" strokeDasharray="3 3" />
            <line x1="0" y1="130" x2="500" y2="130" stroke="rgba(255,255,255,0.04)" strokeDasharray="3 3" />

            {/* Total Assets Area & Line (Cyan) */}
            <path
              d="M0,140 Q80,125 150,110 T300,75 T420,45 T500,25 L500,180 L0,180 Z"
              fill="url(#cyanArea)"
            />
            <path
              d="M0,140 Q80,125 150,110 T300,75 T420,45 T500,25"
              fill="none"
              stroke="#00e5ff"
              strokeWidth="3"
              strokeLinecap="round"
              className="drop-shadow-[0_0_8px_rgba(0,229,255,0.5)]"
            />

            {/* Assigned Assets Line (Emerald) */}
            <path
              d="M0,155 Q80,142 150,128 T300,95 T420,65 T500,45"
              fill="none"
              stroke="#10b981"
              strokeWidth="2.5"
              strokeLinecap="round"
              className="drop-shadow-[0_0_6px_rgba(16,185,129,0.4)]"
            />

            {/* Available in Store Line (Purple) */}
            <path
              d="M0,165 Q80,160 150,155 T300,145 T420,135 T500,125"
              fill="none"
              stroke="#a855f7"
              strokeWidth="2"
              strokeLinecap="round"
              strokeDasharray="4 3"
            />

            {/* Node Points on Active Month */}
            <circle cx="500" cy="25" r="5" fill="#00e5ff" className="drop-shadow-[0_0_10px_#00e5ff]" />
            <circle cx="500" cy="45" r="4" fill="#10b981" />
            <circle cx="500" cy="125" r="4" fill="#a855f7" />
          </svg>

          {/* Month Axis Labels */}
          <div className="flex justify-between text-[10px] font-mono text-tracora-muted pt-2 border-t border-white/[0.04]">
            <span>MAR</span>
            <span>APR</span>
            <span>MAY</span>
            <span>JUN</span>
            <span>JUL</span>
            <span className="text-tracora-cyan font-bold">AUG (CURRENT)</span>
          </div>
        </div>

        {/* Graph Legend */}
        <div className="flex flex-wrap items-center gap-5 mt-4 pt-3 border-t border-tracora-border/60 text-xs font-mono">
          <div className="flex items-center gap-2">
            <span className="w-2.5 h-2.5 rounded-full bg-tracora-cyan shadow-glow-cyan" />
            <span className="text-slate-300">Total Assets</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="w-2.5 h-2.5 rounded-full bg-tracora-emerald" />
            <span className="text-slate-300">In Circulation</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="w-2.5 h-2.5 rounded-full bg-purple-500" />
            <span className="text-slate-300">In Store (Available)</span>
          </div>
        </div>
      </div>

      {/* Chart 2: Category Breakdown Donut Chart - 5 cols */}
      <div className="lg:col-span-5 p-6 rounded-2xl bg-tracora-surface/80 border border-tracora-border relative flex flex-col justify-between">
        <div>
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="text-base font-bold text-white tracking-tight">Assets by Category</h3>
              <p className="text-xs text-tracora-muted font-sans">Hardware classification mix</p>
            </div>
            <PieChart className="w-4 h-4 text-tracora-cyan" />
          </div>

          {/* Donut Visual with Center Total */}
          <div className="flex items-center justify-center py-4 relative">
            <div className="w-36 h-36 rounded-full relative flex items-center justify-center">
              {/* Outer SVG Ring */}
              <svg className="w-full h-full transform -rotate-90" viewBox="0 0 100 100">
                <circle cx="50" cy="50" r="40" stroke="#1e293b" strokeWidth="12" fill="none" />
                {/* Segments */}
                <circle
                  cx="50"
                  cy="50"
                  r="40"
                  stroke="#00e5ff"
                  strokeWidth="12"
                  fill="none"
                  strokeDasharray="95 156"
                  strokeDashoffset="0"
                />
                <circle
                  cx="50"
                  cy="50"
                  r="40"
                  stroke="#2563eb"
                  strokeWidth="12"
                  fill="none"
                  strokeDasharray="55 196"
                  strokeDashoffset="-95"
                />
                <circle
                  cx="50"
                  cy="50"
                  r="40"
                  stroke="#10b981"
                  strokeWidth="12"
                  fill="none"
                  strokeDasharray="38 213"
                  strokeDashoffset="-150"
                />
                <circle
                  cx="50"
                  cy="50"
                  r="40"
                  stroke="#a855f7"
                  strokeWidth="12"
                  fill="none"
                  strokeDasharray="30 221"
                  strokeDashoffset="-188"
                />
                <circle
                  cx="50"
                  cy="50"
                  r="40"
                  stroke="#f59e0b"
                  strokeWidth="12"
                  fill="none"
                  strokeDasharray="20 231"
                  strokeDashoffset="-218"
                />
              </svg>

              {/* Center Readout */}
              <div className="absolute inset-0 flex flex-col items-center justify-center text-center">
                <span className="text-xl font-extrabold text-white font-mono leading-none">
                  {totalAssets || 684}
                </span>
                <span className="text-[9px] uppercase tracking-wider text-tracora-muted font-mono mt-0.5">
                  Total Assets
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* Legend List */}
        <div className="space-y-2 pt-3 border-t border-tracora-border/60">
          {catList.slice(0, 5).map((item, index) => (
            <div key={item.category} className="flex items-center justify-between text-xs font-mono">
              <div className="flex items-center gap-2 truncate">
                <span
                  className="w-2.5 h-2.5 rounded-full flex-shrink-0"
                  style={{ backgroundColor: colors[index % colors.length] }}
                />
                <span className="text-slate-300 truncate">{item.category}</span>
              </div>
              <div className="flex items-center gap-3 text-slate-400 flex-shrink-0">
                <span className="text-white font-semibold">{item.count}</span>
                <span className="w-10 text-right text-slate-500">{item.percentage}%</span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
