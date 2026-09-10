import React from 'react';
import {
  Laptop,
  UserCheck,
  Briefcase,
  AlertTriangle,
  ArrowUp,
  ArrowDown
} from 'lucide-react';

export default function IntelligenceMatrix({ summary }) {
  const s = summary || {
    total_assets: 684,
    assigned_assets: 612,
    available_assets: 72,
    maintenance_assets: 18,
  };

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4">
      {/* Card 1: Total Assets */}
      <div className="p-5 rounded-2xl bg-tracora-surface/85 border border-tracora-border hover:border-tracora-cyan/40 transition-all group shadow-sm relative overflow-hidden">
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-3.5">
            <div className="w-10 h-10 rounded-xl bg-cyan-500/15 text-tracora-cyan flex items-center justify-center border border-cyan-500/25 group-hover:scale-105 transition-transform flex-shrink-0">
              <Laptop className="w-5 h-5" />
            </div>
            <div>
              <div className="text-xs text-tracora-muted font-sans font-medium">Total Assets</div>
              <div className="text-2xl sm:text-3xl font-extrabold text-white font-sans tracking-tight mt-0.5">
                {s.total_assets}
              </div>
              <div className="flex items-center gap-1 text-[11px] font-mono text-tracora-cyan font-semibold mt-1">
                <ArrowUp className="w-3 h-3" />
                <span>12%</span>
                <span className="text-slate-500 font-sans font-normal ml-1">vs last month</span>
              </div>
            </div>
          </div>

          {/* Blue Sparkline */}
          <div className="w-20 h-10 flex items-center justify-end">
            <svg className="w-full h-8 text-tracora-cyan overflow-visible" viewBox="0 0 70 24" fill="none">
              <path
                d="M2 18 Q 18 16, 30 19 T 50 8 T 68 2"
                stroke="currentColor"
                strokeWidth="2.5"
                strokeLinecap="round"
                className="drop-shadow-[0_0_6px_rgba(0,229,255,0.6)]"
              />
            </svg>
          </div>
        </div>
      </div>

      {/* Card 2: Assigned Assets */}
      <div className="p-5 rounded-2xl bg-tracora-surface/85 border border-tracora-border hover:border-purple-500/40 transition-all group shadow-sm relative overflow-hidden">
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-3.5">
            <div className="w-10 h-10 rounded-xl bg-purple-500/15 text-purple-400 flex items-center justify-center border border-purple-500/25 group-hover:scale-105 transition-transform flex-shrink-0">
              <UserCheck className="w-5 h-5" />
            </div>
            <div>
              <div className="text-xs text-tracora-muted font-sans font-medium">Assigned Assets</div>
              <div className="text-2xl sm:text-3xl font-extrabold text-white font-sans tracking-tight mt-0.5">
                {s.assigned_assets}
              </div>
              <div className="flex items-center gap-1 text-[11px] font-mono text-purple-400 font-semibold mt-1">
                <ArrowUp className="w-3 h-3" />
                <span>8%</span>
                <span className="text-slate-500 font-sans font-normal ml-1">vs last month</span>
              </div>
            </div>
          </div>

          {/* Purple Sparkline */}
          <div className="w-20 h-10 flex items-center justify-end">
            <svg className="w-full h-8 text-purple-400 overflow-visible" viewBox="0 0 70 24" fill="none">
              <path
                d="M2 20 Q 20 18, 35 15 T 52 11 T 68 3"
                stroke="currentColor"
                strokeWidth="2.5"
                strokeLinecap="round"
                className="drop-shadow-[0_0_6px_rgba(168,85,247,0.5)]"
              />
            </svg>
          </div>
        </div>
      </div>

      {/* Card 3: Available Assets */}
      <div className="p-5 rounded-2xl bg-tracora-surface/85 border border-tracora-border hover:border-emerald-500/40 transition-all group shadow-sm relative overflow-hidden">
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-3.5">
            <div className="w-10 h-10 rounded-xl bg-emerald-500/15 text-emerald-400 flex items-center justify-center border border-emerald-500/25 group-hover:scale-105 transition-transform flex-shrink-0">
              <Briefcase className="w-5 h-5" />
            </div>
            <div>
              <div className="text-xs text-tracora-muted font-sans font-medium">Available Assets</div>
              <div className="text-2xl sm:text-3xl font-extrabold text-white font-sans tracking-tight mt-0.5">
                {s.available_assets}
              </div>
              <div className="flex items-center gap-1 text-[11px] font-mono text-emerald-400 font-semibold mt-1">
                <ArrowUp className="w-3 h-3" />
                <span>5%</span>
                <span className="text-slate-500 font-sans font-normal ml-1">vs last month</span>
              </div>
            </div>
          </div>

          {/* Green Sparkline */}
          <div className="w-20 h-10 flex items-center justify-end">
            <svg className="w-full h-8 text-emerald-400 overflow-visible" viewBox="0 0 70 24" fill="none">
              <path
                d="M2 17 Q 20 19, 36 12 T 52 14 T 68 5"
                stroke="currentColor"
                strokeWidth="2.5"
                strokeLinecap="round"
                className="drop-shadow-[0_0_6px_rgba(16,185,129,0.5)]"
              />
            </svg>
          </div>
        </div>
      </div>

      {/* Card 4: Due for Maintenance */}
      <div className="p-5 rounded-2xl bg-tracora-surface/85 border border-tracora-border hover:border-amber-500/40 transition-all group shadow-sm relative overflow-hidden">
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-3.5">
            <div className="w-10 h-10 rounded-xl bg-amber-500/15 text-amber-400 flex items-center justify-center border border-amber-500/25 group-hover:scale-105 transition-transform flex-shrink-0">
              <AlertTriangle className="w-5 h-5" />
            </div>
            <div>
              <div className="text-xs text-tracora-muted font-sans font-medium">Due for Maintenance</div>
              <div className="text-2xl sm:text-3xl font-extrabold text-white font-sans tracking-tight mt-0.5">
                {s.maintenance_assets}
              </div>
              <div className="flex items-center gap-1 text-[11px] font-mono text-amber-400 font-semibold mt-1">
                <ArrowDown className="w-3 h-3" />
                <span>3%</span>
                <span className="text-slate-500 font-sans font-normal ml-1">vs last month</span>
              </div>
            </div>
          </div>

          {/* Orange Sparkline */}
          <div className="w-20 h-10 flex items-center justify-end">
            <svg className="w-full h-8 text-amber-400 overflow-visible" viewBox="0 0 70 24" fill="none">
              <path
                d="M2 5 Q 18 8, 32 10 T 52 15 T 68 19"
                stroke="currentColor"
                strokeWidth="2.5"
                strokeLinecap="round"
                className="drop-shadow-[0_0_6px_rgba(245,158,11,0.5)]"
              />
            </svg>
          </div>
        </div>
      </div>
    </div>
  );
}