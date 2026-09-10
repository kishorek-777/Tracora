import React, { useState } from 'react';
import { X, UserPlus, ShieldCheck, AlertCircle, CheckCircle2, RefreshCw } from 'lucide-react';

export default function AssignModal({ isOpen, onClose, targetAsset, onSuccess }) {
  const [employeeId, setEmployeeId] = useState('EMP-001');
  const [employeeName, setEmployeeName] = useState('Rohan Mehta');
  const [remarks, setRemarks] = useState('Hardware refresh deployment');
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState(null);

  if (!isOpen) return null;

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setMessage(null);

    try {
      // Simulate/call assign API
      await new Promise((resolve) => setTimeout(resolve, 600));
      setMessage({ type: 'success', text: `Asset ${targetAsset?.asset_tag || 'TRC-001234'} successfully assigned to ${employeeName}. Movement record created.` });
      setTimeout(() => {
        if (onSuccess) onSuccess();
        onClose();
      }, 1200);
    } catch (err) {
      setMessage({ type: 'error', text: 'Assignment failed: Rule validation refusal.' });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/75 backdrop-blur-sm animate-fade-in">
      <div className="w-full max-w-md rounded-2xl bg-tracora-surface border border-tracora-border shadow-2xl overflow-hidden relative">
        <div className="flex items-center justify-between px-6 py-4 border-b border-tracora-border/80">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-emerald-500/15 text-emerald-400 flex items-center justify-center border border-emerald-500/30">
              <UserPlus className="w-4 h-4" />
            </div>
            <div>
              <h3 className="text-sm font-bold text-white font-sans uppercase tracking-wider">
                Assign Asset Custody
              </h3>
              <span className="text-[11px] font-mono text-tracora-muted">
                Atomic assignment with immutable movement log
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

        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          {/* Target Asset Preview */}
          <div className="p-3.5 rounded-xl bg-tracora-void border border-tracora-border space-y-1">
            <div className="text-[10px] font-mono text-tracora-muted uppercase tracking-wider">
              Selected Device
            </div>
            <div className="text-sm font-bold text-white font-sans">
              {targetAsset?.asset_name || 'MacBook Pro 14" M3 Pro'}
            </div>
            <div className="text-xs font-mono text-tracora-cyan">
              Tag: {targetAsset?.asset_tag || 'TRC-001234'} · Status: {targetAsset?.status || 'In Store'}
            </div>
          </div>

          {/* Employee Target */}
          <div className="space-y-1">
            <label className="text-xs font-mono text-slate-300 block">Assignee Employee</label>
            <select
              value={employeeId}
              onChange={(e) => {
                setEmployeeId(e.target.value);
                setEmployeeName(e.target.options[e.target.selectedIndex].text);
              }}
              className="w-full px-3 py-2 rounded-xl bg-tracora-card border border-tracora-border text-sm text-white focus:outline-none focus:border-tracora-cyan font-sans"
            >
              <option value="EMP-001">Rohan Mehta (Engineering - Hyderabad)</option>
              <option value="EMP-004">Priya Sharma (Development - Bangalore)</option>
              <option value="EMP-009">Arjun Nair (Sales - Delhi)</option>
              <option value="EMP-012">Sneha Iyer (Operations - Chennai)</option>
            </select>
          </div>

          {/* Remarks */}
          <div className="space-y-1">
            <label className="text-xs font-mono text-slate-300 block">Transfer Remarks</label>
            <textarea
              rows={2}
              value={remarks}
              onChange={(e) => setRemarks(e.target.value)}
              placeholder="Reason for custody assignment..."
              className="w-full px-3 py-2 rounded-xl bg-tracora-card border border-tracora-border text-xs text-white placeholder:text-tracora-muted focus:outline-none focus:border-tracora-cyan font-sans resize-none"
            />
          </div>

          {message && (
            <div
              className={`p-3 rounded-xl border text-xs flex items-center gap-2 ${
                message.type === 'success'
                  ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-400'
                  : 'bg-rose-500/10 border-rose-500/30 text-rose-400'
              }`}
            >
              {message.type === 'success' ? <CheckCircle2 className="w-4 h-4 flex-shrink-0" /> : <AlertCircle className="w-4 h-4 flex-shrink-0" />}
              <span>{message.text}</span>
            </div>
          )}

          <div className="pt-2 flex items-center justify-end gap-2">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 rounded-xl bg-white/[0.05] hover:bg-white/[0.1] text-xs font-semibold text-slate-300 transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading}
              className="px-5 py-2 rounded-xl bg-gradient-to-r from-tracora-blue to-tracora-cyan hover:brightness-110 text-black font-bold text-xs uppercase tracking-wider transition-all flex items-center gap-1.5 shadow-glow-cyan"
            >
              {loading && <RefreshCw className="w-3.5 h-3.5 animate-spin" />}
              <span>Confirm Assignment</span>
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
