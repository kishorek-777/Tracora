import React from 'react';
import { Search, QrCode, Bell, User, Sparkles, Command } from 'lucide-react';

export default function Header({ onOpenCommand, onOpenScanner, alertsCount = 18, isCollapsed }) {
  return (
    <header className="sticky top-0 z-20 h-20 bg-tracora-void/80 backdrop-blur-xl border-b border-tracora-border/60 px-6 flex items-center justify-between gap-4">
      {/* Command Search Bar */}
      <div className="flex-1 max-w-xl">
        <button
          onClick={onOpenCommand}
          className="w-full flex items-center justify-between px-4 py-2.5 rounded-xl bg-tracora-surface/80 hover:bg-tracora-surface border border-tracora-border hover:border-tracora-cyan/40 transition-all text-sm text-tracora-muted group cursor-pointer shadow-inner"
        >
          <div className="flex items-center gap-3">
            <Search className="w-4 h-4 text-tracora-muted group-hover:text-tracora-cyan transition-colors" />
            <span className="text-slate-400 group-hover:text-slate-200 text-xs sm:text-sm font-sans truncate">
              Search assets, employees, locations, or serials...
            </span>
          </div>
          <div className="hidden sm:flex items-center gap-1 font-mono text-[11px] bg-white/[0.06] px-2 py-0.5 rounded-md text-slate-400 border border-white/10">
            <Command className="w-3 h-3" />
            <span>K</span>
          </div>
        </button>
      </div>

      {/* Action Controls & Profile */}
      <div className="flex items-center gap-3">
        {/* First-Class Scanner Action */}
        <button
          onClick={onOpenScanner}
          className="flex items-center gap-2 px-3.5 py-2 rounded-xl bg-tracora-cyan/10 hover:bg-tracora-cyan/20 border border-tracora-cyan/30 hover:border-tracora-cyan text-tracora-cyan text-xs font-semibold tracking-wide transition-all shadow-hud-badge"
          title="Open Asset Viewfinder"
        >
          <QrCode className="w-4 h-4" />
          <span className="hidden md:inline">Scan Code</span>
        </button>

        {/* Notifications / Attention Indicator */}
        <div className="relative">
          <button
            onClick={onOpenCommand}
            className="p-2.5 rounded-xl bg-tracora-surface hover:bg-white/5 border border-tracora-border text-slate-300 hover:text-white transition-all relative"
            title={`${alertsCount} Attention Items`}
          >
            <Bell className="w-4 h-4" />
            {alertsCount > 0 && (
              <span className="absolute -top-1 -right-1 w-4 h-4 rounded-full bg-tracora-amber text-[10px] font-bold text-black flex items-center justify-center font-mono ring-2 ring-tracora-void">
                {alertsCount > 9 ? '9+' : alertsCount}
              </span>
            )}
          </button>
        </div>

        <div className="h-6 w-px bg-tracora-border/80 mx-1 hidden sm:block" />

        {/* User Profile Pill */}
        <div className="flex items-center gap-3 pl-1 pr-3 py-1.5 rounded-full bg-tracora-surface/60 border border-tracora-border/80">
          <div className="w-8 h-8 rounded-full bg-gradient-to-tr from-tracora-blue to-tracora-cyan p-0.5">
            <div className="w-full h-full rounded-full bg-tracora-void flex items-center justify-center overflow-hidden">
              <span className="text-xs font-bold text-tracora-cyan">K</span>
            </div>
          </div>
          <div className="hidden sm:flex flex-col text-left">
            <span className="text-xs font-semibold text-white leading-tight font-sans">Kishore</span>
            <span className="text-[10px] text-tracora-cyan font-mono uppercase tracking-wider">IT Admin</span>
          </div>
        </div>
      </div>
    </header>
  );
}
