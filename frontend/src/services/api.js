/**
 * ChainTrace-I4C API Service Client
 * Updated for Elliptic++ Dataset Integration
 */

export const API_BASE_URL = 'http://localhost:8000/api';
export const HEALTH_URL = 'http://localhost:8000/health';

export const DEMO_TOPOLOGY = {
  target: "tx_1",
  terminalExchange: "Exchange Off-Ramp Wallet",
  traversalTimeMs: 4.85,
  nodesCount: 6,
  prunedDustBranches: 0,
  nodes: [
    {
      id: "demo_wallet_1",
      label: "Source Wallet",
      type: "victim",
      riskScore: 5,
      balance: "0.12 BTC",
      cluster: "Origin Source Wallet",
      exchangeName: null,
      jurisdiction: null,
      heuristics: { vaspMatch: 0, sweeper: 0, gasSponsor: 0, fanIn: 0 }
    },
    {
      id: "demo_wallet_2",
      label: "Mule Layer 1",
      type: "mule",
      riskScore: 72,
      balance: "2.5 BTC",
      cluster: "Layering Mule",
      exchangeName: null,
      jurisdiction: null,
      heuristics: { vaspMatch: 10, sweeper: 85, gasSponsor: 0, fanIn: 15 }
    },
    {
      id: "demo_wallet_3",
      label: "Mule Layer 2",
      type: "mule",
      riskScore: 78,
      balance: "4.8 BTC",
      cluster: "Layering Mule",
      exchangeName: null,
      jurisdiction: null,
      heuristics: { vaspMatch: 10, sweeper: 88, gasSponsor: 0, fanIn: 15 }
    },
    {
      id: "demo_wallet_4",
      label: "Consolidator",
      type: "mule",
      riskScore: 88,
      balance: "12.3 BTC",
      cluster: "Consolidation Hub",
      exchangeName: null,
      jurisdiction: null,
      heuristics: { vaspMatch: 10, sweeper: 92, gasSponsor: 0, fanIn: 90 }
    },
    {
      id: "demo_wallet_5",
      label: "Exchange Off-Ramp",
      type: "exchange",
      riskScore: 95,
      balance: "450.0 BTC",
      cluster: "Terminal Off-Ramp Exchange",
      exchangeName: "Exchange Off-Ramp Wallet",
      jurisdiction: "Offshore / Non-Compliant",
      heuristics: { vaspMatch: 100, sweeper: 95, gasSponsor: 0, fanIn: 96 }
    }
  ],
  links: [
    { source: "demo_wallet_1", target: "demo_wallet_2", amount: "2.50 BTC", txHash: "tx_1", suspiciousScore: 72, latency: "120s" },
    { source: "demo_wallet_2", target: "demo_wallet_3", amount: "1.20 BTC", txHash: "tx_2", suspiciousScore: 78, latency: "45s" },
    { source: "demo_wallet_2", target: "demo_wallet_4", amount: "1.25 BTC", txHash: "tx_3", suspiciousScore: 85, latency: "30s" },
    { source: "demo_wallet_3", target: "demo_wallet_4", amount: "1.15 BTC", txHash: "tx_4", suspiciousScore: 82, latency: "22s" },
    { source: "demo_wallet_4", target: "demo_wallet_5", amount: "12.10 BTC", txHash: "tx_5", suspiciousScore: 92, latency: "10s" }
  ]
};

export const PRUNED_DUST_NODE = {
  id: "dust_pruned",
  label: "Dust Transaction (Pruned)",
  type: "dust",
  riskScore: 15,
  balance: "0.0001 BTC",
  cluster: "Pruned Dust Branch (<3%)",
  exchangeName: null,
  jurisdiction: null,
  heuristics: { vaspMatch: 0, sweeper: 10, gasSponsor: 0, fanIn: 0 }
};

export const PRUNED_DUST_LINK = {
  source: "demo_wallet_1",
  target: "dust_pruned",
  amount: "0.0001 BTC",
  txHash: "tx_dust",
  suspiciousScore: 10,
  latency: "3600s"
};

export async function checkBackendHealth() {
  try {
    const res = await fetch(HEALTH_URL, { method: 'GET', headers: { 'Accept': 'application/json' } });
    if (res.ok) {
      const data = await res.json();
      return { online: true, data };
    }
  } catch (e) {
    // offline
  }
  return { online: false, data: null };
}

