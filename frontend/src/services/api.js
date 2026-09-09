/**
 * ChainTrace-I4C API Service Client
 */

export const API_BASE_URL = 'http://localhost:8000/api';
export const HEALTH_URL = 'http://localhost:8000/health';

export const DEMO_TOPOLOGY = {
  target: "0xVic_9011",
  terminalExchange: "CryptoGlobal Exchange (Hot Wallet 04)",
  traversalTimeMs: 4.85,
  nodesCount: 6,
  prunedDustBranches: 1,
  nodes: [
    {
      id: "0xVic_9011",
      label: "Victim Target Wallet",
      type: "victim",
      riskScore: 5,
      balance: "120.50 USDT",
      cluster: "Origin Source Wallet",
      exchangeName: null,
      jurisdiction: null,
      heuristics: { vaspMatch: 0, sweeper: 0, gasSponsor: 0, fanIn: 0 }
    },
    {
      id: "0xMule_A1",
      label: "Hop Mule e_A1",
      type: "mule",
      riskScore: 68,
      balance: "8,400.00 USDT",
      cluster: "Layering Mule Account",
      exchangeName: null,
      jurisdiction: null,
      heuristics: { vaspMatch: 10, sweeper: 85, gasSponsor: 95, fanIn: 15 }
    },
    {
      id: "0xMule_A2",
      label: "Hop Mule e_A2",
      type: "mule",
      riskScore: 74,
      balance: "14,200.00 USDT",
      cluster: "Layering Mule Account",
      exchangeName: null,
      jurisdiction: null,
      heuristics: { vaspMatch: 10, sweeper: 90, gasSponsor: 75, fanIn: 15 }
    },
    {
      id: "0xMule_B1",
      label: "Hop Mule e_B1",
      type: "mule",
      riskScore: 82,
      balance: "23,100.00 USDT",
      cluster: "Layering Mule Account",
      exchangeName: null,
      jurisdiction: null,
      heuristics: { vaspMatch: 10, sweeper: 88, gasSponsor: 75, fanIn: 15 }
    },
    {
      id: "0xConsol_99",
      label: "Hop Mule l_99",
      type: "mule",
      riskScore: 92,
      balance: "94,800.00 USDT",
      cluster: "Consolidation Hub",
      exchangeName: null,
      jurisdiction: null,
      heuristics: { vaspMatch: 10, sweeper: 95, gasSponsor: 40, fanIn: 96 }
    },
    {
      id: "0xVASP_GlobalEx",
      label: "CryptoGlobal Exchange (Hot Wallet 04)",
      type: "exchange",
      riskScore: 97,
      balance: "1,420,000.00 USDT",
      cluster: "Terminal Off-Ramp Exchange",
      exchangeName: "CryptoGlobal Exchange (Hot Wallet 04)",
      jurisdiction: "Seychelles / Non-Compliant",
      heuristics: { vaspMatch: 100, sweeper: 95, gasSponsor: 40, fanIn: 96 }
    }
  ],
  links: [
    { source: "0xVic_9011", target: "0xMule_A1", amount: "48,500.00 USDT", txHash: "0x71fb_a301", suspiciousScore: 75, latency: "42s" },
    { source: "0xMule_A1", target: "0xMule_A2", amount: "24,000.00 USDT", txHash: "0x88ea_120f", suspiciousScore: 75, latency: "18s" },
    { source: "0xMule_A1", target: "0xMule_B1", amount: "23,800.00 USDT", txHash: "0x99cb_e843", suspiciousScore: 75, latency: "22s" },
    { source: "0xMule_A2", target: "0xConsol_99", amount: "23,950.00 USDT", txHash: "0x33dc_91bc", suspiciousScore: 75, latency: "12s" },
    { source: "0xMule_B1", target: "0xConsol_99", amount: "23,720.00 USDT", txHash: "0x44fa_7302", suspiciousScore: 75, latency: "15s" },
    { source: "0xConsol_99", target: "0xVASP_GlobalEx", amount: "47,500.00 USDT", txHash: "0x10fe_ca41", suspiciousScore: 90, latency: "8s" }
  ]
};

export const PRUNED_DUST_NODE = {
  id: "0xDust_Pruned",
  label: "0xDust_Pruned (700 USDT)",
  type: "dust",
  riskScore: 35,
  balance: "42.00 USDT",
  cluster: "Pruned Dust Branch (<3%)",
  exchangeName: null,
  jurisdiction: null,
  heuristics: { vaspMatch: 0, sweeper: 10, gasSponsor: 0, fanIn: 0 }
};

export const PRUNED_DUST_LINK = {
  source: "0xVic_9011",
  target: "0xDust_Pruned",
  amount: "700.00 USDT",
  txHash: "0x22ab_9900",
  suspiciousScore: 30,
  latency: "120s"
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
    total_transactions: 36,
    unique_wallets: 38,
    graph_edges: 35,
    culprits_detected: 19,
    dataset_file: "blockchain_transactions.csv"
  };
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

export async function fetchGraphAnalysis(target = "0xVic_9011", hops = 5) {
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
    let url = `${API_BASE_URL}/graph-ml/transactions/scored?min_score=${minScore}`;
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
