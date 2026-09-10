import React, { useState } from 'react';
import {
  LayoutDashboard,
  Cpu,
  ArrowLeftRight,
  History,
  Wrench,
  Users,
  Building2,
  GitFork,
  MapPin,
  FileBarChart2,
  LineChart,
  ShieldCheck,
  Settings,
  ChevronRight,
  ChevronDown,
  Sparkles,
  Radio,
  PanelLeftClose,
  PanelLeft
} from 'lucide-react';

export default function Sidebar({ activeNav, setActiveNav, onOpenScanner, isCollapsed, setIsCollapsed }) {
  const [assetControlOpen, setAssetControlOpen] = useState(true);

  const navSections = [
    {
      label: 'OVERVIEW',
      items: [
        { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard }
      ]
    },
    {
      label: 'ASSET CONTROL',
      items: [
        { id: 'assets', label: 'Assets', icon: Cpu, badge: '684' },
        { id: 'assignments', label: 'Assignments', icon: ArrowLeftRight },
        { id: 'movements', label: 'Movements', icon: History },
        { id: 'maintenance', label: 'Maintenance', icon: Wrench, badge: '18', badgeAlert: true },
      ]
    },
    {
      label: 'ORGANIZATION',
      items: [
        { id: 'employees', label: 'Employees', icon: Users },
        { id: 'companies', label: 'Companies', icon: Building2 },
        { id: 'departments', label: 'Departments', icon: GitFork },
        { id: 'locations', label: 'Locations', icon: MapPin },
      ]
    },
    {
      label: 'INTELLIGENCE',
      items: [
        { id: 'reports', label: 'Reports', icon: FileBarChart2 },
        { id: 'analytics', label: 'Analytics', icon: LineChart },
        { id: 'audit', label: 'Audit Log', icon: ShieldCheck },
      ]
    },
    {
      label: 'SYSTEM',
      items: [
        { id: 'settings', label: 'Settings', icon: Settings }
      ]
    }
  ];

  return (
    <aside
      className={`fixed top-0 left-0 bottom-0 z-30 flex flex-col bg-tracora-surface/95 backdrop-blur-xl border-r border-tracora-border transition-all duration-300 ${
        isCollapsed ? 'w-20' : 'w-64'
      }`}
    >
      {/* Brand Header */}
      <div className="h-20 flex items-center justify-between px-5 border-b border-tracora-border/60">
        <div className="flex items-center gap-3 overflow-hidden cursor-pointer" onClick={() => setActiveNav('dashboard')}>
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-tracora-blue to-tracora-cyan flex items-center justify-center shadow-glow-cyan flex-shrink-0 relative group">
            <div className="absolute inset-0 rounded-xl bg-tracora-cyan opacity-0 group-hover:opacity-30 transition-opacity blur-sm" />
            <span className="font-extrabold text-black text-xl tracking-tighter font-sans">T</span>
          </div>
          {!isCollapsed && (
            <div className="flex flex-col min-w-0">
              <span className="font-bold text-lg tracking-wider text-white font-sans flex items-center gap-1.5">
                TRACORA
                <span className="w-1.5 h-1.5 rounded-full bg-tracora-cyan animate-pulse" />
              </span>
              <span className="text-[10px] uppercase tracking-widest text-tracora-muted font-medium">
                Track · Manage · Protect
              </span>
            </div>
          )}
        </div>

        <button
          onClick={() => setIsCollapsed(!isCollapsed)}
          className="text-tracora-muted hover:text-white p-1.5 rounded-lg hover:bg-white/5 transition-colors"
          title={isCollapsed ? "Expand sidebar" : "Collapse sidebar"}
        >
          {isCollapsed ? <PanelLeft className="w-4 h-4" /> : <PanelLeftClose className="w-4 h-4" />}
        </button>
      </div>

      {/* Nav List */}
      <div className="flex-1 overflow-y-auto px-3 py-4 space-y-6">
        {navSections.map((section) => (
          <div key={section.label} className="space-y-1">
            {!isCollapsed && (
              <div className="px-3 pb-1 text-[10px] font-bold tracking-wider text-tracora-muted/80 uppercase font-mono">
                {section.label}
              </div>
            )}
            <div className="space-y-0.5">
              {section.items.map((item) => {
                const Icon = item.icon;
                const isActive = activeNav === item.id;
                return (
                  <button
                    key={item.id}
                    onClick={() => setActiveNav(item.id)}
                    className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-all group relative ${
                      isActive
                        ? 'bg-gradient-to-r from-tracora-blue/25 to-tracora-cyan/15 text-tracora-cyan border border-tracora-cyan/35 shadow-hud-badge'
                        : 'text-tracora-text-secondary hover:text-white hover:bg-white/[0.04]'
                    }`}
                    title={isCollapsed ? item.label : undefined}
                  >
                    <Icon
                      className={`w-4 h-4 flex-shrink-0 transition-transform group-hover:scale-110 ${
                        isActive ? 'text-tracora-cyan drop-shadow-[0_0_8px_rgba(0,229,255,0.6)]' : 'text-slate-400 group-hover:text-slate-200'
                      }`}
                    />
                    {!isCollapsed && (
                      <span className="flex-1 text-left truncate">{item.label}</span>
                    )}

                    {!isCollapsed && item.badge && (
                      <span
                        className={`text-[10px] font-mono px-2 py-0.5 rounded-full font-semibold ${
                          item.badgeAlert
                            ? 'bg-tracora-amber/15 text-tracora-amber border border-tracora-amber/30'
                            : 'bg-white/5 text-slate-400'
                        }`}
                      >
                        {item.badge}
                      </span>
                    )}

                    {isActive && (
                      <div className="absolute left-0 top-2 bottom-2 w-1 rounded-r bg-tracora-cyan shadow-glow-cyan" />
                    )}
                  </button>
                );
              })}
            </div>
          </div>
        ))}
      </div>

      {/* Bottom Mission Control Card */}
      {!isCollapsed ? (
        <div className="p-4 border-t border-tracora-border/60 space-y-3">
          <div className="p-3.5 rounded-2xl bg-gradient-to-b from-tracora-card to-tracora-void border border-tracora-border/80 relative overflow-hidden group">
            <div className="absolute -right-6 -bottom-6 w-20 h-20 rounded-full bg-tracora-cyan/10 blur-xl group-hover:bg-tracora-cyan/20 transition-all" />
            <div className="flex items-center gap-2.5 mb-2">
              <div className="w-6 h-6 rounded-lg bg-tracora-cyan/10 border border-tracora-cyan/30 flex items-center justify-center">
                <Sparkles className="w-3.5 h-3.5 text-tracora-cyan" />
              </div>
              <span className="text-xs font-semibold text-white tracking-tight">Industrial HUD</span>
            </div>
            <p className="text-[11px] text-slate-400 leading-relaxed font-sans">
              Smarter Asset Management — for a stronger tomorrow.
            </p>
          </div>

          <div className="flex items-center justify-between text-[11px] text-tracora-muted px-1 font-mono">
            <span className="flex items-center gap-1.5 text-tracora-emerald">
              <span className="w-2 h-2 rounded-full bg-tracora-emerald animate-ping" />
              System Online
            </span>
            <span className="text-slate-500">v2.0.0</span>
          </div>
        </div>
      ) : (
        <div className="p-3 border-t border-tracora-border/60 flex flex-col items-center gap-2 text-tracora-muted">
          <span className="w-2 h-2 rounded-full bg-tracora-emerald" title="System Online" />
        </div>
      )}
    </aside>
  );
}
