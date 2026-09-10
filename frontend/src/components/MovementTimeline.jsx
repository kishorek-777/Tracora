import React from 'react';
import {
  UserCheck,
  MapPin,
  PlusCircle,
  Wrench,
  RotateCcw,
  Clock,
  ArrowUpRight,
  ShieldCheck
} from 'lucide-react';

export default function MovementTimeline({ movements, onSelectAsset }) {
  const list = movements && movements.length > 0 ? movements : [
    {
      asset: 'TRC-001234',
      asset_tag: 'TRC-001234',
      asset_name: 'MacBook Pro 14"',
      movement_type: 'Assign',
      to_employee_name: 'Rohan Mehta',
      recorded_by_name: 'Administrator',
      location: 'Hyderabad Tech Center',
      remarks: 'Q3 Hardware refresh',
      time_ago: '2h ago',
    },
    {
      asset: 'TRC-001233',
      asset_tag: 'TRC-001233',
      asset_name: 'Dell UltraSharp 27"',
      movement_type: 'Relocate',
      to_employee_name: 'Priya Sharma',
      recorded_by_name: 'Administrator',
      location: 'Bangalore HQ',
      remarks: 'Transferred to Floor 4',
      time_ago: '4h ago',
    },
    {
      asset: 'TRC-001228',
      asset_tag: 'TRC-001228',
      asset_name: 'Cisco Catalyst 9200L',
      movement_type: 'Send to Maintenance',
      recorded_by_name: 'Kishore',
      location: 'Bangalore HQ',
      remarks: 'Port 12 PoE issue',
      time_ago: '8h ago',
    },
    {
      asset: 'TRC-001229',
      asset_tag: 'TRC-001229',
      asset_name: 'Logitech MX Master',
      movement_type: 'Unassign',
      recorded_by_name: 'Administrator',
      location: 'Chennai Central Warehouse',
      remarks: 'Project offboarding',
      time_ago: '1d ago',
    },
  ];

  const getEventVisual = (type) => {
    const t = (type || '').toLowerCase();
    if (t.includes('assign')) {
      return {
        icon: UserCheck,
        bg: 'bg-emerald-500/15',
        text: 'text-emerald-400',
        border: 'border-emerald-500/30',
        label: 'Asset Assigned',
      };
    }
    if (t.includes('relocate') || t.includes('location')) {
      return {
        icon: MapPin,
        bg: 'bg-cyan-500/15',
        text: 'text-tracora-cyan',
        border: 'border-cyan-500/30',
        label: 'Location Updated',
      };
    }
    if (t.includes('maintenance')) {
      return {
        icon: Wrench,
        bg: 'bg-amber-500/15',
        text: 'text-amber-400',
        border: 'border-amber-500/30',
        label: 'Maintenance Scheduled',
      };
    }
    if (t.includes('unassign') || t.includes('return')) {
      return {
        icon: RotateCcw,
        bg: 'bg-purple-500/15',
        text: 'text-purple-400',
        border: 'border-purple-500/30',
        label: 'Asset Returned',
      };
    }
    return {
      icon: PlusCircle,
      bg: 'bg-blue-500/15',
      text: 'text-blue-400',
      border: 'border-blue-500/30',
      label: 'Asset Registered',
    };
  };

  return (
    <div className="p-6 rounded-2xl bg-tracora-surface/80 border border-tracora-border relative overflow-hidden flex flex-col justify-between">
      <div>
        <div className="flex items-center justify-between mb-5">
          <div className="flex items-center gap-2">
            <Clock className="w-4 h-4 text-tracora-cyan" />
            <h3 className="text-base font-bold text-white tracking-tight">Recent Activity</h3>
          </div>
          <button
            onClick={() => onSelectAsset && onSelectAsset(null)}
            className="text-xs font-mono text-tracora-cyan hover:underline flex items-center gap-1"
          >
            <span>View All</span>
            <ArrowUpRight className="w-3.5 h-3.5" />
          </button>
        </div>

        <div className="space-y-4 relative">
          {/* Vertical Connecting Line */}
          <div className="absolute top-3 bottom-3 left-4 w-px bg-white/[0.08]" />

          {list.map((m, index) => {
            const visual = getEventVisual(m.movement_type);
            const Icon = visual.icon;
            return (
              <div
                key={index}
                className="flex items-start gap-3.5 relative group cursor-pointer"
                onClick={() => onSelectAsset && onSelectAsset({ asset_tag: m.asset_tag, name: m.asset })}
              >
                <div
                  className={`w-8 h-8 rounded-xl ${visual.bg} ${visual.text} border ${visual.border} flex items-center justify-center flex-shrink-0 z-10 group-hover:scale-110 transition-transform`}
                >
                  <Icon className="w-4 h-4" />
                </div>

                <div className="flex-1 min-w-0 pt-0.5">
                  <div className="flex items-center justify-between gap-2">
                    <span className="text-xs font-bold text-white group-hover:text-tracora-cyan transition-colors">
                      {visual.label}
                    </span>
                    <span className="text-[10px] font-mono text-slate-500 whitespace-nowrap">
                      {m.time_ago}
                    </span>
                  </div>

                  <p className="text-xs text-slate-300 truncate mt-0.5 font-sans">
                    <span className="font-mono text-tracora-cyan font-semibold">
                      {m.asset_tag || m.asset}
                    </span>
                    {m.to_employee_name && (
                      <span> → assigned to <strong className="text-white">{m.to_employee_name}</strong></span>
                    )}
                  </p>

                  {m.remarks && (
                    <p className="text-[11px] text-slate-500 italic mt-0.5 truncate font-sans">
                      "{m.remarks}"
                    </p>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Immutable Trail Footer */}
      <div className="mt-5 pt-3 border-t border-tracora-border/60 flex items-center justify-between text-[10px] font-mono text-slate-500">
        <span className="flex items-center gap-1 text-slate-400">
          <ShieldCheck className="w-3 h-3 text-tracora-cyan" />
          Append-Only Trail
        </span>
        <span>Tamper Proof</span>
      </div>
    </div>
  );
}
