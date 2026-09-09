import React, { useState, useEffect, useCallback } from 'react';
import {
  Shield,
  Activity,
  Play,
  Pause,
  RefreshCw,
  Search,
  X,
  FileText,
  Sliders,
  CheckCircle2,
  AlertCircle,
  ExternalLink,
  Zap,
} from 'lucide-react';
import RealtimeGraphCanvas from './components/RealtimeGraphCanvas';
import EntityInspector from './components/EntityInspector';
import DossierModal from './components/DossierModal';
import {
  checkBackendHealth,
  fetchForensicTrace,
  createBnssRequisition,
  DEMO_TOPOLOGY,
} from './services/api';

export default function App() {
  // Application State
  const [targetAddress, setTargetAddress] = useState('0xVic_9011');
  const [traceData, setTraceData] = useState(DEMO_TOPOLOGY);
  const [selectedNode, setSelectedNode] = useState(DEMO_TOPOLOGY.nodes.find(n => n.type === 'exchange') || DEMO_TOPOLOGY.nodes[0]);
  const [isBackendOnline, setIsBackendOnline] = useState(false);
  const [backendVersion, setBackendVersion] = useState('2.6');

  // Real-Time Controls State
  const [dustThreshold, setDustThreshold] = useState(3.0);
  const [isPlaying, setIsPlaying] = useState(true);
  const [playbackSpeed, setPlaybackSpeed] = useState(1.0);
  const [autoRefresh, setAutoRefresh] = useState(false);
  const [isLoading, setIsLoading] = useState(false);

  // Modal & Copy State
  const [isDossierOpen, setIsDossierOpen] = useState(false);
  const [dossierData, setDossierData] = useState(null);
  const [hasCopiedAddress, setHasCopiedAddress] = useState(false);
  const [hasCopiedHash, setHasCopiedHash] = useState(false);
  const [toast, setToast] = useState(null);

  // Toast Helper
  const showToast = useCallback((message, type = 'info') => {
    setToast({ message, type });
    setTimeout(() => setToast(null), 3500);
  }, []);

  // Health Polling
  const verifyHealth = useCallback(async () => {
    const status = await checkBackendHealth();
    setIsBackendOnline(status.online);
    if (status.online && status.data?.version) {
      setBackendVersion(status.data.version);
    }
  }, []);

  useEffect(() => {
    verifyHealth();
    const interval = setInterval(verifyHealth, 12000);
    return () => clearInterval(interval);
  }, [verifyHealth]);

  // Execute Trace
  const handleRunTrace = useCallback(async (target) => {
    const query = (target || targetAddress).trim();
    if (!query) return;

    setIsLoading(true);
    showToast(`Executing 5-Hop BFS Traversal for ${query}...`, 'info');

    const data = await fetchForensicTrace(query);
    setTraceData(data);
    setTargetAddress(query);

    const defaultSelection = data.nodes.find(n => n.type === 'exchange') || data.nodes[0];
    setSelectedNode(defaultSelection);

    setIsLoading(false);
  }, [targetAddress, showToast]);

  // Initial Trace Execution
  useEffect(() => {
    handleRunTrace('0xVic_9011');
  }, []);

  // Auto-Refresh Poller
  useEffect(() => {
    if (!autoRefresh) return;
    const interval = setInterval(() => {
      handleRunTrace(targetAddress);
    }, 8000);
    return () => clearInterval(interval);
  }, [autoRefresh, targetAddress, handleRunTrace]);

  // Copy Address
  const handleCopyAddress = (address) => {
    navigator.clipboard.writeText(address);
    setHasCopiedAddress(true);
    showToast(`Address copied: ${address}`, 'success');
    setTimeout(() => setHasCopiedAddress(false), 2000);
  };

  // Copy Hash
  const handleCopyHash = (hash) => {
    navigator.clipboard.writeText(hash);
    setHasCopiedHash(true);
    showToast('Cryptographic SHA-256 seal copied!', 'success');
    setTimeout(() => setHasCopiedHash(false), 2000);
  };

  // Generate BNSS Dossier
  const handleGenerateDossier = async () => {
    showToast('Compiling BNSS Sec. 94 Legal Evidence Order...', 'info');

    const payload = {
      officerId: 'IO-DELHI-402',
      targetWallet: targetAddress,
      terminalExchange: traceData.terminalExchange || 'CryptoGlobal Exchange (Hot Wallet 04)',
    };

    const result = await createBnssRequisition(payload);
    setDossierData(result);
    setIsDossierOpen(true);
    showToast(`Requisition Dossier ${result.dossierId} sealed!`, 'success');
  };

  // Compute Root Stolen Value
  const rootOutLinks = traceData.links.filter(l => l.source === traceData.target);
  const totalTracked = rootOutLinks.reduce((acc, l) => {
    const val = parseFloat(l.amount.replace(/[^0-9.-]+/g, '')) || 0;
    return acc + val;
  }, 0) || 48500;

  return (
    <div className="app-container">
      {/* 1. Header Navigation Bar */}
      <header className="app-header">
        <div className="brand-section">
          <div className="brand-icon-box">
            <Shield size={20} />
          </div>
          <div className="brand-text-wrap">
            <div className="brand-title">
              ChainTrace<span>-I4C</span>
            </div>
            <div className="brand-sub">
              Automated Blockchain Analytics &amp; Off-Ramp Forensics (SIH 2026)
            </div>
          </div>
        </div>

        <div className="header-center-pill">
          <span className="pulse-dot"></span>
          <span style={{ fontSize: '0.78rem', fontWeight: 600, color: 'var(--text-secondary)' }}>
            BNSS Sec. 94 Compliant Digital Evidence Architecture
          </span>
        </div>

        <div className="header-right">
          <div className={`connection-pill ${isBackendOnline ? 'online' : 'offline'}`}>
            <span style={{ width: 8, height: 8, borderRadius: '50%', backgroundColor: isBackendOnline ? 'var(--success)' : 'var(--danger)' }}></span>
            <span>{isBackendOnline ? `Backend Online (FastAPI v${backendVersion})` : 'Standby Demo Mode'}</span>
          </div>

          <div className="officer-badge">
            <div className="officer-avatar">IO</div>
            <div style={{ display: 'flex', flexDirection: 'column' }}>
              <span style={{ fontSize: '0.82rem', fontWeight: 700, fontFamily: 'var(--font-mono)' }}>IO-DELHI-402</span>
              <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>Cyber Crime Unit</span>
            </div>
          </div>
        </div>
      </header>

      {/* 2. Real-Time Controls Ribbon */}
      <section className="controls-ribbon">
        {/* Search Input */}
        <div className="search-field-group">
          <div className="search-input-box">
            <Search size={16} className="input-icon-left" />
            <input
              type="text"
              value={targetAddress}
              onChange={e => setTargetAddress(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && handleRunTrace()}
              placeholder="Enter Target TRC-20 Wallet Address (e.g. 0xVic_9011)..."
              spellCheck={false}
            />
            {targetAddress && (
              <button
                onClick={() => setTargetAddress('')}
                style={{ position: 'absolute', right: 10, background: 'none', border: 'none', color: 'var(--text-light)', cursor: 'pointer' }}
              >
                <X size={14} />
              </button>
            )}
          </div>
        </div>

        {/* Case Presets */}
        <div className="preset-pills">
          <span style={{ fontSize: '0.74rem', fontWeight: 600, color: 'var(--text-muted)' }}>Presets:</span>
          <button
            className={`preset-pill-btn ${targetAddress === '0xVic_9011' ? 'active' : ''}`}
            onClick={() => handleRunTrace('0xVic_9011')}
          >
            Case 9011 (5-Hop)
          </button>
          <button
            className={`preset-pill-btn ${targetAddress === '0xMule_A1' ? 'active' : ''}`}
            onClick={() => handleRunTrace('0xMule_A1')}
          >
            Mule Cluster A1
          </button>
          <button
            className={`preset-pill-btn ${targetAddress === '0xConsol_99' ? 'active' : ''}`}
            onClick={() => handleRunTrace('0xConsol_99')}
          >
            Consolidator 99
          </button>
        </div>

        {/* Real-Time Dynamic Dust Filter Slider */}
        <div className="realtime-slider-wrap" title="Slide to adjust dynamic noise filter (< % stolen value)">
          <Sliders size={14} color="var(--primary)" />
          <label>Dust Filter: {dustThreshold}%</label>
          <input
            type="range"
            min="0.5"
            max="5.0"
            step="0.5"
            value={dustThreshold}
            onChange={e => setDustThreshold(parseFloat(e.target.value))}
          />
        </div>

        {/* Real-Time Playback Particle Speed Controls */}
        <div className="playback-controls" title="Real-time fund flow particle controls">
          <button
            className={`btn-icon-play ${isPlaying ? 'active' : ''}`}
            onClick={() => setIsPlaying(!isPlaying)}
            title={isPlaying ? 'Pause Particle Animation' : 'Resume Flow Animation'}
          >
            {isPlaying ? <Pause size={14} /> : <Play size={14} />}
          </button>

          {[1.0, 2.0, 4.0].map(spd => (
            <button
              key={spd}
              className={`preset-pill-btn ${playbackSpeed === spd ? 'active' : ''}`}
              style={{ padding: '4px 8px', fontSize: '0.72rem' }}
              onClick={() => setPlaybackSpeed(spd)}
            >
              {spd}x
            </button>
          ))}
        </div>

        {/* Auto-Refresh Toggle */}
        <button
          className={`preset-pill-btn ${autoRefresh ? 'active' : ''}`}
          onClick={() => {
            setAutoRefresh(!autoRefresh);
            showToast(autoRefresh ? 'Live stream polling paused' : 'Live stream polling active (8s)', 'info');
          }}
          title="Auto-refresh graph from blockchain backend"
        >
          <RefreshCw size={13} style={{ display: 'inline', marginRight: 4, animation: autoRefresh ? 'spin 2s linear infinite' : 'none' }} />
          {autoRefresh ? 'Streaming ON' : 'Live Sync'}
        </button>

        {/* Action Button */}
        <button
          className="btn-primary-trace"
          onClick={() => handleRunTrace()}
          disabled={isLoading}
        >
          <Zap size={15} />
          {isLoading ? 'Tracing Graph...' : 'Run 5-Hop BFS Trace'}
        </button>
      </section>

      {/* 3. Main Workspace Grid */}
      <main className="workspace-grid">
        {/* Left: Metrics & Dynamic Graph Canvas */}
        <div style={{ display: 'flex', flexDirection: 'column' }}>
          {/* Metrics Ribbon */}
          <div className="metrics-ribbon">
            <div className="metric-tile">
              <div className="metric-tile-title">Terminal Off-Ramp Identified</div>
              <div className="metric-tile-val" style={{ color: 'var(--danger)' }}>
                {traceData.terminalExchange ? traceData.terminalExchange.split('(')[0].trim() : 'CryptoGlobal Ex'}
              </div>
              <div className="metric-tile-sub">Seychelles &bull; Non-Compliant Offshore VASP</div>
            </div>

            <div className="metric-tile">
              <div className="metric-tile-title">Initial Stolen Value Tracked</div>
              <div className="metric-tile-val" style={{ color: 'var(--primary)' }}>
                {totalTracked.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })} USDT
              </div>
              <div className="metric-tile-sub">TRC-20 Layering Stream &bull; Max 5 Hops</div>
            </div>

            <div className="metric-tile">
              <div className="metric-tile-title">Graph Entities Mapped</div>
              <div className="metric-tile-val">
                {traceData.nodes.length} Nodes / {traceData.links.length} Links
              </div>
              <div className="metric-tile-sub">BFS Traversal Latency: {traceData.traversalTimeMs} ms</div>
            </div>

            <div className="metric-tile">
              <div className="metric-tile-title">Dynamic Dust Pruning (&lt;{dustThreshold}%)</div>
              <div className="metric-tile-val" style={{ color: dustThreshold > 1.0 ? 'var(--warning)' : 'var(--text-secondary)' }}>
                {dustThreshold > 1.0 ? '1 Branch Pruned' : '0 Pruned (Noise Visible)'}
              </div>
              <div className="metric-tile-sub">
                {dustThreshold > 1.0 ? '0xDust_Pruned (700 USDT) filtered out' : 'Showing all micro-transfers'}
              </div>
            </div>
          </div>

          {/* Graph Stage Card */}
          <div className="graph-stage-card">
            <div className="stage-top-bar">
              <div>
                <h2 style={{ fontSize: '0.98rem', fontWeight: 800, color: 'var(--text-primary)' }}>
                  Real-Time Topological 5-Hop BFS Graph Canvas
                </h2>
                <span style={{ fontSize: '0.73rem', color: 'var(--text-muted)' }}>
                  Interactive force simulation &bull; Drag nodes freely &bull; Live animated fund flow particles
                </span>
              </div>

              <div className="stage-legend">
                <div className="legend-chip"><span className="legend-pip pip-victim"></span>Victim (Hop 0)</div>
                <div className="legend-chip"><span className="legend-pip pip-mule"></span>Layering Mule (Hop 1-3)</div>
                <div className="legend-chip"><span className="legend-pip pip-consol"></span>Consolidator (Hop 4)</div>
                <div className="legend-chip"><span className="legend-pip pip-vasp"></span>Terminal VASP (Hop 5)</div>
                <div className="legend-chip"><span className="legend-pip pip-dust"></span>Pruned Dust</div>
              </div>
            </div>

            <RealtimeGraphCanvas
              traceData={traceData}
              selectedNode={selectedNode}
              onSelectNode={setSelectedNode}
              dustThreshold={dustThreshold}
              isPlaying={isPlaying}
              playbackSpeed={playbackSpeed}
            />
          </div>
        </div>

        {/* Right: Sidebar with Inspector and Legal Action Card */}
        <aside className="sidebar-column">
          <EntityInspector
            selectedNode={selectedNode}
            onOpenDossier={handleGenerateDossier}
            onCopyAddress={handleCopyAddress}
            hasCopiedAddress={hasCopiedAddress}
          />

          {/* BNSS Order Action Card */}
          <div className="bnss-order-card">
            <div className="order-card-header">
              <div className="order-shield-icon">
                <Shield size={18} />
              </div>
              <div>
                <h3 style={{ fontSize: '0.92rem', fontWeight: 800, color: 'var(--text-primary)' }}>
                  Legal Evidence Order
                </h3>
                <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>
                  BNSS (2023) Section 94 Digital Mandate
                </span>
              </div>
            </div>

            <p style={{ padding: '16px 20px 0 20px', fontSize: '0.78rem', color: 'var(--text-secondary)', lineHeight: 1.5 }}>
              Auto-generate a cryptographically verified digital evidence requisition notice under Section 94 of BNSS to mandate emergency freeze of funds at the identified centralized exchange.
            </p>

            <button
              className="btn-generate-requisition"
              onClick={handleGenerateDossier}
            >
              <FileText size={16} />
              Generate BNSS-94 Requisition Dossier
            </button>
          </div>
        </aside>
      </main>

      {/* 4. BNSS Requisition Dossier Modal */}
      <DossierModal
        isOpen={isDossierOpen}
        onClose={() => setIsDossierOpen(false)}
        dossierData={dossierData}
        onCopyHash={handleCopyHash}
        hasCopiedHash={hasCopiedHash}
      />

      {/* 5. Toast System */}
      {toast && (
        <div style={{ position: 'fixed', bottom: 24, right: 24, zIndex: 120 }}>
          <div
            style={{
              backgroundColor: '#ffffff',
              border: '1px solid var(--border-subtle)',
              borderLeft: `4px solid ${toast.type === 'success' ? 'var(--success)' : 'var(--primary)'}`,
              borderRadius: 'var(--radius-md)',
              boxShadow: 'var(--shadow-lg)',
              padding: '12px 18px',
              fontSize: '0.82rem',
              fontWeight: 600,
              color: 'var(--text-primary)',
              display: 'flex',
              alignItems: 'center',
              gap: 10,
            }}
          >
            {toast.type === 'success' ? <CheckCircle2 size={16} color="var(--success)" /> : <Activity size={16} color="var(--primary)" />}
            <span>{toast.message}</span>
          </div>
        </div>
      )}
    </div>
  );
}
