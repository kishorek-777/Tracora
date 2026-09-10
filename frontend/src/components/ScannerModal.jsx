import React, { useState } from 'react';
import {
  X,
  QrCode,
  Scan,
  Camera,
  Search,
  CheckCircle2,
  AlertCircle,
  ExternalLink,
  ArrowRight,
  UserCheck,
  MapPin,
  RefreshCw,
  Clock
} from 'lucide-react';
import { scanAssetApi } from '../api/tracoraClient';

export default function ScannerModal({ isOpen, onClose, onInspectAsset, onOpenAssign }) {
  const [manualCode, setManualCode] = useState('');
  const [scannedResult, setScannedResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  if (!isOpen) return null;

  const recentScans = ['TRC-001234', 'TRC-001233', 'TRC-001230', 'TRC-000012'];

  const handleScan = async (code) => {
    if (!code) return;
    setLoading(true);
    setError(null);
    try {
      const res = await scanAssetApi(code);
      if (res && res.asset) {
        setScannedResult(res);
      } else {
        setError(`No asset found for tag or serial: ${code}`);
      }
    } catch (err) {
      setError('Scan resolution error. Verify asset tag and network.');
    } finally {
      setLoading(false);
    }
  };

  const handleManualSubmit = (e) => {
    e.preventDefault();
    handleScan(manualCode);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-md animate-fade-in">
      <div className="w-full max-w-lg rounded-2xl bg-tracora-surface border border-tracora-border shadow-2xl overflow-hidden relative">
        {/* Modal Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-tracora-border/80">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-tracora-cyan/15 text-tracora-cyan flex items-center justify-center border border-tracora-cyan/30">
              <Scan className="w-4 h-4" />
            </div>
            <div>
              <h3 className="text-sm font-bold text-white font-sans uppercase tracking-wider">
                First-Class Asset Scanner
              </h3>
              <span className="text-[11px] font-mono text-tracora-muted">
                Point camera at physical label or enter tag ID
              </span>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-white/10 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Viewfinder Content */}
        <div className="p-6 space-y-5">
          {!scannedResult ? (
            <>
              {/* Laser Optical Viewfinder */}
              <div className="h-56 rounded-xl bg-tracora-void border-2 border-dashed border-tracora-border/80 relative overflow-hidden flex flex-col items-center justify-center group">
                {/* Laser scan line animation */}
                <div className="absolute inset-x-0 h-0.5 bg-gradient-to-r from-transparent via-tracora-cyan to-transparent animate-scanline shadow-glow-cyan" />

                {/* HUD Corners */}
                <div className="absolute top-3 left-3 w-4 h-4 border-t-2 border-l-2 border-tracora-cyan" />
                <div className="absolute top-3 right-3 w-4 h-4 border-t-2 border-r-2 border-tracora-cyan" />
                <div className="absolute bottom-3 left-3 w-4 h-4 border-b-2 border-l-2 border-tracora-cyan" />
                <div className="absolute bottom-3 right-3 w-4 h-4 border-b-2 border-r-2 border-tracora-cyan" />

                <div className="flex flex-col items-center gap-3 text-center z-10 px-4">
                  <div className="w-14 h-14 rounded-2xl bg-white/[0.04] border border-white/10 flex items-center justify-center text-slate-400 group-hover:text-tracora-cyan group-hover:border-tracora-cyan/40 transition-all">
                    <Camera className="w-7 h-7" />
                  </div>
                  <div>
                    <span className="text-xs font-semibold text-white font-sans block">
                      Align QR or 1D Barcode in Viewfinder
                    </span>
                    <span className="text-[11px] text-slate-500 font-mono mt-0.5 block">
                      Auto-detects Code128, QR, or TRC-Series labels
                    </span>
                  </div>
                </div>

                {loading && (
                  <div className="absolute inset-0 bg-tracora-void/90 flex flex-col items-center justify-center gap-2 z-20">
                    <RefreshCw className="w-6 h-6 text-tracora-cyan animate-spin" />
                    <span className="text-xs font-mono text-tracora-cyan">Resolving Hardware Node...</span>
                  </div>
                )}
              </div>

              {/* Manual Input Fallback */}
              <form onSubmit={handleManualSubmit} className="space-y-2">
                <div className="flex gap-2">
                  <div className="relative flex-1">
                    <Search className="w-4 h-4 text-tracora-muted absolute left-3 top-3" />
                    <input
                      type="text"
                      value={manualCode}
                      onChange={(e) => setManualCode(e.target.value)}
                      placeholder="Enter Asset ID or Serial (e.g. TRC-001234)..."
                      className="w-full pl-9 pr-3 py-2.5 rounded-xl bg-tracora-card border border-tracora-border focus:border-tracora-cyan text-sm text-white placeholder:text-tracora-muted font-mono uppercase focus:outline-none"
                    />
                  </div>
                  <button
                    type="submit"
                    disabled={!manualCode || loading}
                    className="px-5 py-2.5 rounded-xl bg-gradient-to-r from-tracora-blue to-tracora-cyan hover:brightness-110 disabled:opacity-40 text-black font-bold text-xs uppercase tracking-wider font-sans transition-all flex items-center gap-1.5 shadow-glow-cyan"
                  >
                    Resolve
                  </button>
                </div>
              </form>

              {/* Recent Scans Quick Pills */}
              <div>
                <span className="text-[11px] font-mono text-tracora-muted uppercase tracking-wider block mb-2">
                  Recent Scans:
                </span>
                <div className="flex flex-wrap gap-2">
                  {recentScans.map((tag) => (
                    <button
                      key={tag}
                      onClick={() => handleScan(tag)}
                      className="px-2.5 py-1 rounded-lg bg-white/[0.04] hover:bg-white/[0.08] border border-white/10 hover:border-tracora-cyan/40 text-xs font-mono text-slate-300 transition-colors"
                    >
                      {tag}
                    </button>
                  ))}
                </div>
              </div>

              {error && (
                <div className="p-3 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-400 text-xs flex items-center gap-2">
                  <AlertCircle className="w-4 h-4 flex-shrink-0" />
                  <span>{error}</span>
                </div>
              )}
            </>
          ) : (
            /* Resolved Asset Card with Post-Scan Actions */
            <div className="space-y-4">
              <div className="p-4 rounded-xl bg-tracora-void border border-tracora-cyan/40 shadow-hud-badge space-y-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-bold font-mono text-tracora-cyan">
                      {scannedResult.asset.asset_tag || scannedResult.asset.name}
                    </span>
                    <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-emerald-500/15 text-emerald-400 border border-emerald-500/30 font-semibold uppercase">
                      ● {scannedResult.asset.status}
                    </span>
                  </div>
                  <span className="text-[11px] font-mono text-slate-400">
                    SN: {scannedResult.asset.serial_no}
                  </span>
                </div>

                <div className="text-base font-bold text-white font-sans">
                  {scannedResult.asset.asset_name}
                </div>

                <div className="grid grid-cols-2 gap-2 text-xs font-mono pt-2 border-t border-white/[0.06]">
                  <div className="flex items-center gap-2 text-slate-300">
                    <UserCheck className="w-3.5 h-3.5 text-tracora-cyan" />
                    <span>{scannedResult.holder?.employee_name || 'Unassigned'}</span>
                  </div>
                  <div className="flex items-center gap-2 text-slate-300">
                    <MapPin className="w-3.5 h-3.5 text-tracora-cyan" />
                    <span className="truncate">{scannedResult.asset.location}</span>
                  </div>
                </div>
              </div>

              {/* Action Buttons */}
              <div className="space-y-2 pt-2">
                <button
                  onClick={() => {
                    onInspectAsset(scannedResult.asset);
                    onClose();
                  }}
                  className="w-full flex items-center justify-center gap-2 py-2.5 rounded-xl bg-tracora-cyan text-black font-bold text-xs uppercase tracking-wider font-sans hover:brightness-110 transition-all shadow-glow-cyan"
                >
                  <ExternalLink className="w-4 h-4" />
                  View Asset Full Telemetry
                </button>

                <div className="grid grid-cols-2 gap-2">
                  <button
                    onClick={() => {
                      onOpenAssign(scannedResult.asset);
                      onClose();
                    }}
                    className="py-2 px-3 rounded-xl bg-white/[0.05] hover:bg-white/[0.1] border border-white/10 text-white font-semibold text-xs transition-colors"
                  >
                    Change Assignment
                  </button>
                  <button
                    onClick={() => setScannedResult(null)}
                    className="py-2 px-3 rounded-xl bg-white/[0.05] hover:bg-white/[0.1] border border-white/10 text-slate-300 hover:text-white font-semibold text-xs transition-colors"
                  >
                    Scan Another
                  </button>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
