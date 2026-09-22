import React, { useState, useEffect, useRef } from 'react';
import { Html5Qrcode } from 'html5-qrcode';
import {
  Camera,
  CameraOff,
  Search,
  X,
  ArrowLeft,
  Wifi,
  WifiOff,
  AlertCircle,
  Clock,
  Layers,
  Wrench,
  User,
  Building,
  MapPin,
  CheckCircle2,
  RefreshCw,
  SearchX,
  ScanLine,
  SlidersHorizontal,
} from 'lucide-react';

function getStatusBadge(status) {
  const norm = status || 'Unknown';
  let dotColor = 'bg-slate-500';
  let badgeClasses = 'bg-slate-100 text-slate-700 border-slate-300';

  if (norm === 'In Store') {
    dotColor = 'bg-blue-600';
    badgeClasses = 'bg-blue-50 text-blue-700 border-blue-200';
  } else if (norm === 'Assigned') {
    dotColor = 'bg-emerald-600';
    badgeClasses = 'bg-emerald-50 text-emerald-700 border-emerald-200';
  } else if (norm === 'Under Maintenance' || norm === 'Damaged') {
    dotColor = 'bg-amber-600';
    badgeClasses = 'bg-amber-50 text-amber-700 border-amber-200';
  } else if (norm === 'Lost') {
    dotColor = 'bg-rose-600';
    badgeClasses = 'bg-rose-50 text-rose-700 border-rose-200';
  } else if (norm === 'Recovered') {
    dotColor = 'bg-yellow-600';
    badgeClasses = 'bg-yellow-50 text-yellow-800 border-yellow-200';
  } else if (norm === 'Released' || norm === 'Retired') {
    dotColor = 'bg-slate-500';
    badgeClasses = 'bg-slate-100 text-slate-700 border-slate-300';
  }

  return (
    <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold border ${badgeClasses}`}>
      <span className={`w-2 h-2 rounded-full ${dotColor}`} />
      <span>{norm}</span>
    </span>
  );
}

export default function MobileApp() {
  // Shell tab state: 'scan' | 'lookup'
  const [activeTab, setActiveTab] = useState(() => {
    const path = window.location.pathname;
    return path.includes('/lookup') ? 'lookup' : 'scan';
  });

  // Screen state machine: 'SCAN' | 'RESULT' | 'MULTIPLE' | 'NOT_FOUND' | 'OFFLINE'
  const [screen, setScreen] = useState('SCAN');
  const [searchQuery, setSearchQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [isOnline, setIsOnline] = useState(navigator.onLine);

  // Camera state
  const [cameraActive, setCameraActive] = useState(true);
  const [cameraDenied, setCameraDenied] = useState(false);

  // Data state
  const [singleResult, setSingleResult] = useState(null);
  const [multipleResults, setMultipleResults] = useState([]);
  const [lastSearchedTerm, setLastSearchedTerm] = useState('');
  const [lastFailedQuery, setLastFailedQuery] = useState('');

  const inputRef = useRef(null);
  const scannerRef = useRef(null);

  // Sync tab with URL
  const switchTab = (tab) => {
    setActiveTab(tab);
    const targetUrl = tab === 'lookup' ? '/mobile/lookup' : '/mobile/scan';
    window.history.pushState(null, '', targetUrl);
    if (tab === 'lookup') {
      // In lookup tab, focus input and collapse camera
      setCameraActive(false);
      resetToScan(false);
      setTimeout(() => inputRef.current?.focus(), 150);
    } else {
      setCameraActive(true);
      resetToScan(true);
    }
  };

  // Connectivity listener
  useEffect(() => {
    const handleOnline = () => setIsOnline(true);
    const handleOffline = () => {
      setIsOnline(false);
      if (screen !== 'SCAN') {
        setScreen('OFFLINE');
      }
    };

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);
    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, [screen]);

  // Handle popstate for browser back/forward navigation within /mobile
  useEffect(() => {
    const handlePopState = () => {
      const path = window.location.pathname;
      if (path.includes('/lookup')) {
        setActiveTab('lookup');
        setCameraActive(false);
      } else {
        setActiveTab('scan');
        setCameraActive(true);
      }
      resetToScan(false);
    };
    window.addEventListener('popstate', handlePopState);
    return () => window.removeEventListener('popstate', handlePopState);
  }, []);

  // Initialize camera scanner when in SCAN screen and camera is active
  useEffect(() => {
    let isMounted = true;

    if (screen === 'SCAN' && cameraActive && !cameraDenied && activeTab === 'scan') {
      const startScanner = async () => {
        try {
          const html5QrCode = new Html5Qrcode('pwa-reader');
          scannerRef.current = html5QrCode;

          const config = {
            fps: 10,
            qrbox: { width: 220, height: 220 },
            aspectRatio: 1.0,
          };

          await html5QrCode.start(
            { facingMode: 'environment' },
            config,
            (decodedText) => {
              if (isMounted) {
                performLookup(decodedText);
              }
            },
            () => {}
          );
        } catch (err) {
          console.warn('Camera initiation note:', err);
          if (isMounted) {
            setCameraDenied(true);
            setCameraActive(false);
            setTimeout(() => inputRef.current?.focus(), 200);
          }
        }
      };

      const timer = setTimeout(startScanner, 100);
      return () => {
        isMounted = false;
        clearTimeout(timer);
        if (scannerRef.current) {
          try {
            if (scannerRef.current.isScanning) {
              scannerRef.current.stop().then(() => scannerRef.current.clear()).catch(() => {});
            } else {
              scannerRef.current.clear();
            }
          } catch (_) {}
          scannerRef.current = null;
        }
      };
    } else {
      if (scannerRef.current) {
        try {
          if (scannerRef.current.isScanning) {
            scannerRef.current.stop().then(() => scannerRef.current.clear()).catch(() => {});
          } else {
            scannerRef.current.clear();
          }
        } catch (_) {}
        scannerRef.current = null;
      }
    }
  }, [screen, cameraActive, cameraDenied, activeTab]);

  const stopActiveCamera = async () => {
    if (scannerRef.current && scannerRef.current.isScanning) {
      try {
        await scannerRef.current.stop();
        scannerRef.current.clear();
      } catch (_) {}
      scannerRef.current = null;
    }
  };

  const performLookup = async (queryTerm) => {
    const q = (queryTerm || searchQuery || '').trim();
    if (!q) return;

    await stopActiveCamera();
    setLoading(true);
    setLastSearchedTerm(q);

    try {
      const response = await fetch(`/api/method/tracora.api.lookup.find_asset?q=${encodeURIComponent(q)}`, {
        method: 'GET',
        headers: {
          Accept: 'application/json',
          'X-Frappe-CSRF-Token': window.frappe?.csrf_token || '',
        },
      });

      if (response.status === 401 || response.status === 403) {
        window.location.href = '/login?redirect-to=/mobile';
        return;
      }

      if (!response.ok) {
        const errJson = await response.json().catch(() => null);
        if (errJson && (errJson.exc_type === 'PermissionError' || response.status === 403)) {
          window.location.href = '/login?redirect-to=/mobile';
          return;
        }
        throw new Error(`HTTP ${response.status}`);
      }

      const resData = await response.json();
      const payload = resData.message || resData;

      if (payload.match_type === 'single') {
        setSingleResult(payload);
        setScreen('RESULT');
      } else if (payload.match_type === 'multiple') {
        setMultipleResults(payload.results || []);
        setScreen('MULTIPLE');
      } else {
        setScreen('NOT_FOUND');
      }
    } catch (err) {
      console.error('Lookup request failed:', err);
      setLastFailedQuery(q);
      setScreen('OFFLINE');
    } finally {
      setLoading(false);
    }
  };

  const resetToScan = (enableCamera = true) => {
    setScreen('SCAN');
    setSingleResult(null);
    setMultipleResults([]);
    setSearchQuery('');
    if (!cameraDenied && enableCamera && activeTab === 'scan') {
      setCameraActive(true);
    } else {
      setCameraActive(false);
      setTimeout(() => inputRef.current?.focus(), 150);
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900 flex flex-col font-sans max-w-md mx-auto shadow-xl selection:bg-slate-900 selection:text-white pb-6">
      {/* APP SHELL HEADER */}
      <header className="sticky top-0 z-30 bg-slate-900 text-white px-4 pt-3 pb-2 shadow-md flex flex-col gap-2">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            {screen !== 'SCAN' ? (
              <button
                type="button"
                onClick={() => resetToScan(activeTab === 'scan')}
                className="min-h-[44px] min-w-[44px] -ml-2 p-2 flex items-center justify-center rounded-xl hover:bg-slate-800 active:bg-slate-700 transition-colors"
                aria-label="Back to Search"
              >
                <ArrowLeft className="w-5 h-5 text-white" />
              </button>
            ) : (
              <div className="min-h-[44px] min-w-[44px] -ml-2 flex items-center justify-center">
                <ScanLine className="w-6 h-6 text-emerald-400" />
              </div>
            )}
            <div>
              <h1 className="text-base font-bold tracking-tight text-white flex items-center gap-1.5 leading-none">
                TRACORA
                <span className="text-[11px] font-mono px-1.5 py-0.5 rounded-sm bg-emerald-500/20 text-emerald-300 font-normal">
                  MOBILE
                </span>
              </h1>
              <span className="text-[10px] text-slate-400 font-mono tracking-wider uppercase">
                {activeTab === 'scan' ? 'Asset Scanner' : 'Asset Directory'}
              </span>
            </div>
          </div>

          {/* Connection Status Pill */}
          <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[11px] font-mono border border-slate-700 bg-slate-800/80">
            {isOnline ? (
              <>
                <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
                <span className="text-slate-300">Live</span>
              </>
            ) : (
              <>
                <span className="w-2 h-2 rounded-full bg-rose-500" />
                <span className="text-rose-300">Offline</span>
              </>
            )}
          </div>
        </div>

        {/* MOBILE SHELL NAVIGATION TABS */}
        <nav className="flex rounded-xl bg-slate-800/90 p-1 border border-slate-700 text-xs font-semibold">
          <button
            type="button"
            onClick={() => switchTab('scan')}
            className={`flex-1 min-h-[38px] rounded-lg flex items-center justify-center gap-1.5 transition-all ${
              activeTab === 'scan'
                ? 'bg-slate-900 text-white shadow-xs font-bold'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <Camera className="w-3.5 h-3.5" />
            <span>QR Scan</span>
          </button>
          <button
            type="button"
            onClick={() => switchTab('lookup')}
            className={`flex-1 min-h-[38px] rounded-lg flex items-center justify-center gap-1.5 transition-all ${
              activeTab === 'lookup'
                ? 'bg-slate-900 text-white shadow-xs font-bold'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <Search className="w-3.5 h-3.5" />
            <span>Tag / Serial Lookup</span>
          </button>
        </nav>
      </header>

      {/* SCREEN 1: SCAN & SEARCH VIEW */}
      {screen === 'SCAN' && (
        <main className="flex-1 p-4 flex flex-col space-y-4">
          {/* SEARCH INPUT BAR */}
          <form
            onSubmit={(e) => {
              e.preventDefault();
              performLookup(searchQuery);
            }}
            className="space-y-2"
          >
            <label htmlFor="pwa-asset-input" className="block text-xs font-semibold text-slate-700 uppercase tracking-wider">
              {activeTab === 'scan' ? 'Scan or Enter Asset Identifier' : 'Search Asset by Tag, Serial, or Name'}
            </label>
            <div className="relative flex items-center">
              <input
                id="pwa-asset-input"
                ref={inputRef}
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="e.g. TRC-000007, SN-10293, MacBook..."
                className="w-full min-h-[48px] pl-10 pr-10 rounded-xl border-2 border-slate-300 focus:border-slate-900 focus:ring-0 text-sm font-medium text-slate-900 bg-white shadow-xs outline-none transition-colors"
                autoComplete="off"
                autoCapitalize="characters"
              />
              <Search className="w-4 h-4 text-slate-400 absolute left-3 pointer-events-none" />
              {searchQuery && (
                <button
                  type="button"
                  onClick={() => setSearchQuery('')}
                  className="min-h-[44px] min-w-[44px] absolute right-0 flex items-center justify-center text-slate-400 hover:text-slate-700"
                  aria-label="Clear Search Input"
                >
                  <X className="w-4 h-4" />
                </button>
              )}
            </div>

            <button
              type="submit"
              disabled={loading || !searchQuery.trim()}
              className="w-full min-h-[48px] bg-slate-900 hover:bg-slate-800 disabled:bg-slate-300 text-white font-semibold text-sm rounded-xl transition-colors shadow-xs active:scale-[0.99] flex items-center justify-center gap-2"
            >
              {loading ? (
                <>
                  <RefreshCw className="w-4 h-4 animate-spin" />
                  <span>Looking up Asset...</span>
                </>
              ) : (
                <>
                  <Search className="w-4 h-4" />
                  <span>Find Asset</span>
                </>
              )}
            </button>
          </form>

          {/* CAMERA VIEWFINDER (Active in 'scan' tab) */}
          {activeTab === 'scan' && (
            <div className="bg-white rounded-2xl border border-slate-200 p-4 space-y-3 shadow-xs">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-slate-700 uppercase tracking-wider flex items-center gap-1.5">
                  <Camera className="w-4 h-4 text-slate-500" />
                  <span>Camera Viewfinder</span>
                </span>

                {!cameraDenied && (
                  <button
                    type="button"
                    onClick={() => {
                      setCameraActive(!cameraActive);
                      if (cameraActive) {
                        setTimeout(() => inputRef.current?.focus(), 150);
                      }
                    }}
                    className="min-h-[44px] px-3 text-xs font-semibold text-slate-600 hover:text-slate-900 transition-colors flex items-center gap-1"
                  >
                    {cameraActive ? (
                      <>
                        <CameraOff className="w-3.5 h-3.5" />
                        <span>Type instead</span>
                      </>
                    ) : (
                      <>
                        <Camera className="w-3.5 h-3.5" />
                        <span>Open camera</span>
                      </>
                    )}
                  </button>
                )}
              </div>

              {cameraDenied ? (
                <div className="p-4 rounded-xl bg-amber-50 border border-amber-200 text-amber-800 space-y-2">
                  <div className="flex items-center gap-2 font-semibold text-sm">
                    <AlertCircle className="w-4 h-4 flex-shrink-0 text-amber-600" />
                    <span>Camera Permission Denied</span>
                  </div>
                  <p className="text-xs text-amber-700 leading-relaxed">
                    Camera access was declined. Use the text input above to search by Asset Tag, Serial Number, or Asset Name.
                  </p>
                </div>
              ) : cameraActive ? (
                <div className="relative overflow-hidden rounded-xl bg-slate-950 flex flex-col items-center justify-center min-h-[260px] border border-slate-800">
                  <div id="pwa-reader" className="w-full h-full min-h-[260px]" />
                  <div className="absolute bottom-2 text-center text-[10px] text-slate-300 bg-slate-900/80 px-3 py-1 rounded-full font-mono pointer-events-none">
                    Align asset barcode/QR code within frame
                  </div>
                </div>
              ) : (
                <div className="p-6 rounded-xl bg-slate-100 border border-dashed border-slate-300 text-center space-y-3">
                  <div className="w-12 h-12 rounded-full bg-white flex items-center justify-center mx-auto text-slate-400 shadow-xs">
                    <CameraOff className="w-6 h-6" />
                  </div>
                  <div>
                    <h2 className="text-xs font-bold text-slate-700 uppercase tracking-wider">Camera Paused</h2>
                    <p className="text-xs text-slate-500 pt-0.5">
                      Type the asset tag or serial above, or re-open the camera scanner.
                    </p>
                  </div>
                  <button
                    type="button"
                    onClick={() => setCameraActive(true)}
                    className="min-h-[44px] px-4 bg-white border border-slate-300 hover:bg-slate-50 text-slate-800 text-xs font-semibold rounded-lg shadow-xs transition-colors"
                  >
                    Activate Camera
                  </button>
                </div>
              )}
            </div>
          )}

          {/* TIPS & WORKFLOW GUIDANCE */}
          <div className="bg-slate-100/70 rounded-xl p-3 border border-slate-200 text-[11px] text-slate-600 space-y-1">
            <span className="font-semibold text-slate-800">Field Scanner Workflow:</span>
            <ul className="list-disc list-inside space-y-0.5 text-slate-500 pl-1">
              <li>Exact QR tag scans immediately resolve the asset custody profile.</li>
              <li>Damaged labels can be looked up by serial number or model name.</li>
              <li>Zero data cached offline to guarantee custody freshness (HLD §8).</li>
            </ul>
          </div>
        </main>
      )}

      {/* SCREEN 2: RESULT VIEW (FR-32/33) */}
      {screen === 'RESULT' && singleResult?.asset && (
        <main className="flex-1 p-4 space-y-4">
          {/* Main Custody Card */}
          <div className="bg-white rounded-2xl border border-slate-200 p-4 space-y-3 shadow-xs">
            <div className="flex items-start justify-between gap-2 border-b border-slate-100 pb-3">
              <div>
                <span className="text-[11px] font-mono text-slate-400 uppercase tracking-wider block">Asset Tag</span>
                <span className="text-lg font-mono font-bold text-slate-900 tracking-tight">
                  {singleResult.asset.asset_tag}
                </span>
              </div>
              {getStatusBadge(singleResult.asset.status)}
            </div>

            <div>
              <span className="text-[11px] font-mono text-slate-400 uppercase tracking-wider block">Asset Name</span>
              <h1 className="text-base font-bold text-slate-900 leading-snug">
                {singleResult.asset.asset_name}
              </h1>
              <span className="text-xs text-slate-500 font-medium">
                {singleResult.asset.brand} {singleResult.asset.model_number && `• ${singleResult.asset.model_number}`}
              </span>
            </div>

            {/* Holder Profile */}
            <div className="pt-2 border-t border-slate-100 space-y-2">
              <span className="text-[11px] font-mono text-slate-400 uppercase tracking-wider block">Current Custody</span>
              {singleResult.holder ? (
                <div className="bg-slate-50 rounded-xl p-3 border border-slate-200 space-y-2">
                  <div className="flex items-center gap-2.5">
                    <div className="w-8 h-8 rounded-full bg-slate-900 text-white flex items-center justify-center font-bold text-xs flex-shrink-0">
                      {singleResult.holder.employee_name?.charAt(0) || 'U'}
                    </div>
                    <div className="min-w-0">
                      <div className="text-sm font-bold text-slate-900 truncate">
                        {singleResult.holder.employee_name}
                      </div>
                      <div className="text-xs font-mono text-slate-500">
                        {singleResult.holder.employee_code}
                      </div>
                    </div>
                  </div>

                  <div className="text-xs text-slate-600 space-y-1 pt-1 border-t border-slate-200/60 font-medium">
                    <div className="flex items-center gap-1.5">
                      <Building className="w-3.5 h-3.5 text-slate-400 flex-shrink-0" />
                      <span className="truncate">{singleResult.holder.company} ({singleResult.holder.company_type})</span>
                    </div>
                    {singleResult.holder.company_type === 'External' ? (
                      <div className="flex items-center gap-1.5 text-slate-500">
                        <User className="w-3.5 h-3.5 text-slate-400 flex-shrink-0" />
                        <span className="truncate">{singleResult.holder.designation || 'External Custodian'}</span>
                      </div>
                    ) : (
                      <div className="flex items-center gap-1.5 text-slate-500">
                        <MapPin className="w-3.5 h-3.5 text-slate-400 flex-shrink-0" />
                        <span className="truncate">
                          {[singleResult.holder.branch, singleResult.holder.department].filter(Boolean).join(' • ') || 'Internal'}
                        </span>
                      </div>
                    )}
                  </div>
                </div>
              ) : (
                <div className="bg-slate-50 rounded-xl p-3 border border-slate-200 text-xs text-slate-600 flex items-center gap-2">
                  <CheckCircle2 className="w-4 h-4 text-blue-600 flex-shrink-0" />
                  <span>Unassigned — Stored at <strong>{singleResult.asset.location || 'Central Store'}</strong></span>
                </div>
              )}
            </div>
          </div>

          {/* Asset Specifications & Details */}
          <div className="bg-white rounded-2xl border border-slate-200 p-4 space-y-3 shadow-xs">
            <h2 className="text-sm font-bold uppercase tracking-wider text-slate-700 flex items-center gap-1.5 border-b border-slate-100 pb-2">
              <SlidersHorizontal className="w-4 h-4 text-slate-500" />
              <span>Asset Specifications</span>
            </h2>

            <dl className="grid grid-cols-2 gap-3 text-xs">
              <div>
                <dt className="text-slate-400 font-mono text-[10px] uppercase">Serial Number</dt>
                <dd className="font-mono font-semibold text-slate-900 truncate">
                  {singleResult.asset.serial_no || '—'}
                </dd>
              </div>
              <div>
                <dt className="text-slate-400 font-mono text-[10px] uppercase">Condition</dt>
                <dd className="font-semibold text-slate-900">{singleResult.asset.condition || 'Good'}</dd>
              </div>
              <div>
                <dt className="text-slate-400 font-mono text-[10px] uppercase">Owner Company</dt>
                <dd className="font-semibold text-slate-900 truncate">{singleResult.asset.owner_company || '—'}</dd>
              </div>
              <div>
                <dt className="text-slate-400 font-mono text-[10px] uppercase">Holding Company</dt>
                <dd className="font-semibold text-slate-900 truncate">{singleResult.asset.holding_company || '—'}</dd>
              </div>
              <div>
                <dt className="text-slate-400 font-mono text-[10px] uppercase">Branch</dt>
                <dd className="font-semibold text-slate-900 truncate">{singleResult.asset.branch || '—'}</dd>
              </div>
              <div>
                <dt className="text-slate-400 font-mono text-[10px] uppercase">Location</dt>
                <dd className="font-semibold text-slate-900 truncate">{singleResult.asset.location || '—'}</dd>
              </div>
            </dl>
          </div>

          {/* Open Maintenance (if any) */}
          {singleResult.open_maintenance && (
            <div className="bg-amber-50 rounded-2xl border border-amber-200 p-4 space-y-2 shadow-xs text-amber-900">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold uppercase tracking-wider flex items-center gap-1.5 text-amber-800">
                  <Wrench className="w-4 h-4 text-amber-600" />
                  <span>Open Maintenance</span>
                </span>
                <span className="font-mono text-xs font-semibold">{singleResult.open_maintenance.name}</span>
              </div>
              <div className="text-xs space-y-1">
                <div>Vendor: <strong>{singleResult.open_maintenance.vendor}</strong></div>
                <div>Reason: <em>{singleResult.open_maintenance.reason}</em></div>
                <div className="text-amber-700">Due: {singleResult.open_maintenance.due_date || 'TBD'}</div>
              </div>
            </div>
          )}

          {/* Active Licence Seats (if any) */}
          {singleResult.licence_seats && singleResult.licence_seats.length > 0 && (
            <div className="bg-white rounded-2xl border border-slate-200 p-4 space-y-3 shadow-xs">
              <h2 className="text-sm font-bold uppercase tracking-wider text-slate-700 flex items-center gap-1.5 border-b border-slate-100 pb-2">
                <Layers className="w-4 h-4 text-slate-500" />
                <span>Installed Licences ({singleResult.licence_seats.length})</span>
              </h2>
              <div className="space-y-2 pt-1">
                {singleResult.licence_seats.map((seat) => (
                  <div key={seat.name} className="text-xs p-2.5 rounded-lg bg-slate-50 border border-slate-200">
                    <div className="font-bold text-slate-900">{seat.software_name}</div>
                    <div className="text-slate-500 text-[11px]">{seat.licence_name} • {seat.licence_type}</div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Movement Timeline (Last 20) */}
          <div className="bg-white rounded-2xl border border-slate-200 p-4 space-y-3 shadow-xs">
            <h2 className="text-sm font-bold uppercase tracking-wider text-slate-700 flex items-center gap-1.5 border-b border-slate-100 pb-2">
              <Clock className="w-4 h-4 text-slate-500" />
              <span>Custody Timeline (Recent {singleResult.recent_movements?.length || 0})</span>
            </h2>

            {singleResult.recent_movements && singleResult.recent_movements.length > 0 ? (
              <div className="space-y-3 pt-1">
                {singleResult.recent_movements.map((mov, idx) => (
                  <div key={mov.name || idx} className="flex gap-3 text-xs">
                    <div className="w-2.5 h-2.5 rounded-full bg-slate-400 mt-1 flex-shrink-0" />
                    <div className="flex-1 space-y-0.5">
                      <div className="flex items-center justify-between">
                        <span className="font-semibold text-slate-900">{mov.movement_type}</span>
                        <span className="text-slate-400 font-mono text-[11px]">{mov.movement_date}</span>
                      </div>
                      <div className="text-slate-600">
                        {mov.to_employee && <span>To: <strong>{mov.to_employee}</strong> </span>}
                        {mov.to_location && <span>at {mov.to_location}</span>}
                      </div>
                      {mov.remarks && (
                        <div className="text-slate-500 italic text-[11px]">"{mov.remarks}"</div>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-xs text-slate-500 italic py-2">No previous recorded movements.</div>
            )}
          </div>

          {/* Bottom Sticky Action */}
          <button
            type="button"
            onClick={() => resetToScan(activeTab === 'scan')}
            className="w-full min-h-[48px] bg-slate-900 hover:bg-slate-800 text-white font-semibold text-sm rounded-xl transition-colors shadow-sm flex items-center justify-center gap-2 active:scale-[0.99]"
          >
            <Camera className="w-4 h-4" />
            <span>Scan Another Asset</span>
          </button>
        </main>
      )}

      {/* SCREEN 3: MULTIPLE MATCHES (FR-91) */}
      {screen === 'MULTIPLE' && (
        <main className="flex-1 p-4 space-y-4">
          <div className="bg-white rounded-2xl border border-slate-200 p-4 shadow-xs space-y-1">
            <h1 className="text-base font-bold text-slate-900">
              Results for "{lastSearchedTerm}"
            </h1>
            <p className="text-xs text-slate-500">
              {multipleResults.length} matching assets found. Select an asset to view details (FR-91):
            </p>
          </div>

          <div className="space-y-2.5">
            {multipleResults.map((item) => (
              <div
                key={item.name}
                onClick={() => performLookup(item.asset_tag || item.name)}
                className="min-h-[56px] p-3.5 bg-white hover:bg-slate-50 active:bg-slate-100 rounded-xl border border-slate-200 cursor-pointer transition-colors shadow-xs flex flex-col justify-between space-y-2"
                role="button"
                tabIndex={0}
              >
                <div className="flex items-center justify-between">
                  <span className="font-mono font-bold text-sm text-slate-900">
                    {item.asset_tag || item.name}
                  </span>
                  {getStatusBadge(item.status)}
                </div>

                <div>
                  <div className="font-semibold text-sm text-slate-900">{item.asset_name}</div>
                  <div className="text-xs text-slate-500 font-medium">
                    {item.brand} {item.model_number && `• ${item.model_number}`}
                  </div>
                </div>

                <div className="flex items-center justify-between text-xs text-slate-600 pt-1 border-t border-slate-100">
                  <div className="flex items-center gap-1 truncate max-w-[55%]">
                    <User className="w-3.5 h-3.5 text-slate-400 flex-shrink-0" />
                    <span className="truncate">{item.holder_name || item.assigned_to || 'Unassigned'}</span>
                  </div>
                  <div className="flex items-center gap-1 text-slate-500">
                    <MapPin className="w-3.5 h-3.5 text-slate-400 flex-shrink-0" />
                    <span>{item.location || '—'}</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </main>
      )}

      {/* SCREEN 4: NOT FOUND (FR-34) */}
      {screen === 'NOT_FOUND' && (
        <main className="flex-1 p-6 flex flex-col items-center justify-center text-center space-y-5">
          <div className="w-16 h-16 rounded-3xl bg-slate-100 border border-slate-200 flex items-center justify-center text-slate-400 shadow-inner">
            <SearchX className="w-8 h-8" />
          </div>

          <div className="space-y-2 max-w-xs">
            <h1 className="text-xl font-bold text-slate-900">No Asset Found</h1>
            <p className="text-sm text-slate-600">
              No asset found matching <span className="font-mono font-semibold text-slate-900">"{lastSearchedTerm}"</span>.
            </p>
            <p className="text-xs text-slate-500 leading-relaxed pt-1">
              Check the tag, serial number, or spelling and search again. Unknown assets must be registered at an Admin desk.
            </p>
          </div>

          <button
            type="button"
            onClick={() => resetToScan(activeTab === 'scan')}
            className="min-h-[44px] px-6 bg-slate-900 hover:bg-slate-800 text-white font-semibold text-sm rounded-xl transition-colors shadow-xs active:scale-[0.99]"
          >
            Search Again
          </button>
        </main>
      )}

      {/* SCREEN 5: OFFLINE (Honest and Immediate) */}
      {screen === 'OFFLINE' && (
        <main className="flex-1 p-6 flex flex-col items-center justify-center text-center space-y-5">
          <div className="w-16 h-16 rounded-3xl bg-rose-50 border border-rose-200 flex items-center justify-center text-rose-500 shadow-inner">
            <WifiOff className="w-8 h-8" />
          </div>

          <div className="space-y-2 max-w-xs">
            <h1 className="text-xl font-bold text-slate-900">No Connection</h1>
            <p className="text-sm text-slate-600">
              Unable to reach the Tracora server.
            </p>
            <p className="text-xs text-slate-500 leading-relaxed pt-1">
              Asset data is not cached offline to prevent displaying outdated custody records (HLD §8). Please verify network connectivity.
            </p>
          </div>

          <div className="flex flex-col gap-2 w-full max-w-xs">
            {lastFailedQuery && (
              <button
                type="button"
                onClick={() => performLookup(lastFailedQuery)}
                className="w-full min-h-[44px] bg-slate-900 hover:bg-slate-800 text-white font-semibold text-sm rounded-xl transition-colors shadow-xs active:scale-[0.99] flex items-center justify-center gap-2"
              >
                <RefreshCw className="w-4 h-4" />
                <span>Retry Connection</span>
              </button>
            )}
            <button
              type="button"
              onClick={() => resetToScan(false)}
              className="w-full min-h-[44px] bg-slate-100 hover:bg-slate-200 text-slate-800 font-semibold text-sm rounded-xl transition-colors active:scale-[0.99]"
            >
              Back to Search
            </button>
          </div>
        </main>
      )}
    </div>
  );
}
