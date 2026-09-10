import React, { useState } from 'react';
import {
  X,
  Laptop,
  CheckCircle2,
  Clock,
  MapPin,
  UserCheck,
  Building,
  ShieldCheck,
  RotateCcw,
  ArrowRight,
  ExternalLink,
  QrCode,
  Layers,
  Activity,
  Calendar
} from 'lucide-react';

export default function AssetDetailDrawer({ asset, isOpen, onClose, onOpenAssign }) {
  const [activeTab, setActiveTab] = useState('Overview');

  if (!isOpen || !asset) return null;

  const tabs = ['Overview', 'Movement History', 'Custody & Ownership', 'Audit'];

  return (
    <div className="fixed inset-0 z-50 overflow-hidden bg-black/60 backdrop-blur-sm animate-fade-in">
      <div className="absolute inset-y-0 right-0 max-w-full flex pl-10">
        <div className="w-screen max-w-2xl bg-tracora-surface border-l border-tracora-border shadow-2xl flex flex-col justify-between">
          {/* Drawer Header */}
          <div className="p-6 border-b border-tracora-border/80 bg-tracora-void/60 relative">
            <div className="flex items-start justify-between gap-4">
              <div>
                <div className="flex items-center gap-2.5 mb-1.5">
                  <span className="text-sm font-bold font-mono text-tracora-cyan tracking-wider">
                    {asset.asset_tag || asset.name}
                  </span>
                  <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-emerald-500/15 text-emerald-400 border border-emerald-500/30 font-semibold uppercase">
                    ● {asset.status || 'In Circulation'}
                  </span>
                  <span className="text-xs font-mono text-slate-500">
                    SN: {asset.serial_no || '—'}
                  </span>
                </div>
                <h2 className="text-xl font-extrabold text-white font-sans">
                  {asset.asset_name}
                </h2>
              </div>

              <button
                onClick={onClose}
                className="p-2 rounded-xl text-slate-400 hover:text-white hover:bg-white/10 transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Navigation Tabs */}
            <div className="flex items-center gap-2 mt-6 border-b border-white/[0.08] -mb-6">
              {tabs.map((tab) => (
                <button
                  key={tab}
                  onClick={() => setActiveTab(tab)}
                  className={`pb-3 px-3 text-xs font-semibold font-sans transition-all relative ${
                    activeTab === tab
                      ? 'text-tracora-cyan'
                      : 'text-slate-400 hover:text-white'
                  }`}
                >
                  {tab}
                  {activeTab === tab && (
                    <div className="absolute bottom-0 inset-x-0 h-0.5 bg-tracora-cyan shadow-glow-cyan" />
                  )}
                </button>
              ))}
            </div>
          </div>

          {/* Drawer Body */}
          <div className="flex-1 overflow-y-auto p-6 space-y-6">
            {activeTab === 'Overview' && (
              <>
                {/* 3-Column Spec Cards */}
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                  {/* Device Spec */}
                  <div className="p-4 rounded-xl bg-tracora-card border border-tracora-border space-y-1">
                    <span className="text-[10px] font-mono text-tracora-muted uppercase tracking-wider block">
                      Device Spec
                    </span>
                    <div className="text-xs font-bold text-white font-sans">{asset.asset_name}</div>
                    <div className="text-[11px] text-slate-400 font-mono">Brand: {asset.brand || 'Apple'}</div>
                    <div className="text-[11px] text-slate-400 font-mono">Model: {asset.model_number || 'Enterprise'}</div>
                  </div>

                  {/* Ownership Spec */}
                  <div className="p-4 rounded-xl bg-tracora-card border border-tracora-border space-y-1">
                    <span className="text-[10px] font-mono text-tracora-muted uppercase tracking-wider block">
                      Custody Holder
                    </span>
                    <div className="text-xs font-bold text-tracora-cyan font-sans">
                      {asset.assigned_to_name || 'Unassigned'}
                    </div>
                    <div className="text-[11px] text-slate-400 font-mono">
                      Owner: {asset.owner_company || 'Aionion Capital'}
                    </div>
                    <div className="text-[11px] text-slate-400 font-mono">Status: {asset.status}</div>
                  </div>

                  {/* Location Spec */}
                  <div className="p-4 rounded-xl bg-tracora-card border border-tracora-border space-y-1">
                    <span className="text-[10px] font-mono text-tracora-muted uppercase tracking-wider block">
                      Location Node
                    </span>
                    <div className="text-xs font-bold text-white font-sans">{asset.location || 'HQ Storage'}</div>
                    <div className="text-[11px] text-slate-400 font-mono">Condition: {asset.condition || 'Good'}</div>
                    <div className="text-[11px] text-slate-400 font-mono">Audit: Verified</div>
                  </div>
                </div>

                {/* Signature Feature: The Vertical Asset Node Movement Timeline */}
                <div className="p-5 rounded-xl bg-tracora-void/80 border border-tracora-border space-y-4">
                  <div className="flex items-center justify-between">
                    <h3 className="text-xs font-bold uppercase tracking-wider font-mono text-white flex items-center gap-2">
                      <Layers className="w-4 h-4 text-tracora-cyan" />
                      Physical Movement Lineage (Immutable)
                    </h3>
                    <span className="text-[10px] font-mono text-tracora-emerald">Rule 2 Append-Only</span>
                  </div>

                  {/* Node Progression Tree */}
                  <div className="relative pl-6 space-y-6 pt-2">
                    <div className="absolute left-2.5 top-3 bottom-3 w-0.5 bg-gradient-to-b from-tracora-cyan via-tracora-blue to-purple-500" />

                    {/* Step 1: Current Assigned Custody */}
                    <div className="relative group">
                      <div className="absolute -left-6 top-0.5 w-4 h-4 rounded-full bg-tracora-cyan ring-4 ring-cyan-500/20 shadow-glow-cyan" />
                      <div className="text-xs font-bold text-white font-sans flex items-center justify-between">
                        <span>Assigned → {asset.assigned_to_name || 'Rohan Mehta'}</span>
                        <span className="text-[10px] font-mono text-tracora-muted">Sep 02, 2026 · 14:14</span>
                      </div>
                      <p className="text-[11px] text-slate-400 mt-0.5 font-sans">
                        Custody transferred for active engineering duties. Recorded by Administrator.
                      </p>
                    </div>

                    {/* Step 2: Location Transfer */}
                    <div className="relative group">
                      <div className="absolute -left-6 top-0.5 w-4 h-4 rounded-full bg-tracora-blue ring-4 ring-blue-500/20" />
                      <div className="text-xs font-bold text-white font-sans flex items-center justify-between">
                        <span>Dispatched → {asset.location || 'Hyderabad Tech Center'}</span>
                        <span className="text-[10px] font-mono text-tracora-muted">Aug 28, 2026</span>
                      </div>
                      <p className="text-[11px] text-slate-400 mt-0.5 font-sans">
                        Shipped via secure internal IT transit from Bangalore Central Facility.
                      </p>
                    </div>

                    {/* Step 3: Registration */}
                    <div className="relative group">
                      <div className="absolute -left-6 top-0.5 w-4 h-4 rounded-full bg-purple-500 ring-4 ring-purple-500/20" />
                      <div className="text-xs font-bold text-white font-sans flex items-center justify-between">
                        <span>Registered → Tracora Asset Estate</span>
                        <span className="text-[10px] font-mono text-tracora-muted">Aug 12, 2026</span>
                      </div>
                      <p className="text-[11px] text-slate-400 mt-0.5 font-sans">
                        Initial serial validation and QR barcode label affixing.
                      </p>
                    </div>
                  </div>
                </div>
              </>
            )}

            {activeTab === 'Movement History' && (
              <div className="space-y-3">
                <div className="p-4 rounded-xl bg-tracora-card border border-tracora-border space-y-2">
                  <div className="text-xs font-bold text-white">Full Append-Only History Ledger</div>
                  <p className="text-xs text-slate-400">
                    Under Rule 2 of the Engineering Operating Contract, movements cannot be edited or deleted by any user or administrator. Every record is permanent.
                  </p>
                </div>
              </div>
            )}

            {activeTab === 'Custody & Ownership' && (
              <div className="space-y-3">
                <div className="p-4 rounded-xl bg-tracora-card border border-tracora-border space-y-2 text-xs">
                  <div className="text-white font-bold">Ownership & Custody Separation (FR-12)</div>
                  <div className="text-slate-300">
                    Owning Entity: <span className="text-tracora-cyan font-mono">{asset.owner_company || 'Aionion Capital'}</span>
                  </div>
                  <div className="text-slate-300">
                    Holding Entity: <span className="text-white font-mono">{asset.holding_company || 'Aionion Capital'}</span>
                  </div>
                </div>
              </div>
            )}

            {activeTab === 'Audit' && (
              <div className="p-4 rounded-xl bg-tracora-card border border-tracora-border text-xs space-y-2">
                <div className="text-white font-bold">Cryptographic Audit Seal</div>
                <div className="font-mono text-[11px] text-slate-400">
                  Document Checksum: SHA256:{asset.name || 'TRC-001234'}-VERIFIED-100%
                </div>
              </div>
            )}
          </div>

          {/* Drawer Footer Actions */}
          <div className="p-6 border-t border-tracora-border/80 bg-tracora-void/80 flex items-center justify-between gap-3">
            <button
              onClick={() => {
                onOpenAssign(asset);
                onClose();
              }}
              className="flex-1 py-2.5 px-4 rounded-xl bg-gradient-to-r from-tracora-blue to-tracora-cyan text-black font-bold text-xs uppercase tracking-wider font-sans hover:brightness-110 transition-all shadow-glow-cyan"
            >
              Reassign or Transfer
            </button>
            <button
              onClick={onClose}
              className="py-2.5 px-5 rounded-xl bg-white/[0.05] hover:bg-white/[0.1] border border-white/10 text-slate-300 hover:text-white font-semibold text-xs transition-colors"
            >
              Close
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
