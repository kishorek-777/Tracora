import React from 'react';
import { MapPin, ArrowUpRight, Globe2, Building } from 'lucide-react';

export default function LocationDistribution({ locations, onSelectLocation }) {
  const locs = locations && locations.length > 0 ? locations : [
    { location: 'LOC-BLR', name: 'Bangalore HQ', city: 'Bangalore', count: 125 },
    { location: 'LOC-HYD', name: 'Hyderabad Tech Center', city: 'Hyderabad', count: 98 },
    { location: 'LOC-DEL', name: 'Delhi Regional Office', city: 'Delhi', count: 76 },
    { location: 'LOC-MUM', name: 'Mumbai Financial Office', city: 'Mumbai', count: 64 },
    { location: 'LOC-CHN', name: 'Chennai Central Warehouse', city: 'Chennai', count: 52 },
  ];

  return (
    <div className="p-6 rounded-2xl bg-tracora-surface/80 border border-tracora-border relative overflow-hidden flex flex-col justify-between">
      <div>
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <Globe2 className="w-4 h-4 text-tracora-cyan" />
            <h3 className="text-base font-bold text-white tracking-tight">Geographic Estate</h3>
          </div>
          <button
            onClick={() => onSelectLocation && onSelectLocation(null)}
            className="text-xs font-mono text-tracora-cyan hover:underline flex items-center gap-1"
          >
            <span>View All</span>
            <ArrowUpRight className="w-3.5 h-3.5" />
          </button>
        </div>

        {/* Technical Coordinate Map Visual */}
        <div className="h-32 rounded-xl bg-tracora-void/80 border border-tracora-border/60 relative overflow-hidden flex items-center justify-center p-3 mb-4">
          {/* Background Grid Pattern */}
          <div className="absolute inset-0 bg-grid-pattern opacity-40" />

          {/* Glowing Regional Nodes */}
          <div className="relative w-full h-full">
            {/* Delhi Node */}
            <div className="absolute top-4 left-1/2 transform -translate-x-1/2 flex items-center gap-1.5 cursor-pointer group">
              <span className="w-2.5 h-2.5 rounded-full bg-tracora-cyan shadow-glow-cyan animate-pulse" />
              <span className="text-[10px] font-mono text-slate-300 group-hover:text-white bg-tracora-surface/90 px-1.5 py-0.5 rounded border border-tracora-border">
                DEL · 76
              </span>
            </div>

            {/* Mumbai Node */}
            <div className="absolute top-14 left-1/4 flex items-center gap-1.5 cursor-pointer group">
              <span className="w-2 h-2 rounded-full bg-tracora-blue animate-pulse" />
              <span className="text-[10px] font-mono text-slate-300 group-hover:text-white bg-tracora-surface/90 px-1.5 py-0.5 rounded border border-tracora-border">
                MUM · 64
              </span>
            </div>

            {/* Hyderabad Node */}
            <div className="absolute top-16 left-1/2 flex items-center gap-1.5 cursor-pointer group">
              <span className="w-2.5 h-2.5 rounded-full bg-tracora-emerald shadow-hud-badge" />
              <span className="text-[10px] font-mono text-slate-300 group-hover:text-white bg-tracora-surface/90 px-1.5 py-0.5 rounded border border-tracora-border">
                HYD · 98
              </span>
            </div>

            {/* Bangalore Node */}
            <div className="absolute bottom-3 left-1/2 transform -translate-x-4 flex items-center gap-1.5 cursor-pointer group">
              <span className="w-3 h-3 rounded-full bg-tracora-cyan ring-4 ring-cyan-500/20 shadow-glow-cyan" />
              <span className="text-[10px] font-mono font-bold text-tracora-cyan bg-tracora-surface/90 px-2 py-0.5 rounded border border-tracora-cyan/40">
                BLR · 125
              </span>
            </div>

            {/* Chennai Node */}
            <div className="absolute bottom-4 right-1/4 flex items-center gap-1.5 cursor-pointer group">
              <span className="w-2 h-2 rounded-full bg-purple-400" />
              <span className="text-[10px] font-mono text-slate-300 group-hover:text-white bg-tracora-surface/90 px-1.5 py-0.5 rounded border border-tracora-border">
                CHN · 52
              </span>
            </div>
          </div>
        </div>

        {/* Location List Items */}
        <div className="space-y-2">
          {locs.slice(0, 5).map((loc) => (
            <div
              key={loc.location}
              onClick={() => onSelectLocation && onSelectLocation(loc)}
              className="flex items-center justify-between p-2.5 rounded-xl bg-tracora-card/50 hover:bg-tracora-card border border-tracora-border/60 hover:border-tracora-cyan/30 transition-all cursor-pointer group"
            >
              <div className="flex items-center gap-2.5 truncate">
                <MapPin className="w-3.5 h-3.5 text-tracora-cyan group-hover:scale-110 transition-transform flex-shrink-0" />
                <span className="text-xs font-semibold text-slate-200 group-hover:text-white truncate font-sans">
                  {loc.name || loc.city}
                </span>
              </div>
              <span className="text-xs font-mono font-bold text-tracora-cyan bg-tracora-cyan/10 px-2 py-0.5 rounded-md border border-tracora-cyan/20">
                {loc.count} assets
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
