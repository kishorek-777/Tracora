import React, { useState, useEffect, useRef } from 'react';
import {
  Camera,
  CameraOff,
  Search,
  X,
  ArrowLeft,
  WifiOff,
  AlertCircle,
  Clock,
  Layers,
  Wrench,
  User,
  RefreshCw,
  SearchX,
  ScanLine,
  LogOut,
  Lock,
  Eye,
  EyeOff,
  ShieldCheck,
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

// Invalidate Workbox cached mobile document shell on auth boundary transitions
const invalidateShellCache = async () => {
  if (typeof window !== 'undefined' && 'caches' in window) {
    try {
      const cache = await caches.open('tracora-mobile-shell');
      await Promise.all([
        cache.delete('/mobile'),
        cache.delete('/mobile/'),
      ]);
    } catch (err) {
      console.warn('Cache invalidation note:', err);
    }
  }
};

export default function MobileApp() {
  // Session & Authentication State
  const [currentUser, setCurrentUser] = useState(() => {
    if (typeof window !== 'undefined') {
      if (window.__TRACORA_USER__ && window.__TRACORA_USER__ !== 'Guest') {
        return window.__TRACORA_USER__;
      }
      if (window.frappe?.session?.user && window.frappe.session.user !== 'Guest') {
        return window.frappe.session.user;
      }
    }
    return null;
  });

  const [csrfToken, setCsrfToken] = useState(() => {
    if (typeof window !== 'undefined') {
      return window.__CSRF_TOKEN__ || window.csrf_token || window.frappe?.csrf_token || '';
    }
    return '';
  });

  // Login Form State
  const [loginUsername, setLoginUsername] = useState('');
  const [loginPassword, setLoginPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [loginLoading, setLoginLoading] = useState(false);
  const [loginError, setLoginError] = useState('');
  const [logoutLoading, setLogoutLoading] = useState(false);

  // Shell tab state: 'scan' | 'lookup'
  const [activeTab, setActiveTab] = useState(() => {
    const path = typeof window !== 'undefined' ? window.location.pathname : '';
    return path.includes('/lookup') ? 'lookup' : 'scan';
  });

  // Screen state machine: 'LOGIN' | 'SCAN' | 'RESULT' | 'MULTIPLE' | 'NOT_FOUND' | 'OFFLINE'
  const [screen, setScreen] = useState(() => {
    if (typeof window !== 'undefined') {
      const u = window.__TRACORA_USER__ || window.frappe?.session?.user;
      if (!u || u === 'Guest') {
        return 'LOGIN';
      }
    }
    return 'SCAN';
  });

  const [searchQuery, setSearchQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [isOnline, setIsOnline] = useState(typeof navigator !== 'undefined' ? navigator.onLine : true);

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
      if (screen !== 'SCAN' && screen !== 'LOGIN') {
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
      if (currentUser) {
        resetToScan(false);
      }
    };
    window.addEventListener('popstate', handlePopState);
    return () => window.removeEventListener('popstate', handlePopState);
  }, [currentUser]);

  // Initialize camera scanner when in SCAN screen and camera is active
  useEffect(() => {
    let isMounted = true;

    if (currentUser && screen === 'SCAN' && cameraActive && !cameraDenied && activeTab === 'scan') {
      const startScanner = async () => {
        try {
          const { Html5Qrcode } = await import('html5-qrcode');
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
          } catch {}
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
        } catch {}
        scannerRef.current = null;
      }
    }
  }, [currentUser, screen, cameraActive, cameraDenied, activeTab]);

  const stopActiveCamera = async () => {
    if (scannerRef.current && scannerRef.current.isScanning) {
      try {
        await scannerRef.current.stop();
        scannerRef.current.clear();
      } catch {}
      scannerRef.current = null;
    }
  };

  // Auth: Submit login
  const handleLogin = async (e) => {
    if (e) e.preventDefault();
    setLoginError('');

    const usr = loginUsername.trim();
    const pwd = loginPassword;
    if (!usr || !pwd) {
      setLoginError('Please enter both email/username and password.');
      return;
    }

    if (!isOnline) {
      setLoginError('Cannot sign in while offline. Please connect to a network.');
      return;
    }

    setLoginLoading(true);
    try {
      const body = new URLSearchParams({ usr, pwd });
      const response = await fetch('/api/method/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
          Accept: 'application/json',
          'X-Frappe-CSRF-Token': csrfToken,
        },
        body: body.toString(),
      });

      const data = await response.json().catch(() => null);

      if (!response.ok || (data && data.exc)) {
        const msg = data?.message || 'Invalid username or password.';
        setLoginError(msg);
        setLoginLoading(false);
        return;
      }

      // Purge cached guest shell in Workbox immediately upon login
      await invalidateShellCache();

      // Retrieve new authenticated session info and updated CSRF token
      let authedUser = usr;
      let newCsrf = '';
      try {
        const sessionRes = await fetch('/api/method/tracora.api.lookup.get_session_info', {
          method: 'GET',
          headers: { Accept: 'application/json' },
        });
        if (sessionRes.ok) {
          const sessionData = await sessionRes.json();
          const info = sessionData.message || {};
          if (info.user && info.user !== 'Guest') {
            authedUser = info.user;
          }
          if (info.csrf_token) {
            newCsrf = info.csrf_token;
          }
        }
      } catch (sessErr) {
        console.warn('Session info fetch note:', sessErr);
      }

      setCurrentUser(authedUser);
      if (newCsrf) {
        setCsrfToken(newCsrf);
      }
      if (typeof window !== 'undefined') {
        window.__TRACORA_USER__ = authedUser;
        if (newCsrf) {
          window.__CSRF_TOKEN__ = newCsrf;
          window.csrf_token = newCsrf;
          if (window.frappe) window.frappe.csrf_token = newCsrf;
        }
      }

      setLoginPassword('');
      setScreen('SCAN');
      resetToScan(activeTab === 'scan');
    } catch {
      setLoginError('Network or server error during sign in. Please retry.');
    } finally {
      setLoginLoading(false);
    }
  };

  // Auth: Submit logout
  const handleLogout = async () => {
    if (logoutLoading) return;
    setLogoutLoading(true);

    try {
      await stopActiveCamera();
      await invalidateShellCache();

      await fetch('/api/method/logout', {
        method: 'POST',
        headers: {
          Accept: 'application/json',
          'X-Frappe-CSRF-Token': csrfToken,
        },
      }).catch(() => {});
    } finally {
      setCurrentUser(null);
      if (typeof window !== 'undefined') {
        window.__TRACORA_USER__ = 'Guest';
      }
      setSingleResult(null);
      setMultipleResults([]);
      setSearchQuery('');
      setLogoutLoading(false);
      setScreen('LOGIN');
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
          'X-Frappe-CSRF-Token': csrfToken || '',
        },
      });

      if (response.status === 401 || response.status === 403) {
        setCurrentUser(null);
        if (typeof window !== 'undefined') {
          window.__TRACORA_USER__ = 'Guest';
        }
        setLoginError('Your session has expired. Please sign in again.');
        setScreen('LOGIN');
        return;
      }

      if (!response.ok) {
        const errJson = await response.json().catch(() => null);
        if (errJson && (errJson.exc_type === 'PermissionError' || response.status === 403)) {
          setCurrentUser(null);
          if (typeof window !== 'undefined') {
            window.__TRACORA_USER__ = 'Guest';
          }
          setLoginError('Your session has expired. Please sign in again.');
          setScreen('LOGIN');
          return;
        }
        throw new Error(`HTTP ${response.status}`);
      }

      const res = await response.json();
      const payload = res.message;

      if (!payload || payload.match_type === 'none') {
        setScreen('NOT_FOUND');
      } else if (payload.match_type === 'single') {
        setSingleResult(payload);
        setScreen('RESULT');
      } else if (payload.match_type === 'multiple') {
        setMultipleResults(payload.results || []);
        setScreen('MULTIPLE');
      }
    } catch (err) {
      console.warn('Asset lookup network note:', err);
      setLastFailedQuery(q);
      setScreen('OFFLINE');
    } finally {
      setLoading(false);
    }
  };

  const handleManualSearch = (e) => {
    e.preventDefault();
    if (searchQuery.trim()) {
      performLookup(searchQuery.trim());
    }
  };

  const selectMultipleItem = (assetTag) => {
    performLookup(assetTag);
  };

  const resetToScan = (startCamera = true) => {
    setSingleResult(null);
    setMultipleResults([]);
    setSearchQuery('');
    setScreen('SCAN');
    if (activeTab === 'scan' && startCamera) {
      setCameraActive(true);
    }
  };

  // =========================================================================
  // VIEW: BRANDED LOGIN VIEW (Option A: Scoped inside Tracora /mobile)
  // =========================================================================
  if (!currentUser || screen === 'LOGIN') {
    return (
      <div className="min-h-screen bg-slate-900 text-slate-100 flex flex-col justify-between p-4 sm:p-6 font-sans">
        {/* Top brand header */}
        <header className="pt-4 flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="w-9 h-9 rounded-xl bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-center text-emerald-400">
              <ScanLine className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-1.5">
                <span className="font-bold tracking-tight text-base text-white">TRACORA</span>
                <span className="text-[10px] font-semibold uppercase tracking-wider px-1.5 py-0.5 rounded bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">Mobile</span>
              </div>
              <p className="text-[10px] text-slate-400 tracking-wider font-medium">ASSET SCANNER & CUSTODY</p>
            </div>
          </div>

          {/* Connectivity Badge */}
          <div className={`flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium border ${
            isOnline
              ? 'bg-emerald-500/10 text-emerald-300 border-emerald-500/20'
              : 'bg-rose-500/10 text-rose-300 border-rose-500/20'
          }`}>
            <span className={`w-1.5 h-1.5 rounded-full ${isOnline ? 'bg-emerald-400 animate-pulse' : 'bg-rose-400'}`} />
            <span>{isOnline ? 'Live' : 'Offline'}</span>
          </div>
        </header>

        {/* Center Login Card */}
        <main className="my-auto py-8 flex flex-col items-center">
          <div className="w-full max-w-sm bg-slate-800/80 border border-slate-700/80 rounded-2xl p-6 sm:p-8 shadow-2xl backdrop-blur-sm space-y-6">
            <div className="text-center space-y-2">
              <div className="w-12 h-12 rounded-2xl bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center text-emerald-400 mx-auto shadow-inner">
                <Lock className="w-6 h-6" />
              </div>
              <h1 className="text-xl font-bold tracking-tight text-white">Sign In to Tracora</h1>
              <p className="text-xs text-slate-400 leading-relaxed">
                Enter your credentials to access asset barcode scanning and custody verification.
              </p>
            </div>

            {/* Offline notification if disconnected */}
            {!isOnline && (
              <div className="p-3 rounded-xl bg-amber-500/10 border border-amber-500/30 text-amber-300 text-xs flex items-center gap-2">
                <WifiOff className="w-4 h-4 shrink-0 text-amber-400" />
                <span>You are currently offline. Connect to network to sign in.</span>
              </div>
            )}

            {/* Error Banner */}
            {loginError && (
              <div className="p-3 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-300 text-xs flex items-start gap-2.5 animate-fadeIn">
                <AlertCircle className="w-4 h-4 shrink-0 text-rose-400 mt-0.5" />
                <span className="leading-relaxed">{loginError}</span>
              </div>
            )}

            <form onSubmit={handleLogin} className="space-y-4">
              {/* Username Input */}
              <div className="space-y-1.5">
                <label className="block text-xs font-semibold text-slate-300">
                  Email or Username
                </label>
                <div className="relative">
                  <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-500">
                    <User className="w-4 h-4" />
                  </div>
                  <input
                    type="text"
                    required
                    autoComplete="username"
                    value={loginUsername}
                    onChange={(e) => setLoginUsername(e.target.value)}
                    placeholder="e.g. kishore.k@aionioncapital.com"
                    disabled={loginLoading}
                    className="w-full pl-9 pr-3 py-2.5 bg-slate-900/90 border border-slate-700 rounded-xl text-sm text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 transition-colors disabled:opacity-50"
                  />
                </div>
              </div>

              {/* Password Input */}
              <div className="space-y-1.5">
                <label className="block text-xs font-semibold text-slate-300">
                  Password
                </label>
                <div className="relative">
                  <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-500">
                    <Lock className="w-4 h-4" />
                  </div>
                  <input
                    type={showPassword ? 'text' : 'password'}
                    required
                    autoComplete="current-password"
                    value={loginPassword}
                    onChange={(e) => setLoginPassword(e.target.value)}
                    placeholder="Enter your password"
                    disabled={loginLoading}
                    className="w-full pl-9 pr-10 py-2.5 bg-slate-900/90 border border-slate-700 rounded-xl text-sm text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 transition-colors disabled:opacity-50"
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    tabIndex={-1}
                    className="absolute inset-y-0 right-0 pr-3 flex items-center text-slate-500 hover:text-slate-300 transition-colors"
                  >
                    {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                  </button>
                </div>
              </div>

              {/* Submit Button */}
              <button
                type="submit"
                disabled={loginLoading || !isOnline}
                className="w-full min-h-[44px] mt-2 bg-emerald-600 hover:bg-emerald-500 active:bg-emerald-700 text-white font-semibold text-sm rounded-xl transition-all shadow-md flex items-center justify-center gap-2 active:scale-[0.99] disabled:opacity-50 cursor-pointer"
              >
                {loginLoading ? (
                  <>
                    <RefreshCw className="w-4 h-4 animate-spin" />
                    <span>Signing in...</span>
                  </>
                ) : (
                  <>
                    <ShieldCheck className="w-4 h-4" />
                    <span>Sign In</span>
                  </>
                )}
              </button>
            </form>
          </div>
        </main>

        {/* Security Footnote */}
        <footer className="text-center pb-2 text-[11px] text-slate-500">
          Secured by Frappe Session Authentication &bull; Aionion Capital Tracora
        </footer>
      </div>
    );
  }

  // =========================================================================
  // VIEW: MAIN AUTHENTICATED SCANNER SHELL
  // =========================================================================
  return (
    <div className="min-h-screen bg-slate-50 flex flex-col font-sans">
      {/* Top App Header with User & Logout controls */}
      <header className="sticky top-0 z-30 bg-slate-900 border-b border-slate-800 text-white shadow-md">
        <div className="px-4 py-3 flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-center text-emerald-400">
              <ScanLine className="w-4 h-4" />
            </div>
            <div>
              <div className="flex items-center gap-1.5">
                <span className="font-bold tracking-tight text-sm text-white">TRACORA</span>
                <span className="text-[10px] font-semibold uppercase tracking-wider px-1.5 py-0.5 rounded bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">Mobile</span>
              </div>
              <p className="text-[10px] text-slate-400 tracking-wide font-medium">ASSET SCANNER</p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            {/* Online/Offline status badge */}
            <div className={`flex items-center gap-1 px-2 py-0.5 rounded-full text-[11px] font-medium border ${
              isOnline
                ? 'bg-emerald-500/10 text-emerald-300 border-emerald-500/20'
                : 'bg-rose-500/10 text-rose-300 border-rose-500/20'
            }`}>
              <span className={`w-1.5 h-1.5 rounded-full ${isOnline ? 'bg-emerald-400 animate-pulse' : 'bg-rose-400'}`} />
              <span>{isOnline ? 'Live' : 'Offline'}</span>
            </div>

            {/* Authenticated user badge and logout action */}
            <div className="flex items-center gap-1.5 pl-1.5 border-l border-slate-700/80">
              <div className="hidden sm:flex items-center gap-1 text-[11px] text-slate-300 max-w-[130px] truncate" title={currentUser}>
                <User className="w-3 h-3 text-slate-400 shrink-0" />
                <span className="truncate">{currentUser.split('@')[0]}</span>
              </div>
              <button
                type="button"
                onClick={handleLogout}
                disabled={logoutLoading}
                title={`Sign out (${currentUser})`}
                aria-label="Sign out"
                className="p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 active:bg-slate-900 text-slate-300 hover:text-white transition-colors border border-slate-700 active:scale-95 disabled:opacity-50 cursor-pointer"
              >
                {logoutLoading ? (
                  <RefreshCw className="w-3.5 h-3.5 animate-spin text-slate-400" />
                ) : (
                  <LogOut className="w-3.5 h-3.5" />
                )}
              </button>
            </div>
          </div>
        </div>

        {/* Tab Switcher: QR Scan vs Tag/Serial Lookup */}
        <div className="px-4 pb-2.5 pt-1 grid grid-cols-2 gap-2 max-w-md mx-auto">
          <button
            type="button"
            onClick={() => switchTab('scan')}
            className={`min-h-[38px] flex items-center justify-center gap-1.5 rounded-lg text-xs font-semibold transition-all cursor-pointer ${
              activeTab === 'scan'
                ? 'bg-slate-800 text-emerald-400 border border-emerald-500/30 shadow-xs'
                : 'bg-slate-900/60 text-slate-400 hover:text-slate-200 border border-transparent'
            }`}
          >
            <Camera className="w-3.5 h-3.5" />
            <span>QR Scan</span>
          </button>
          <button
            type="button"
            onClick={() => switchTab('lookup')}
            className={`min-h-[38px] flex items-center justify-center gap-1.5 rounded-lg text-xs font-semibold transition-all cursor-pointer ${
              activeTab === 'lookup'
                ? 'bg-slate-800 text-emerald-400 border border-emerald-500/30 shadow-xs'
                : 'bg-slate-900/60 text-slate-400 hover:text-slate-200 border border-transparent'
            }`}
          >
            <Search className="w-3.5 h-3.5" />
            <span>Tag / Serial Lookup</span>
          </button>
        </div>
      </header>

      {/* SCREEN 1: SCAN & SEARCH FORM */}
      {screen === 'SCAN' && (
        <main className="flex-1 p-4 space-y-4 max-w-lg mx-auto w-full">
          {/* Universal Search Bar */}
          <form onSubmit={handleManualSearch} className="space-y-2">
            <label htmlFor="search-input" className="block text-[11px] font-bold text-slate-500 uppercase tracking-wider">
              Scan or Enter Asset Identifier
            </label>
            <div className="relative">
              <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-400">
                <Search className="w-4 h-4" />
              </div>
              <input
                id="search-input"
                ref={inputRef}
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="e.g. TRC-000007, SN-10293, MacBook..."
                className="w-full pl-9 pr-8 py-2.5 bg-white border border-slate-300 rounded-xl text-sm font-medium text-slate-900 placeholder-slate-400 shadow-xs focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500"
              />
              {searchQuery && (
                <button
                  type="button"
                  onClick={() => setSearchQuery('')}
                  className="absolute inset-y-0 right-0 pr-2.5 flex items-center text-slate-400 hover:text-slate-600"
                >
                  <X className="w-4 h-4" />
                </button>
              )}
            </div>
            <button
              type="submit"
              disabled={loading || !searchQuery.trim()}
              className="w-full min-h-[44px] bg-slate-900 hover:bg-slate-800 text-white font-semibold text-sm rounded-xl transition-all shadow-xs flex items-center justify-center gap-2 active:scale-[0.99] disabled:opacity-40"
            >
              {loading ? (
                <>
                  <RefreshCw className="w-4 h-4 animate-spin text-emerald-400" />
                  <span>Searching...</span>
                </>
              ) : (
                <>
                  <Search className="w-4 h-4" />
                  <span>Find Asset</span>
                </>
              )}
            </button>
          </form>

          {/* Camera Viewfinder Box (Shown only in scan tab) */}
          {activeTab === 'scan' && (
            <div className="bg-white rounded-2xl border border-slate-200 shadow-xs p-4 space-y-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2 text-xs font-bold text-slate-700 uppercase tracking-wider">
                  <Camera className="w-4 h-4 text-emerald-600" />
                  <span>Camera Viewfinder</span>
                </div>
                {cameraDenied && (
                  <span className="text-xs font-semibold text-rose-600 flex items-center gap-1">
                    <CameraOff className="w-3.5 h-3.5" />
                    Permission Denied
                  </span>
                )}
              </div>

              {cameraDenied ? (
                <div className="p-4 bg-amber-50 border border-amber-200 rounded-xl text-xs text-amber-800 space-y-1">
                  <p className="font-semibold flex items-center gap-1.5">
                    <AlertCircle className="w-4 h-4 text-amber-600 shrink-0" />
                    Camera Permission Denied
                  </p>
                  <p className="text-amber-700 leading-relaxed">
                    Camera access was declined. Use the text input above to search by Asset Tag, Serial Number, or Asset Name.
                  </p>
                </div>
              ) : (
                <div className="relative overflow-hidden rounded-xl bg-slate-950 aspect-square max-w-[280px] mx-auto border border-slate-800 flex items-center justify-center">
                  <div id="pwa-reader" className="w-full h-full" />
                  {/* Subtle Target Reticle Overlay */}
                  <div className="absolute inset-0 pointer-events-none flex items-center justify-center">
                    <div className="w-48 h-48 border-2 border-emerald-400/80 rounded-2xl relative shadow-[0_0_15px_rgba(52,211,153,0.3)]">
                      <div className="absolute -top-1 -left-1 w-4 h-4 border-t-4 border-l-4 border-emerald-400 rounded-tl-lg" />
                      <div className="absolute -top-1 -right-1 w-4 h-4 border-t-4 border-r-4 border-emerald-400 rounded-tr-lg" />
                      <div className="absolute -bottom-1 -left-1 w-4 h-4 border-b-4 border-l-4 border-emerald-400 rounded-bl-lg" />
                      <div className="absolute -bottom-1 -right-1 w-4 h-4 border-b-4 border-r-4 border-emerald-400 rounded-br-lg" />
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Guidelines info card */}
          <div className="bg-slate-100/80 rounded-xl p-3 border border-slate-200 text-xs text-slate-600 space-y-1">
            <p className="font-semibold text-slate-800">Field Scanner Workflow:</p>
            <ul className="list-disc pl-4 space-y-0.5 text-[11px] text-slate-600">
              <li>Exact QR tag scans immediately resolve the asset custody profile.</li>
              <li>Damaged labels can be looked up by serial number or model name.</li>
              <li>Zero data cached offline to guarantee custody freshness (HLD §8).</li>
            </ul>
          </div>
        </main>
      )}

      {/* SCREEN 2: SINGLE ASSET CUSTODY RECORD */}
      {screen === 'RESULT' && singleResult && (
        <main className="flex-1 p-4 space-y-4 max-w-lg mx-auto w-full pb-8">
          {/* Top navigation row */}
          <div className="flex items-center justify-between">
            <button
              type="button"
              onClick={() => resetToScan(activeTab === 'scan')}
              className="inline-flex items-center gap-1.5 text-xs font-semibold text-slate-600 hover:text-slate-900 bg-white border border-slate-300 rounded-lg px-3 py-1.5 shadow-xs"
            >
              <ArrowLeft className="w-3.5 h-3.5" />
              <span>Back to Scanner</span>
            </button>

            {getStatusBadge(singleResult.asset.status)}
          </div>

          {/* Primary Asset Card */}
          <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-4 space-y-3">
            <div>
              <span className="text-[10px] font-bold text-emerald-700 tracking-wider uppercase font-mono">
                {singleResult.asset.asset_tag}
              </span>
              <h1 className="text-lg font-bold text-slate-900 leading-snug">
                {singleResult.asset.asset_name}
              </h1>
              <p className="text-xs text-slate-500">
                {singleResult.asset.brand} &bull; {singleResult.asset.model_number || 'N/A'}
              </p>
            </div>

            <div className="pt-2 border-t border-slate-100 grid grid-cols-2 gap-2 text-xs">
              <div>
                <span className="text-[10px] text-slate-400 block uppercase">Serial No</span>
                <span className="font-mono font-medium text-slate-800">{singleResult.asset.serial_no || 'None'}</span>
              </div>
              <div>
                <span className="text-[10px] text-slate-400 block uppercase">Condition</span>
                <span className="font-medium text-slate-800">{singleResult.asset.condition || 'N/A'}</span>
              </div>
              <div>
                <span className="text-[10px] text-slate-400 block uppercase">Holding Company</span>
                <span className="font-medium text-slate-800 truncate block">{singleResult.asset.holding_company || 'N/A'}</span>
              </div>
              <div>
                <span className="text-[10px] text-slate-400 block uppercase">Location</span>
                <span className="font-medium text-slate-800 truncate block">{singleResult.asset.location || 'N/A'}</span>
              </div>
            </div>
          </div>

          {/* Current Custody Card */}
          <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-4 space-y-2.5">
            <div className="flex items-center gap-2 text-xs font-bold text-slate-700 uppercase tracking-wider">
              <User className="w-4 h-4 text-emerald-600" />
              <span>Current Custody Profile</span>
            </div>

            {singleResult.holder ? (
              <div className="space-y-2 text-xs">
                <div className="flex items-center justify-between">
                  <span className="font-bold text-slate-900 text-sm">{singleResult.holder.employee_name}</span>
                  <span className={`text-[10px] px-2 py-0.5 rounded font-semibold ${
                    singleResult.holder.company_type === 'External'
                      ? 'bg-amber-100 text-amber-800 border border-amber-300'
                      : 'bg-blue-100 text-blue-800 border border-blue-300'
                  }`}>
                    {singleResult.holder.company_type}
                  </span>
                </div>

                <div className="grid grid-cols-2 gap-2 pt-1 border-t border-slate-100 text-slate-600">
                  <div>
                    <span className="text-[10px] text-slate-400 block uppercase">Employee Code</span>
                    <span className="font-mono font-medium text-slate-800">{singleResult.holder.employee_code}</span>
                  </div>
                  <div>
                    <span className="text-[10px] text-slate-400 block uppercase">Company</span>
                    <span className="font-medium text-slate-800 truncate block">{singleResult.holder.company}</span>
                  </div>
                  {singleResult.holder.department && (
                    <div>
                      <span className="text-[10px] text-slate-400 block uppercase">Department</span>
                      <span className="font-medium text-slate-800 truncate block">{singleResult.holder.department}</span>
                    </div>
                  )}
                  {singleResult.holder.designation && (
                    <div>
                      <span className="text-[10px] text-slate-400 block uppercase">Designation</span>
                      <span className="font-medium text-slate-800 truncate block">{singleResult.holder.designation}</span>
                    </div>
                  )}
                </div>
              </div>
            ) : (
              <div className="p-3 bg-slate-50 border border-slate-200 rounded-xl text-xs text-slate-600">
                <span className="font-semibold text-slate-800">Unassigned / In Store</span>
                <p className="text-[11px] text-slate-500 pt-0.5">
                  This asset is currently in inventory storage and not in active personal custody.
                </p>
              </div>
            )}
          </div>

          {/* Open Maintenance Card (If active) */}
          {singleResult.open_maintenance && (
            <div className="bg-amber-50/80 rounded-2xl border border-amber-200 p-4 space-y-2">
              <div className="flex items-center justify-between text-xs font-bold text-amber-800 uppercase tracking-wider">
                <div className="flex items-center gap-1.5">
                  <Wrench className="w-4 h-4 text-amber-700" />
                  <span>Open Maintenance Log</span>
                </div>
                <span className="px-2 py-0.5 rounded text-[10px] bg-amber-200/80 text-amber-900 border border-amber-300">
                  {singleResult.open_maintenance.log_status}
                </span>
              </div>
              <div className="text-xs text-amber-900 space-y-1">
                <p><span className="font-semibold">Vendor:</span> {singleResult.open_maintenance.vendor || 'In-House'}</p>
                <p><span className="font-semibold">Reason:</span> {singleResult.open_maintenance.reason || 'Routine'}</p>
                {singleResult.open_maintenance.due_date && (
                  <p><span className="font-semibold">Expected Return:</span> {singleResult.open_maintenance.due_date}</p>
                )}
              </div>
            </div>
          )}

          {/* Active Licence Seats */}
          {singleResult.licence_seats && singleResult.licence_seats.length > 0 && (
            <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-4 space-y-2.5">
              <div className="flex items-center gap-2 text-xs font-bold text-slate-700 uppercase tracking-wider">
                <Layers className="w-4 h-4 text-emerald-600" />
                <span>Installed Software Licences ({singleResult.licence_seats.length})</span>
              </div>
              <div className="space-y-1.5">
                {singleResult.licence_seats.map((seat) => (
                  <div key={seat.name} className="p-2.5 rounded-xl bg-slate-50 border border-slate-200 flex items-center justify-between text-xs">
                    <div>
                      <p className="font-bold text-slate-800">{seat.software_name}</p>
                      <p className="text-[10px] text-slate-500">{seat.licence_name} &bull; {seat.licence_type}</p>
                    </div>
                    <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-emerald-100 text-emerald-800">
                      {seat.seat_status}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Recent Movement Audit Trail */}
          {singleResult.recent_movements && singleResult.recent_movements.length > 0 && (
            <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-4 space-y-2.5">
              <div className="flex items-center gap-2 text-xs font-bold text-slate-700 uppercase tracking-wider">
                <Clock className="w-4 h-4 text-emerald-600" />
                <span>Recent Movements ({singleResult.recent_movements.length})</span>
              </div>
              <div className="divide-y divide-slate-100 text-xs">
                {singleResult.recent_movements.slice(0, 5).map((mv) => (
                  <div key={mv.name} className="py-2 first:pt-0 last:pb-0 space-y-0.5">
                    <div className="flex items-center justify-between">
                      <span className="font-semibold text-slate-800">{mv.movement_type}</span>
                      <span className="text-[10px] text-slate-400 font-mono">{mv.movement_date}</span>
                    </div>
                    <p className="text-[11px] text-slate-500">
                      {mv.from_employee ? `${mv.from_employee} → ` : ''}{mv.to_employee || mv.to_location || 'Storage'}
                    </p>
                  </div>
                ))}
              </div>
            </div>
          )}
        </main>
      )}

      {/* SCREEN 3: MULTIPLE PARTIAL MATCHES */}
      {screen === 'MULTIPLE' && (
        <main className="flex-1 p-4 space-y-3 max-w-lg mx-auto w-full pb-8">
          <div className="flex items-center justify-between">
            <button
              type="button"
              onClick={() => resetToScan(activeTab === 'scan')}
              className="inline-flex items-center gap-1.5 text-xs font-semibold text-slate-600 hover:text-slate-900 bg-white border border-slate-300 rounded-lg px-3 py-1.5 shadow-xs"
            >
              <ArrowLeft className="w-3.5 h-3.5" />
              <span>Back to Search</span>
            </button>
            <span className="text-xs font-semibold text-slate-500">
              {multipleResults.length} Assets Found
            </span>
          </div>

          <div className="bg-amber-50 border border-amber-200 rounded-xl p-3 text-xs text-amber-800">
            <span className="font-semibold">Multiple assets matched "{lastSearchedTerm}".</span> Select an asset below to inspect its exact custody record.
          </div>

          <div className="space-y-2">
            {multipleResults.map((item) => (
              <button
                type="button"
                key={item.name}
                onClick={() => selectMultipleItem(item.asset_tag)}
                className="w-full p-3.5 bg-white hover:bg-slate-50 border border-slate-200 rounded-xl text-left shadow-xs transition-colors space-y-1 block"
              >
                <div className="flex items-center justify-between">
                  <span className="font-mono text-xs font-bold text-emerald-700">
                    {item.asset_tag}
                  </span>
                  {getStatusBadge(item.status)}
                </div>
                <p className="font-bold text-slate-900 text-sm">{item.asset_name}</p>
                <div className="flex items-center gap-2 text-xs text-slate-500 pt-0.5">
                  <span>{item.brand || 'Asset'}</span>
                  {item.serial_no && (
                    <>
                      <span>&bull;</span>
                      <span className="font-mono text-[11px]">SN: {item.serial_no}</span>
                    </>
                  )}
                  {item.holder_name && (
                    <>
                      <span>&bull;</span>
                      <span className="text-slate-700 font-medium">{item.holder_name}</span>
                    </>
                  )}
                </div>
              </button>
            ))}
          </div>
        </main>
      )}

      {/* SCREEN 4: NOT FOUND (FR-34: Names searched query, creates zero records) */}
      {screen === 'NOT_FOUND' && (
        <main className="flex-1 p-6 flex flex-col items-center justify-center text-center space-y-4">
          <div className="w-16 h-16 rounded-3xl bg-slate-100 border border-slate-200 flex items-center justify-center text-slate-400 shadow-inner">
            <SearchX className="w-8 h-8" />
          </div>

          <div className="space-y-1.5 max-w-xs">
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
