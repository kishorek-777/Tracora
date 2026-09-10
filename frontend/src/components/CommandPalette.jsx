import React, { useState, useEffect } from 'react';
import { Search, X, Laptop, User, MapPin, ArrowRight, CornerDownLeft } from 'lucide-react';
import { searchAssetsApi } from '../api/tracoraClient';

export default function CommandPalette({ isOpen, onClose, onSelectAsset, onOpenScanner }) {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState({ assets: [], employees: [], locations: [] });
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const handleKeyDown = (e) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault();
        if (isOpen) onClose();
        else onOpenScanner ? onOpenScanner() : null;
      }
      if (e.key === 'Escape' && isOpen) {
        onClose();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, onClose, onOpenScanner]);

  useEffect(() => {
    if (!query || query.length < 2) {
      setResults({ assets: [], employees: [], locations: [] });
      return;
    }
    let cancelled = false;
    const search = async () => {
      setLoading(true);
      try {
        const res = await searchAssetsApi(query);
        if (!cancelled && res) {
          setResults(res);
        }
      } catch (err) {
        console.error(err);
      } finally {
        if (!cancelled) setLoading(false);
      }
    };
    const timer = setTimeout(search, 200);
    return () => {
      cancelled = true;
      clearTimeout(timer);
    };
  }, [query]);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-start justify-center pt-20 p-4 bg-black/75 backdrop-blur-sm animate-fade-in">
      <div className="w-full max-w-2xl rounded-2xl bg-tracora-surface border border-tracora-border shadow-2xl overflow-hidden relative flex flex-col max-h-[70vh]">
        {/* Search Input Bar */}
        <div className="flex items-center px-4 py-3.5 border-b border-tracora-border/80 bg-tracora-void/50">
          <Search className="w-5 h-5 text-tracora-cyan mr-3 flex-shrink-0" />
          <input
            type="text"
            autoFocus
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Type an asset tag, serial, employee name, or location..."
            className="flex-1 bg-transparent text-sm text-white placeholder:text-tracora-muted focus:outline-none font-sans"
          />
          {query && (
            <button onClick={() => setQuery('')} className="p-1 text-slate-400 hover:text-white">
              <X className="w-4 h-4" />
            </button>
          )}
          <button onClick={onClose} className="p-1 ml-2 text-slate-400 hover:text-white">
            <kbd className="px-1.5 py-0.5 text-[10px] font-mono bg-white/[0.08] rounded border border-white/10">ESC</kbd>
          </button>
        </div>

        {/* Results Area */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {!query && (
            <div className="py-8 text-center text-slate-400 space-y-2">
              <span className="text-xs font-mono uppercase tracking-wider text-tracora-muted">
                Fast Navigation Suggestions
              </span>
              <div className="flex justify-center gap-2 pt-2">
                {['MacBook Pro', 'Dell Monitor', 'Rohan Mehta', 'Hyderabad'].map((item) => (
                  <button
                    key={item}
                    onClick={() => setQuery(item)}
                    className="px-2.5 py-1 rounded-lg bg-white/[0.03] hover:bg-white/[0.08] border border-white/10 text-xs text-slate-300 font-mono"
                  >
                    {item}
                  </button>
                ))}
              </div>
            </div>
          )}

          {results.assets && results.assets.length > 0 && (
            <div>
              <span className="text-[10px] font-mono uppercase tracking-wider text-tracora-cyan px-2 mb-1 block">
                Hardware Nodes ({results.assets.length})
              </span>
              <div className="space-y-1">
                {results.assets.map((asset) => (
                  <div
                    key={asset.name}
                    onClick={() => {
                      onSelectAsset(asset);
                      onClose();
                    }}
                    className="flex items-center justify-between p-2.5 rounded-xl hover:bg-white/[0.05] transition-colors cursor-pointer group"
                  >
                    <div className="flex items-center gap-3">
                      <Laptop className="w-4 h-4 text-tracora-cyan" />
                      <div>
                        <div className="text-xs font-bold text-white group-hover:text-tracora-cyan transition-colors">
                          {asset.asset_name}
                        </div>
                        <div className="text-[10px] font-mono text-slate-400">
                          {asset.asset_tag} · SN: {asset.serial_no || '—'}
                        </div>
                      </div>
                    </div>
                    <span className="text-[11px] font-mono text-slate-500 flex items-center gap-1">
                      <span>{asset.status}</span>
                      <CornerDownLeft className="w-3 h-3 text-slate-400 group-hover:text-white" />
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {results.employees && results.employees.length > 0 && (
            <div>
              <span className="text-[10px] font-mono uppercase tracking-wider text-emerald-400 px-2 mb-1 block">
                Personnel / Custodians ({results.employees.length})
              </span>
              <div className="space-y-1">
                {results.employees.map((emp) => (
                  <div
                    key={emp.name}
                    className="flex items-center justify-between p-2.5 rounded-xl hover:bg-white/[0.05] transition-colors cursor-pointer group"
                  >
                    <div className="flex items-center gap-3">
                      <User className="w-4 h-4 text-emerald-400" />
                      <div>
                        <div className="text-xs font-bold text-white">{emp.employee_name}</div>
                        <div className="text-[10px] font-mono text-slate-400">
                          {emp.company} · {emp.department}
                        </div>
                      </div>
                    </div>
                    <span className="text-[11px] font-mono text-emerald-400">● {emp.status}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {results.locations && results.locations.length > 0 && (
            <div>
              <span className="text-[10px] font-mono uppercase tracking-wider text-purple-400 px-2 mb-1 block">
                Locations ({results.locations.length})
              </span>
              <div className="space-y-1">
                {results.locations.map((loc) => (
                  <div
                    key={loc.name}
                    className="flex items-center justify-between p-2.5 rounded-xl hover:bg-white/[0.05] transition-colors cursor-pointer group"
                  >
                    <div className="flex items-center gap-3">
                      <MapPin className="w-4 h-4 text-purple-400" />
                      <div className="text-xs font-bold text-white">{loc.location_name || loc.name}</div>
                    </div>
                    <span className="text-[11px] font-mono text-slate-400">Node</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Command Bar Footer */}
        <div className="p-3 border-t border-tracora-border/80 bg-tracora-void/80 flex items-center justify-between text-[11px] font-mono text-slate-500">
          <div className="flex items-center gap-4">
            <span>↑↓ Navigate</span>
            <span>↵ Select</span>
            <span>ESC Close</span>
          </div>
          <span>Tracora Command Palette</span>
        </div>
      </div>
    </div>
  );
}
