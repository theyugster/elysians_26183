import React from 'react';
import { Copy, ShieldAlert, Check, AlertTriangle, ExternalLink } from 'lucide-react';

export default function EntityInspector({
  selectedNode,
  onOpenDossier,
  onCopyAddress,
  hasCopiedAddress,
}) {
  if (!selectedNode) {
    return (
      <div className="inspector-card">
        <div className="inspector-header">
          <h3 className="panel-title">Entity Heuristic Inspector</h3>
        </div>
        <div className="inspector-body" style={{ color: 'var(--text-muted)', fontSize: '0.84rem' }}>
          Select any node in the graph to inspect its multi-signal attribution breakdown.
        </div>
      </div>
    );
  }

  const h = selectedNode.heuristics || { vaspMatch: 10, sweeper: 15, gasSponsor: 0, fanIn: 15 };
  const isVasp = selectedNode.type === 'exchange';
  const isVictim = selectedNode.type === 'victim';

  const clusterClass = isVasp ? 'exchange' : (isVictim ? 'victim' : 'mule');

  return (
    <div className="inspector-card">
      <div className="inspector-header">
        <h3 className="panel-title">Entity Heuristic Inspector</h3>
        <span className={`cluster-type-badge ${clusterClass}`}>
          {selectedNode.cluster || (isVasp ? 'Terminal Off-Ramp' : 'Layering Mule')}
        </span>
      </div>

      <div className="inspector-body">
        {/* Entity Identity & Address */}
        <div className="entity-identity-block">
          <span style={{ fontSize: '0.94rem', fontWeight: 800, color: 'var(--text-primary)', display: 'block' }}>
            {selectedNode.label}
          </span>

          <div className="address-chip-row">
            <span className="mono-address">{selectedNode.id}</span>
            <button
              onClick={() => onCopyAddress(selectedNode.id)}
              style={{ background: 'none', border: 'none', color: 'var(--text-light)', cursor: 'pointer', display: 'flex' }}
              title="Copy Address"
            >
              {hasCopiedAddress ? <Check size={14} color="var(--success)" /> : <Copy size={14} />}
            </button>
          </div>

          <div className="dual-stats-grid">
            <div className="stat-cell">
              <span className="stat-cell-label">Current Balance</span>
              <div className="stat-cell-val">{selectedNode.balance || '0.00 USDT'}</div>
            </div>

            <div className="stat-cell">
              <span className="stat-cell-label">Composite Threat</span>
              <div className="stat-cell-val" style={{ color: isVasp || selectedNode.riskScore >= 70 ? 'var(--danger)' : 'var(--primary)' }}>
                {selectedNode.riskScore} / 100
              </div>
            </div>
          </div>
        </div>

        {/* 4-Signal Explainable Attribution Matrix (Slide 3 & 4) */}
        <div className="matrix-container">
          <span style={{ fontSize: '0.74rem', textTransform: 'uppercase', fontWeight: 800, letterSpacing: '0.04em', color: 'var(--text-secondary)' }}>
            4-Signal Attribution Matrix (Slide 3)
          </span>

          {/* 1. VASP Match */}
          <div className="matrix-row">
            <div className="matrix-meta">
              <span className="matrix-title">1. Known VASP Registry Match</span>
              <span className="matrix-percent" style={{ color: h.vaspMatch >= 90 ? 'var(--danger)' : 'var(--text-secondary)' }}>
                {h.vaspMatch}%
              </span>
            </div>
            <div className="matrix-track">
              <div className="matrix-bar-fill bar-danger" style={{ width: `${h.vaspMatch}%` }}></div>
            </div>
            <span className="matrix-caption">
              {h.vaspMatch >= 90 ? 
                'Direct match with registered non-compliant exchange hot wallet.' : 
                'Unregistered intermediary or non-custodial address.'}
            </span>
          </div>

          {/* 2. Sweeper Engine */}
          <div className="matrix-row">
            <div className="matrix-meta">
              <span className="matrix-title">2. Sweeper Engine Score</span>
              <span className="matrix-percent" style={{ color: 'var(--primary)' }}>
                {h.sweeper}%
              </span>
            </div>
            <div className="matrix-track">
              <div className="matrix-bar-fill bar-primary" style={{ width: `${h.sweeper}%` }}></div>
            </div>
            <span className="matrix-caption">
              {h.sweeper >= 60 ? 
                'Rapid automated forwarding (< 30s latency) and high-ratio balance emptying pattern detected.' : 
                'Standard transaction latency and hold duration.'}
            </span>
          </div>

          {/* 3. Gas Sponsor */}
          <div className="matrix-row">
            <div className="matrix-meta">
              <span className="matrix-title">3. Gas Sponsor Profiling</span>
              <span className="matrix-percent" style={{ color: 'var(--purple)' }}>
                {h.gasSponsor}%
              </span>
            </div>
            <div className="matrix-track">
              <div className="matrix-bar-fill bar-purple" style={{ width: `${h.gasSponsor}%` }}></div>
            </div>
            <span className="matrix-caption">
              {h.gasSponsor >= 50 ? 
                'Transactions gas-funded by unlinked supplier: 0xGasSponsor_Sybil (Sybil marker).' : 
                'Self-funding address or native gas holder.'}
            </span>
          </div>

          {/* 4. Fan-In Consolidation */}
          <div className="matrix-row">
            <div className="matrix-meta">
              <span className="matrix-title">4. Fan-In Consolidation</span>
              <span className="matrix-percent" style={{ color: 'var(--warning)' }}>
                {h.fanIn}%
              </span>
            </div>
            <div className="matrix-track">
              <div className="matrix-bar-fill bar-amber" style={{ width: `${h.fanIn}%` }}></div>
            </div>
            <span className="matrix-caption">
              {h.fanIn >= 65 ? 
                'Convergence hub: Multiple split mule branches merge into this single consolidating address.' : 
                'Linear transfer chain without reconvergence.'}
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}
