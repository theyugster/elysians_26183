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
  Fingerprint,
  Database,
  Layers,
  ArrowUpRight
} from 'lucide-react';
import RealtimeGraphCanvas from './components/RealtimeGraphCanvas';
import EntityInspector from './components/EntityInspector';
import DossierModal from './components/DossierModal';
import CulpritKYCPanel from './components/CulpritKYCPanel';
import ScoredTransactionsFeed from './components/ScoredTransactionsFeed';
import ErrorBoundary from './components/ErrorBoundary';
import {
  checkBackendHealth,
  fetchForensicTrace,
  createBnssRequisition,
  fetchDatasetStatus,
  fetchScoredTransactions,
  fetchIdentifiedCulprits,
  fetchGraphAnalysis,
  loadDataset,
  DEMO_TOPOLOGY,
} from './services/api';

export default function App() {
  // Application State
  const [targetAddress, setTargetAddress] = useState('0xVic_9011');
  const [traceData, setTraceData] = useState(DEMO_TOPOLOGY);
  const [selectedNode, setSelectedNode] = useState(DEMO_TOPOLOGY.nodes.find(n => n.type === 'exchange') || DEMO_TOPOLOGY.nodes[0]);
  const [isBackendOnline, setIsBackendOnline] = useState(false);
  const [backendVersion, setBackendVersion] = useState('2.0');

  // Navigation / View Tabs
  const [activeTab, setActiveTab] = useState('WORKSPACE'); // 'WORKSPACE' | 'CULPRITS' | 'TRANSACTIONS'

  // Graph ML & KYC Intelligence State
  const [datasetStatus, setDatasetStatus] = useState(null);
  const [scoredTransactions, setScoredTransactions] = useState([]);
  const [culprits, setCulprits] = useState([]);

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

  // Health & Dataset Polling
  const verifyHealth = useCallback(async () => {
    const status = await checkBackendHealth();
    setIsBackendOnline(status.online);
    if (status.online && status.data?.version) {
      setBackendVersion(status.data.version);
    }
  }, []);

  const loadDatasetDetails = useCallback(async () => {
    const [status, txs, culps] = await Promise.all([
      fetchDatasetStatus(),
      fetchScoredTransactions(),
      fetchIdentifiedCulprits()
    ]);
    if (status) setDatasetStatus(status);
    if (txs && txs.length) setScoredTransactions(txs);
    if (culps && culps.length) setCulprits(culps);
  }, []);

  useEffect(() => {
    verifyHealth();
    loadDatasetDetails();
    const interval = setInterval(verifyHealth, 12000);
    return () => clearInterval(interval);
  }, [verifyHealth, loadDatasetDetails]);

  // Execute Graph ML Trace & Analysis
  const handleRunTrace = useCallback(async (target) => {
    const query = (target || targetAddress).trim();
    if (!query) return;

    setIsLoading(true);
    showToast(`Evaluating Graph Model & BFS propagation for ${query}...`, 'info');

    // Attempt Graph ML analyze endpoint first
    const mlAnalysis = await fetchGraphAnalysis(query);
    if (mlAnalysis && mlAnalysis.nodes && mlAnalysis.nodes.length > 0) {
      // Map ML analysis output format to traceData format expected by canvas
      const formattedData = {
        target: mlAnalysis.target,
        terminalExchange: mlAnalysis.terminalExchange || 'CryptoGlobal Exchange (Hot Wallet 04)',
        traversalTimeMs: 4.8,
        nodesCount: mlAnalysis.total_nodes,
        prunedDustBranches: 1,
        nodes: mlAnalysis.nodes.map(n => ({
          ...n,
          balance: n.balance || `${(n.riskScore * 1400).toLocaleString()} USDT`,
          cluster: n.role || (n.type === 'exchange' ? 'Terminal Off-Ramp' : 'Layering Mule'),
          heuristics: {
            vaspMatch: n.type === 'exchange' ? 95 : 10,
            sweeper: n.riskScore >= 70 ? 88 : 20,
            gasSponsor: 45,
            fanIn: n.riskScore >= 80 ? 90 : 25
          }
        })),
        links: mlAnalysis.links.map(l => ({
          source: l.from_address,
          target: l.to_address,
          amount: l.formatted_amount || `${l.amount.toLocaleString()} USDT`,
          txHash: l.tx_hash,
          suspiciousScore: l.fraud_score,
          latency: `${l.latency_seconds}s`,
          fraud_score: l.fraud_score,
          risk_factors: l.risk_factors
        }))
      };
      setTraceData(formattedData);
      setTargetAddress(query);

      const defaultSelection = formattedData.nodes.find(n => n.type === 'exchange' || n.isCulprit) || formattedData.nodes[0];
      setSelectedNode(defaultSelection);
    } else {
      // Fallback to legacy trace endpoint
      const data = await fetchForensicTrace(query);
      setTraceData(data);
      setTargetAddress(query);
      const defaultSelection = data.nodes.find(n => n.type === 'exchange') || data.nodes[0];
      setSelectedNode(defaultSelection);
    }

    // Refresh transaction list and culprits
    const [txs, culps] = await Promise.all([
      fetchScoredTransactions(),
      fetchIdentifiedCulprits()
    ]);
    if (txs && txs.length) setScoredTransactions(txs);
    if (culps && culps.length) setCulprits(culps);

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

  // Copy Helpers
  const handleCopyAddress = (address) => {
    navigator.clipboard.writeText(address);
    setHasCopiedAddress(true);
    showToast(`Address copied: ${address}`, 'success');
    setTimeout(() => setHasCopiedAddress(false), 2000);
  };

  const handleCopyHash = (hash) => {
    navigator.clipboard.writeText(hash);
    setHasCopiedHash(true);
    showToast('Cryptographic SHA-256 seal copied!', 'success');
    setTimeout(() => setHasCopiedHash(false), 2000);
  };

  // Re-Score Dataset Trigger
  const handleReloadDataset = async () => {
    setIsLoading(true);
    showToast('Re-scoring entire graph dataset against Graph ML Model...', 'info');
    const res = await loadDataset();
    if (res) {
      setDatasetStatus(res);
      await loadDatasetDetails();
      await handleRunTrace(targetAddress);
      showToast(`Dataset re-scored: ${res.total_transactions} txs, ${res.culprits_detected} culprits identified!`, 'success');
    }
    setIsLoading(false);
  };

  // Generate BNSS Dossier
  const handleGenerateDossier = async (targetWalletParam = null, exchangeParam = null) => {
    const target = targetWalletParam || targetAddress;
    const terminal = exchangeParam || traceData.terminalExchange || 'CryptoGlobal Exchange (Hot Wallet 04)';

    showToast(`Compiling BNSS Sec. 94 Legal Order with Culprit KYC for ${target}...`, 'info');

    const payload = {
      officerId: 'IO-DELHI-402',
      targetWallet: target,
      terminalExchange: terminal,
    };

    const result = await createBnssRequisition(payload);
    setDossierData(result);
    setIsDossierOpen(true);
    showToast(`Requisition Dossier ${result.dossierId} sealed with KYC Attachment!`, 'success');
  };

  // Handle Select Culprit from KYC Panel
  const handleSelectCulpritOnGraph = (walletAddr) => {
    setActiveTab('WORKSPACE');
    const found = traceData.nodes.find(n => n.id === walletAddr);
    if (found) {
      setSelectedNode(found);
      showToast(`Located culprit node: ${walletAddr}`, 'info');
    } else {
      handleRunTrace(walletAddr);
    }
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
              Graph ML Fraud Detection &amp; KYC Unmasking Intelligence (SIH 2026)
            </div>
          </div>
        </div>

        {/* View Navigation Tabs */}
        <div style={{
          display: 'flex',
          alignItems: 'center',
          backgroundColor: 'var(--bg-main)',
          padding: '4px',
          borderRadius: 'var(--radius-md)',
          border: '1px solid var(--border-subtle)'
        }}>
          <button
            onClick={() => setActiveTab('WORKSPACE')}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              padding: '6px 14px',
              fontSize: '0.78rem',
              fontWeight: 700,
              borderRadius: 'var(--radius-sm)',
              border: 'none',
              backgroundColor: activeTab === 'WORKSPACE' ? '#ffffff' : 'transparent',
              color: activeTab === 'WORKSPACE' ? 'var(--primary)' : 'var(--text-secondary)',
              boxShadow: activeTab === 'WORKSPACE' ? 'var(--shadow-sm)' : 'none',
              cursor: 'pointer'
            }}
          >
            <Layers size={14} />
            Graph Forensics Canvas
          </button>

          <button
            onClick={() => setActiveTab('CULPRITS')}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              padding: '6px 14px',
              fontSize: '0.78rem',
              fontWeight: 700,
              borderRadius: 'var(--radius-sm)',
              border: 'none',
              backgroundColor: activeTab === 'CULPRITS' ? '#ffffff' : 'transparent',
              color: activeTab === 'CULPRITS' ? 'var(--danger)' : 'var(--text-secondary)',
              boxShadow: activeTab === 'CULPRITS' ? 'var(--shadow-sm)' : 'none',
              cursor: 'pointer'
            }}
          >
            <Fingerprint size={14} />
            Culprit KYC Intelligence ({culprits.length})
          </button>

          <button
            onClick={() => setActiveTab('TRANSACTIONS')}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              padding: '6px 14px',
              fontSize: '0.78rem',
              fontWeight: 700,
              borderRadius: 'var(--radius-sm)',
              border: 'none',
              backgroundColor: activeTab === 'TRANSACTIONS' ? '#ffffff' : 'transparent',
              color: activeTab === 'TRANSACTIONS' ? 'var(--primary)' : 'var(--text-secondary)',
              boxShadow: activeTab === 'TRANSACTIONS' ? 'var(--shadow-sm)' : 'none',
              cursor: 'pointer'
            }}
          >
            <Activity size={14} />
            Scored Transactions ({scoredTransactions.length})
          </button>
        </div>

        {/* Status & Officer Profile */}
        <div className="header-right">
          <div className={`connection-pill ${isBackendOnline ? 'online' : 'offline'}`}>
            <span style={{ width: 8, height: 8, borderRadius: '50%', backgroundColor: isBackendOnline ? 'var(--success)' : 'var(--danger)' }}></span>
            <span>{isBackendOnline ? `FastAPI v${backendVersion} &bull; Graph Engine Active` : 'Standalone Demo Mode'}</span>
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

      {/* 2. Dataset Management & Real-Time Controls Ribbon */}
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
              placeholder="Enter Target Wallet (e.g. 0xVic_9011, 0xConsol_99)..."
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
            Victim Exfiltration (9011)
          </button>
          <button
            className={`preset-pill-btn ${targetAddress === '0xConsol_99' ? 'active' : ''}`}
            onClick={() => handleRunTrace('0xConsol_99')}
          >
            Syndicate Consolidator 99
          </button>
          <button
            className={`preset-pill-btn ${targetAddress === '0xVASP_GlobalEx' ? 'active' : ''}`}
            onClick={() => handleRunTrace('0xVASP_GlobalEx')}
          >
            Terminal VASP Hot Wallet
          </button>
        </div>

        {/* Dataset Status Badge & Re-Score Button */}
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '8px',
          padding: '4px 10px',
          backgroundColor: '#f1f5f9',
          borderRadius: 'var(--radius-md)',
          border: '1px solid var(--border-subtle)'
        }}>
          <Database size={13} color="var(--primary)" />
          <span style={{ fontSize: '0.72rem', fontWeight: 600, color: 'var(--text-secondary)' }}>
            Dataset: <strong>{datasetStatus?.dataset_file || 'blockchain_transactions.csv'}</strong> ({datasetStatus?.total_transactions || 36} txs)
          </span>
          <button
            onClick={handleReloadDataset}
            disabled={isLoading}
            style={{
              padding: '3px 8px',
              fontSize: '0.7rem',
              fontWeight: 700,
              backgroundColor: '#ffffff',
              border: '1px solid var(--border-subtle)',
              borderRadius: '4px',
              color: 'var(--primary)',
              cursor: 'pointer'
            }}
            title="Re-run graph model scoring across the entire dataset"
          >
            Re-Score
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

        {/* Flow Particle Speed */}
        <div className="playback-controls" title="Real-time fund flow particle controls">
          <button
            className={`btn-icon-play ${isPlaying ? 'active' : ''}`}
            onClick={() => setIsPlaying(!isPlaying)}
            title={isPlaying ? 'Pause Particle Animation' : 'Resume Flow Animation'}
          >
            {isPlaying ? <Pause size={14} /> : <Play size={14} />}
          </button>
        </div>

        {/* Action Button */}
        <button
          className="btn-primary-trace"
          onClick={() => handleRunTrace()}
          disabled={isLoading}
        >
          <Zap size={15} />
          {isLoading ? 'Scoring Graph...' : 'Evaluate Graph Model'}
        </button>
      </section>

      {/* 3. Main Workspace Views */}
      <main style={{ padding: '20px 24px', maxWidth: '1600px', margin: '0 auto', width: '100%' }}>
        {activeTab === 'WORKSPACE' && (
          <div className="workspace-grid" style={{ padding: 0 }}>
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
                  <div className="metric-tile-title">Culprits Unmasked by Graph ML</div>
                  <div className="metric-tile-val" style={{ color: 'var(--danger)' }}>
                    {culprits.length} Culprits Identified
                  </div>
                  <div className="metric-tile-sub">Real-World KYC &amp; Downstream Tracing Active</div>
                </div>

                <div className="metric-tile">
                  <div className="metric-tile-title">Graph Entities Mapped</div>
                  <div className="metric-tile-val">
                    {traceData.nodes.length} Nodes / {traceData.links.length} Links
                  </div>
                  <div className="metric-tile-sub">Graph Feature Inference: {traceData.traversalTimeMs} ms</div>
                </div>

                <div className="metric-tile">
                  <div className="metric-tile-title">Transactions Scored Against Model</div>
                  <div className="metric-tile-val" style={{ color: 'var(--primary)' }}>
                    {scoredTransactions.length} Evaluated
                  </div>
                  <div className="metric-tile-sub">
                    {scoredTransactions.filter(t => t.classification === 'FRAUDULENT').length} Flagged Fraudulent
                  </div>
                </div>
              </div>

              {/* Graph Stage Card */}
              <div className="graph-stage-card">
                <div className="stage-top-bar">
                  <div>
                    <h2 style={{ fontSize: '0.98rem', fontWeight: 800, color: 'var(--text-primary)' }}>
                      Real-Time Graph ML Fraud Topology Canvas
                    </h2>
                    <span style={{ fontSize: '0.73rem', color: 'var(--text-muted)' }}>
                      Edges scored by model: <span style={{ color: '#ef4444', fontWeight: 700 }}>Red &ge; 70%</span> &bull; <span style={{ color: '#f59e0b', fontWeight: 700 }}>Amber 40-69%</span> &bull; <span style={{ color: '#64748b', fontWeight: 700 }}>Slate &lt; 40%</span>
                    </span>
                  </div>

                  <div className="stage-legend">
                    <div className="legend-chip"><span className="legend-pip pip-victim"></span>Victim</div>
                    <div className="legend-chip"><span className="legend-pip pip-mule"></span>Flagged Mule</div>
                    <div className="legend-chip"><span className="legend-pip pip-consol"></span>Consolidator</div>
                    <div className="legend-chip"><span className="legend-pip pip-vasp"></span>Terminal VASP</div>
                  </div>
                </div>

                <ErrorBoundary>
                  <RealtimeGraphCanvas
                    traceData={traceData}
                    selectedNode={selectedNode}
                    onSelectNode={setSelectedNode}
                    dustThreshold={dustThreshold}
                    isPlaying={isPlaying}
                    playbackSpeed={playbackSpeed}
                  />
                </ErrorBoundary>
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
                  Auto-generate a cryptographically verified digital evidence requisition notice with Annexure A (Unmasked Culprit KYC intelligence) to mandate emergency asset freeze.
                </p>

                <button
                  className="btn-generate-requisition"
                  onClick={() => handleGenerateDossier()}
                >
                  <FileText size={16} />
                  Generate BNSS-94 Requisition Dossier
                </button>
              </div>
            </aside>
          </div>
        )}

        {/* View 2: Culprit KYC Resolution Panel */}
        {activeTab === 'CULPRITS' && (
          <CulpritKYCPanel
            culprits={culprits}
            selectedWallet={selectedNode?.id}
            onSelectCulprit={handleSelectCulpritOnGraph}
            onGenerateDossier={(wallet, name) => handleGenerateDossier(wallet, name)}
          />
        )}

        {/* View 3: Scored Transactions Feed */}
        {activeTab === 'TRANSACTIONS' && (
          <ScoredTransactionsFeed
            transactions={scoredTransactions}
          />
        )}
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
