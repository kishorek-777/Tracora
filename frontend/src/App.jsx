import React, { useState, useEffect } from 'react';
import Sidebar from './components/Sidebar';
import Header from './components/Header';
import AssetHero from './components/AssetHero';
import IntelligenceMatrix from './components/IntelligenceMatrix';
import AssetCharts from './components/AssetCharts';
import LocationDistribution from './components/LocationDistribution';
import RecentAssetsTable from './components/RecentAssetsTable';
import MovementTimeline from './components/MovementTimeline';
import ScannerModal from './components/ScannerModal';
import AssetDetailDrawer from './components/AssetDetailDrawer';
import CommandPalette from './components/CommandPalette';
import AssignModal from './components/AssignModal';
import { fetchDashboardSummary } from './api/tracoraClient';
import { ShieldCheck, RefreshCw } from 'lucide-react';

export default function App() {
  const [activeNav, setActiveNav] = useState('dashboard');
  const [isCollapsed, setIsCollapsed] = useState(false);
  const [isScannerOpen, setIsScannerOpen] = useState(false);
  const [isCommandOpen, setIsCommandOpen] = useState(false);
  const [isAssignOpen, setIsAssignOpen] = useState(false);
  const [selectedAsset, setSelectedAsset] = useState(null);
  const [targetAssetForAssign, setTargetAssetForAssign] = useState(null);

  const [dashboardData, setDashboardData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadData() {
      try {
        const data = await fetchDashboardSummary();
        setDashboardData(data);
      } catch (err) {
        console.error('Failed to load dashboard summary:', err);
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, []);

  const handleOpenAssign = (asset) => {
    setTargetAssetForAssign(asset || dashboardData?.recent_assets?.[0]);
    setIsAssignOpen(true);
  };

  const handleInspectAsset = (asset) => {
    setSelectedAsset(asset);
  };

  return (
    <div className="min-h-screen bg-[#060913] text-tracora-text flex selection:bg-tracora-cyan selection:text-black">
      {/* 5-Tier Navigation Sidebar */}
      <Sidebar
        activeNav={activeNav}
        setActiveNav={setActiveNav}
        onOpenScanner={() => setIsScannerOpen(true)}
        isCollapsed={isCollapsed}
        setIsCollapsed={setIsCollapsed}
      />

      {/* Main Content Area */}
      <div
        className={`flex-1 flex flex-col min-w-0 transition-all duration-300 ${
          isCollapsed ? 'pl-20' : 'pl-64'
        }`}
      >
        {/* Global Command Header */}
        <Header
          onOpenCommand={() => setIsCommandOpen(true)}
          onOpenScanner={() => setIsScannerOpen(true)}
          alertsCount={dashboardData?.summary?.attention_count || 18}
          isCollapsed={isCollapsed}
        />

        {/* Viewport Frame */}
        <main className="flex-1 p-5 sm:p-7 max-w-[1680px] w-full mx-auto space-y-6">
          {loading ? (
            <div className="h-96 flex flex-col items-center justify-center gap-3">
              <RefreshCw className="w-8 h-8 text-tracora-cyan animate-spin" />
              <span className="text-xs font-mono text-tracora-muted uppercase tracking-wider">
                Synchronizing Asset Intelligence Telemetry...
              </span>
            </div>
          ) : (
            <>
              {/* Row 1: Hero Showcase & Quick Actions Hub */}
              <AssetHero
                summary={dashboardData.summary}
                featuredAsset={dashboardData.recent_assets?.[0]}
                onOpenScanner={() => setIsScannerOpen(true)}
                onOpenAssign={() => handleOpenAssign(dashboardData.recent_assets?.[0])}
                onOpenNewAsset={() => handleOpenAssign(null)}
                onSelectAsset={handleInspectAsset}
              />

              {/* Row 2: The 4 Stat Cards Row (Full width) */}
              <IntelligenceMatrix summary={dashboardData.summary} />

              {/* Row 3: Charts & Locations */}
              <div className="grid grid-cols-1 xl:grid-cols-12 gap-6 items-stretch">
                <div className="xl:col-span-8">
                  <AssetCharts
                    categories={dashboardData.categories}
                    totalAssets={dashboardData.summary.total_assets}
                  />
                </div>
                <div className="xl:col-span-4">
                  <LocationDistribution
                    locations={dashboardData.locations}
                    onSelectLocation={(loc) => {
                      if (dashboardData.recent_assets?.[0]) {
                        handleInspectAsset(dashboardData.recent_assets[0]);
                      }
                    }}
                  />
                </div>
              </div>

              {/* Row 4: Recent Assets & Recent Activity */}
              <div className="grid grid-cols-1 xl:grid-cols-12 gap-6 items-stretch">
                <div className="xl:col-span-8">
                  <RecentAssetsTable
                    assets={dashboardData.recent_assets}
                    onSelectAsset={handleInspectAsset}
                  />
                </div>
                <div className="xl:col-span-4">
                  <MovementTimeline
                    movements={dashboardData.recent_movements}
                    onSelectAsset={handleInspectAsset}
                  />
                </div>
              </div>
            </>
          )}
        </main>

        {/* Technical Footer */}
        <footer className="border-t border-tracora-border/60 bg-tracora-surface/30 px-8 py-4 flex flex-col sm:flex-row items-center justify-between gap-4 text-xs font-mono text-tracora-muted">
          <div className="flex items-center gap-2">
            <span className="font-bold text-white tracking-wider">TRACORA</span>
            <span>/</span>
            <span>Asset Management Platform</span>
          </div>
          <div className="flex items-center gap-2 text-slate-400">
            <ShieldCheck className="w-4 h-4 text-tracora-cyan" />
            <span>Built for a smarter, safer tomorrow.</span>
          </div>
        </footer>
      </div>

      {/* Interactive Modals & Drawers */}
      <ScannerModal
        isOpen={isScannerOpen}
        onClose={() => setIsScannerOpen(false)}
        onInspectAsset={handleInspectAsset}
        onOpenAssign={handleOpenAssign}
      />

      <CommandPalette
        isOpen={isCommandOpen}
        onClose={() => setIsCommandOpen(false)}
        onSelectAsset={handleInspectAsset}
        onOpenScanner={() => setIsScannerOpen(true)}
      />

      <AssetDetailDrawer
        asset={selectedAsset}
        isOpen={!!selectedAsset}
        onClose={() => setSelectedAsset(null)}
        onOpenAssign={handleOpenAssign}
      />

      <AssignModal
        isOpen={isAssignOpen}
        onClose={() => setIsAssignOpen(false)}
        targetAsset={targetAssetForAssign}
        onSuccess={async () => {
          const fresh = await fetchDashboardSummary();
          setDashboardData(fresh);
        }}
      />
    </div>
  );
}