export async function fetchForensicTrace(target) {
  try {
    const res = await fetch(`${API_BASE_URL}/forensics/trace?target=${encodeURIComponent(target)}`);
    if (res.ok) {
      return await res.json();
    }
  } catch (e) {
    console.warn("Backend trace unavailable, using scenario fallback:", e);
  }
  return DEMO_TOPOLOGY;
}

export async function fetchDatasetStatus() {
  try {
    const res = await fetch(`${API_BASE_URL}/graph-ml/dataset/status`);
    if (res.ok) return await res.json();
  } catch (e) {
    console.warn("Dataset status error:", e);
  }
  return {
    status: "STANDALONE_CACHE",
    total_transactions: 5000,
    unique_wallets: 586,
    graph_edges: 1405,
    culprits_detected: 0,
    dataset_file: "Elliptic++ (offline)"
  };
}

export async function fetchDatasetInfo() {
  try {
    const res = await fetch(`${API_BASE_URL}/graph-ml/dataset/info`);
    if (res.ok) return await res.json();
  } catch (e) {
    console.warn("Dataset info error:", e);
  }
  return null;
}

export async function loadDataset(datasetPath = null) {
  try {
    const res = await fetch(`${API_BASE_URL}/graph-ml/dataset/load`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(datasetPath ? { dataset_path: datasetPath } : {})
    });
    if (res.ok) return await res.json();
  } catch (e) {
    console.warn("Dataset load error:", e);
  }
  return null;
}

export async function fetchGraphAnalysis(target = "tx_1", hops = 3) {
  try {
    const res = await fetch(`${API_BASE_URL}/graph-ml/analyze?target=${encodeURIComponent(target)}&hops=${hops}`);
    if (res.ok) return await res.json();
  } catch (e) {
    console.warn("Graph analyze error:", e);
  }
  return null;
}

export async function fetchScoredTransactions(minScore = 0, classification = null) {
  try {
    let url = `${API_BASE_URL}/graph-ml/transactions/scored?min_score=${minScore}&limit=500`;
    if (classification) url += `&classification=${encodeURIComponent(classification)}`;
    const res = await fetch(url);
    if (res.ok) return await res.json();
  } catch (e) {
    console.warn("Scored transactions error:", e);
  }
  return [];
}

export async function fetchIdentifiedCulprits() {
  try {
    const res = await fetch(`${API_BASE_URL}/graph-ml/culprits/identified`);
    if (res.ok) return await res.json();
  } catch (e) {
    console.warn("Culprits fetch error:", e);
  }
  return [];
}

export async function fetchWalletKyc(address) {
  try {
    const res = await fetch(`${API_BASE_URL}/graph-ml/wallet/${encodeURIComponent(address)}/kyc`);
    if (res.ok) return await res.json();
  } catch (e) {
    console.warn("Wallet KYC error:", e);
  }
  return null;
}

export async function createBnssRequisition(payload) {
  try {
    const res = await fetch(`${API_BASE_URL}/forensics/dossier/generate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    if (res.ok) {
      return await res.json();
    }
  } catch (e) {
    console.warn("Backend requisition failed, generating client fallback:", e);
  }

  // Client-side fallback with SHA-256 seal
  const timestamp = new Date().toISOString();
  const rawSignature = `${payload.officerId}:${payload.targetWallet}:${payload.terminalExchange}:${timestamp}`;
  const msgBuffer = new TextEncoder().encode(rawSignature);
  const hashBuffer = await crypto.subtle.digest('SHA-256', msgBuffer);
  const hashArray = Array.from(new Uint8Array(hashBuffer));
  const sha256AuditHash = hashArray.map(b => b.toString(16).padStart(2, '0')).join('');

  return {
    dossierId: `BNSS-94-${sha256AuditHash.slice(0, 10).toUpperCase()}`,
    officerId: payload.officerId,
    targetWallet: payload.targetWallet,
    terminalExchange: payload.terminalExchange,
    sha256AuditHash: sha256AuditHash,
    createdAt: timestamp,
    legalMandate: "Bharatiya Nagarik Suraksha Sanhita (BNSS) Section 94 Digital Evidence Order"
  };
}
