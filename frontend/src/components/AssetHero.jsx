import React from 'react';
import {
  Shield,
  Target,
  Zap,
  QrCode,
  Laptop,
  PlusCircle,
  Scan,
  UserPlus,
  FileSpreadsheet,
  ChevronRight,
  ExternalLink,
  Sparkles
} from 'lucide-react';

export default function AssetHero({
  summary,
  featuredAsset,
  onOpenScanner,
  onOpenAssign,
  onOpenNewAsset,
  onSelectAsset
}) {
  const asset = featuredAsset || {
    asset_tag: 'TRC-001234',
    asset_name: 'MacBook Pro 14"',
    brand: 'Apple',
    serial_no: 'C02G80XMD6R7',
    status: 'In Circulation',
    assigned_to_name: 'Rohan Mehta',
    location: 'Hyderabad',
  };

  return (
    <div className="grid grid-cols-1 xl:grid-cols-12 gap-6 items-stretch">
      {/* Central Hero Showcase Card (8 cols) */}
      <div className="xl:col-span-8 p-6 sm:p-8 rounded-2xl bg-gradient-to-br from-[#0c1324] via-[#090e1a] to-[#050811] border border-tracora-border/80 relative overflow-hidden flex flex-col justify-between shadow-glow-card group">
        {/* Subtle Ambient Background Mesh */}
        <div className="absolute top-0 right-1/4 w-96 h-96 rounded-full bg-tracora-cyan/10 blur-3xl pointer-events-none" />
        <div className="absolute -bottom-10 right-0 w-80 h-80 rounded-full bg-tracora-blue/15 blur-3xl pointer-events-none" />

        <div className="relative z-10 grid grid-cols-1 md:grid-cols-12 gap-6 items-center">
          {/* Left Text & Badges Column (7 cols) */}
          <div className="md:col-span-6 lg:col-span-7 space-y-4">
            <div className="text-[11px] font-mono tracking-widest text-slate-400 font-semibold uppercase flex items-center gap-1.5">
              <span>GOOD MORNING, KISHORE</span>
              <span>👋</span>
            </div>

            <div className="space-y-1">
              <h1 className="text-3xl sm:text-4xl font-extrabold text-white tracking-tight font-sans leading-tight">
                Your Assets.<br />
                <span className="bg-gradient-to-r from-tracora-cyan via-sky-400 to-tracora-blue bg-clip-text text-transparent drop-shadow-[0_0_20px_rgba(0,229,255,0.3)]">
                  Our Priority.
                </span>
              </h1>
              <p className="text-xs sm:text-sm text-slate-400 leading-relaxed font-sans pt-1 max-w-md">
                Track, manage and protect your organization's assets — all in one place.
              </p>
            </div>

            {/* 3 Trust / Enterprise Badges */}
            <div className="grid grid-cols-3 gap-2 pt-3">
              {/* Badge 1: Secure */}
              <div className="p-2.5 rounded-xl bg-white/[0.03] border border-white/[0.06] hover:border-tracora-cyan/30 transition-colors">
                <div className="w-6 h-6 rounded-lg bg-emerald-500/15 text-emerald-400 flex items-center justify-center mb-1.5">
                  <Shield className="w-3.5 h-3.5" />
                </div>
                <div className="text-[11px] font-bold text-white leading-none">Secure</div>
                <div className="text-[9px] text-slate-500 font-mono mt-0.5">Enterprise grade</div>
              </div>

              {/* Badge 2: Accurate */}
              <div className="p-2.5 rounded-xl bg-white/[0.03] border border-white/[0.06] hover:border-tracora-cyan/30 transition-colors">
                <div className="w-6 h-6 rounded-lg bg-cyan-500/15 text-tracora-cyan flex items-center justify-center mb-1.5">
                  <Target className="w-3.5 h-3.5" />
                </div>
                <div className="text-[11px] font-bold text-white leading-none">Accurate</div>
                <div className="text-[9px] text-slate-500 font-mono mt-0.5">Real-time updates</div>
              </div>

              {/* Badge 3: Efficient */}
              <div className="p-2.5 rounded-xl bg-white/[0.03] border border-white/[0.06] hover:border-tracora-cyan/30 transition-colors">
                <div className="w-6 h-6 rounded-lg bg-purple-500/15 text-purple-400 flex items-center justify-center mb-1.5">
                  <Zap className="w-3.5 h-3.5" />
                </div>
                <div className="text-[11px] font-bold text-white leading-none">Efficient</div>
                <div className="text-[9px] text-slate-500 font-mono mt-0.5">Smarter ops</div>
              </div>
            </div>
          </div>

          {/* Right 3D Hardware Pedestal Showcase (5 cols) */}
          <div className="md:col-span-6 lg:col-span-5 relative flex items-center justify-center">
            {/* 3D Hardware Stage Image */}
            <div className="relative w-full rounded-2xl overflow-hidden border border-tracora-cyan/20 shadow-2xl group/img">
              <img
                src="/hardware_stage.jpg"
                alt="3D Enterprise Hardware Cyber Stage"
                className="w-full h-56 sm:h-64 object-cover transform group-hover/img:scale-105 transition-transform duration-700"
              />
              <div className="absolute inset-0 bg-gradient-to-t from-tracora-void/90 via-transparent to-transparent pointer-events-none" />

              {/* Floating Holographic HUD Card */}
              <div
                onClick={() => onSelectAsset && onSelectAsset(asset)}
                className="absolute bottom-3 left-3 right-3 p-3 rounded-xl bg-tracora-void/85 backdrop-blur-md border border-tracora-cyan/40 shadow-hud-badge cursor-pointer hover:border-tracora-cyan transition-all"
              >
                <div className="flex items-start justify-between gap-2">
                  <div className="space-y-0.5">
                    <div className="flex items-center gap-1.5">
                      <span className="text-[10px] font-mono text-slate-400">IT Asset</span>
                      <span className="text-xs font-bold text-white font-sans">{asset.asset_name}</span>
                      <span className="text-[9px] font-mono px-1.5 py-0.2 rounded-full bg-emerald-500/20 text-emerald-400 border border-emerald-500/40 font-bold uppercase">
                        Assigned
                      </span>
                    </div>
                    <div className="text-[10px] font-mono text-slate-300">
                      Asset ID: <strong className="text-tracora-cyan">{asset.asset_tag || 'TRC-001234'}</strong>
                    </div>
                    <div className="text-[10px] font-mono text-slate-400">
                      Owner: <span className="text-slate-200">{asset.assigned_to_name || 'Rohan Mehta'}</span> · Location: <span className="text-slate-200">{asset.location || 'Hyderabad'}</span>
                    </div>
                  </div>

                  <div className="w-9 h-9 rounded-lg bg-white/10 border border-white/20 p-1 flex items-center justify-center flex-shrink-0">
                    <QrCode className="w-full h-full text-tracora-cyan" />
                  </div>
                </div>
              </div>

              {/* Holographic Watermark Tag */}
              <div className="absolute top-2 right-2 text-[8px] font-mono tracking-widest text-tracora-cyan/70 font-semibold bg-tracora-void/70 px-1.5 py-0.5 rounded border border-tracora-cyan/20">
                REAL CONTROL
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Right Column: Quick Actions Card (4 cols) */}
      <div className="xl:col-span-4 p-6 rounded-2xl bg-tracora-surface/90 border border-tracora-border/80 flex flex-col justify-between shadow-glow-card">
        <div>
          <div className="flex items-center justify-between mb-5">
            <h2 className="text-base font-bold text-white tracking-tight flex items-center gap-2 font-sans">
              <Zap className="w-4 h-4 text-tracora-cyan" />
              Quick Actions
            </h2>
            <span className="text-[10px] font-mono text-tracora-muted uppercase tracking-wider">Fast Lane</span>
          </div>

          <div className="space-y-2.5">
            {/* Action 1: Add New Asset */}
            <button
              onClick={onOpenNewAsset}
              className="w-full flex items-center justify-between p-3 rounded-xl bg-tracora-card hover:bg-tracora-card-hover border border-tracora-border hover:border-tracora-cyan/40 transition-all text-left group"
            >
              <div className="flex items-center gap-3">
                <div className="w-9 h-9 rounded-lg bg-tracora-blue/20 text-tracora-blue group-hover:text-tracora-cyan group-hover:bg-tracora-cyan/20 flex items-center justify-center transition-colors">
                  <PlusCircle className="w-4 h-4" />
                </div>
                <div>
                  <div className="text-xs font-semibold text-white group-hover:text-tracora-cyan transition-colors font-sans">
                    Add New Asset
                  </div>
                  <div className="text-[11px] text-tracora-muted font-sans">Register a new asset in the system</div>
                </div>
              </div>
              <ChevronRight className="w-4 h-4 text-tracora-muted group-hover:text-white group-hover:translate-x-0.5 transition-all" />
            </button>

            {/* Action 2: Scan QR / Barcode */}
            <button
              onClick={onOpenScanner}
              className="w-full flex items-center justify-between p-3 rounded-xl bg-tracora-card hover:bg-tracora-card-hover border border-tracora-border hover:border-tracora-cyan/40 transition-all text-left group"
            >
              <div className="flex items-center gap-3">
                <div className="w-9 h-9 rounded-lg bg-purple-500/20 text-purple-400 group-hover:text-purple-300 flex items-center justify-center transition-colors">
                  <Scan className="w-4 h-4" />
                </div>
                <div>
                  <div className="text-xs font-semibold text-white group-hover:text-tracora-cyan transition-colors font-sans">
                    Scan QR / Barcode
                  </div>
                  <div className="text-[11px] text-tracora-muted font-sans">View or manage asset details</div>
                </div>
              </div>
              <ChevronRight className="w-4 h-4 text-tracora-muted group-hover:text-white group-hover:translate-x-0.5 transition-all" />
            </button>

            {/* Action 3: Assign Asset */}
            <button
              onClick={onOpenAssign}
              className="w-full flex items-center justify-between p-3 rounded-xl bg-tracora-card hover:bg-tracora-card-hover border border-tracora-border hover:border-tracora-cyan/40 transition-all text-left group"
            >
              <div className="flex items-center gap-3">
                <div className="w-9 h-9 rounded-lg bg-emerald-500/20 text-emerald-400 group-hover:text-emerald-300 flex items-center justify-center transition-colors">
                  <UserPlus className="w-4 h-4" />
                </div>
                <div>
                  <div className="text-xs font-semibold text-white group-hover:text-tracora-cyan transition-colors font-sans">
                    Assign Asset
                  </div>
                  <div className="text-[11px] text-tracora-muted font-sans">Assign to an employee or department</div>
                </div>
              </div>
              <ChevronRight className="w-4 h-4 text-tracora-muted group-hover:text-white group-hover:translate-x-0.5 transition-all" />
            </button>

            {/* Action 4: Generate Report */}
            <button
              onClick={() => alert("Asset compliance report generated.")}
              className="w-full flex items-center justify-between p-3 rounded-xl bg-tracora-card hover:bg-tracora-card-hover border border-tracora-border hover:border-tracora-cyan/40 transition-all text-left group"
            >
              <div className="flex items-center gap-3">
                <div className="w-9 h-9 rounded-lg bg-amber-500/20 text-amber-400 group-hover:text-amber-300 flex items-center justify-center transition-colors">
                  <FileSpreadsheet className="w-4 h-4" />
                </div>
                <div>
                  <div className="text-xs font-semibold text-white group-hover:text-tracora-cyan transition-colors font-sans">
                    Generate Report
                  </div>
                  <div className="text-[11px] text-tracora-muted font-sans">Download asset reports</div>
                </div>
              </div>
              <ChevronRight className="w-4 h-4 text-tracora-muted group-hover:text-white group-hover:translate-x-0.5 transition-all" />
            </button>
          </div>
        </div>

        {/* Audit Compliance Footer */}
        <div className="mt-4 pt-3 border-t border-tracora-border/60 flex items-center justify-between text-[11px] font-mono text-slate-400">
          <span className="flex items-center gap-1.5 text-tracora-cyan">
            <Sparkles className="w-3.5 h-3.5" />
            Audit Sealed
          </span>
          <span>Rule 2 Enforced</span>
        </div>
      </div>
    </div>
  );
}