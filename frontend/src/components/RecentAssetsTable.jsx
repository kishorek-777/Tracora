import React, { useState } from 'react';
import {
  Laptop,
  Monitor,
  Smartphone,
  Mouse,
  HardDrive,
  MoreVertical,
  ArrowUpRight,
  ExternalLink,
  ShieldCheck,
  Search
} from 'lucide-react';

export default function RecentAssetsTable({ assets, onSelectAsset }) {
  const [filter, setFilter] = useState('');

  const list = assets && assets.length > 0 ? assets : [];

  const filtered = list.filter((a) => {
    if (!filter) return true;
    const q = filter.toLowerCase();
    return (
      (a.asset_tag && a.asset_tag.toLowerCase().includes(q)) ||
      (a.asset_name && a.asset_name.toLowerCase().includes(q)) ||
      (a.assigned_to_name && a.assigned_to_name.toLowerCase().includes(q)) ||
      (a.location && a.location.toLowerCase().includes(q)) ||
      (a.serial_no && a.serial_no.toLowerCase().includes(q))
    );
  });

  const getCategoryIcon = (category) => {
    const c = (category || '').toLowerCase();
    if (c.includes('laptop')) return Laptop;
    if (c.includes('monitor') || c.includes('display')) return Monitor;
    if (c.includes('phone') || c.includes('mobile')) return Smartphone;
    if (c.includes('mouse') || c.includes('keyboard') || c.includes('accessory')) return Mouse;
    return HardDrive;
  };

  const getStatusBadge = (status) => {
    const s = (status || '').toLowerCase();
    if (s.includes('circulation') || s.includes('assigned')) {
      return (
        <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[11px] font-mono font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">
          <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
          Assigned
        </span>
      );
    }
    if (s.includes('store') || s.includes('available')) {
      return (
        <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[11px] font-mono font-semibold bg-purple-500/10 text-purple-400 border border-purple-500/30">
          <span className="w-1.5 h-1.5 rounded-full bg-purple-400" />
          Available
        </span>
      );
    }
    if (s.includes('maintenance')) {
      return (
        <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[11px] font-mono font-semibold bg-amber-500/10 text-amber-400 border border-amber-500/30">
          <span className="w-1.5 h-1.5 rounded-full bg-amber-400 animate-ping" />
          Maintenance
        </span>
      );
    }
    return (
      <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[11px] font-mono font-semibold bg-slate-500/10 text-slate-400 border border-slate-500/30">
        {status || 'Unknown'}
      </span>
    );
  };

  return (
    <div className="p-6 rounded-2xl bg-tracora-surface/80 border border-tracora-border shadow-sm flex flex-col justify-between">
      <div>
        {/* Table Header Controls */}
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 mb-5">
          <div>
            <h3 className="text-base font-bold text-white tracking-tight">Recent Assets Register</h3>
            <p className="text-xs text-tracora-muted font-sans">Active hardware nodes under management</p>
          </div>

          <div className="flex items-center gap-3 w-full sm:w-auto">
            <div className="relative flex-1 sm:w-60">
              <Search className="w-3.5 h-3.5 text-tracora-muted absolute left-3 top-2.5" />
              <input
                type="text"
                value={filter}
                onChange={(e) => setFilter(e.target.value)}
                placeholder="Filter tag, holder, serial..."
                className="w-full pl-8 pr-3 py-1.5 rounded-xl bg-tracora-card border border-tracora-border text-xs text-white placeholder:text-tracora-muted focus:outline-none focus:border-tracora-cyan/50 font-sans"
              />
            </div>
            <button
              onClick={() => onSelectAsset && onSelectAsset(list[0])}
              className="text-xs font-mono text-tracora-cyan hover:underline flex items-center gap-1 flex-shrink-0"
            >
              <span>View All</span>
              <ArrowUpRight className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>

        {/* Data Table */}
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs font-sans">
            <thead>
              <tr className="border-b border-tracora-border/80 text-[11px] font-mono uppercase tracking-wider text-tracora-muted">
                <th className="pb-3 pl-2">Asset ID</th>
                <th className="pb-3">Device Name</th>
                <th className="pb-3">Category</th>
                <th className="pb-3">Assigned To</th>
                <th className="pb-3">Location</th>
                <th className="pb-3">Status</th>
                <th className="pb-3 pr-2 text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/[0.04]">
              {filtered.map((asset) => {
                const CategoryIcon = getCategoryIcon(asset.category);
                return (
                  <tr
                    key={asset.name || asset.asset_tag}
                    onClick={() => onSelectAsset && onSelectAsset(asset)}
                    className="hover:bg-white/[0.03] transition-colors cursor-pointer group"
                  >
                    {/* Asset ID */}
                    <td className="py-3 pl-2 font-mono font-bold text-tracora-cyan group-hover:underline">
                      {asset.asset_tag || asset.name}
                    </td>

                    {/* Device Name & Brand */}
                    <td className="py-3">
                      <div className="flex items-center gap-2.5">
                        <div className="w-7 h-7 rounded-lg bg-tracora-card border border-tracora-border flex items-center justify-center text-slate-300 group-hover:text-tracora-cyan transition-colors">
                          <CategoryIcon className="w-3.5 h-3.5" />
                        </div>
                        <div>
                          <div className="font-semibold text-white group-hover:text-tracora-cyan transition-colors">
                            {asset.asset_name}
                          </div>
                          <div className="text-[10px] font-mono text-slate-500">
                            SN: {asset.serial_no || '—'}
                          </div>
                        </div>
                      </div>
                    </td>

                    {/* Category */}
                    <td className="py-3 font-mono text-slate-300">
                      {asset.category || 'Hardware'}
                    </td>

                    {/* Assigned To */}
                    <td className="py-3">
                      {asset.assigned_to_name && asset.assigned_to_name !== 'Unassigned' ? (
                        <div className="font-medium text-slate-200">
                          {asset.assigned_to_name}
                        </div>
                      ) : (
                        <span className="text-slate-500 font-mono text-[11px] italic">
                          Unassigned
                        </span>
                      )}
                    </td>

                    {/* Location */}
                    <td className="py-3 font-mono text-slate-400">
                      {asset.location}
                    </td>

                    {/* Status */}
                    <td className="py-3">
                      {getStatusBadge(asset.status)}
                    </td>

                    {/* Action */}
                    <td className="py-3 pr-2 text-right">
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          onSelectAsset && onSelectAsset(asset);
                        }}
                        className="p-1 rounded-lg hover:bg-white/10 text-tracora-muted hover:text-white transition-colors"
                        title="Inspect Asset"
                      >
                        <ExternalLink className="w-3.5 h-3.5" />
                      </button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
