"""
Multi-Signal Heuristic Attribution Matrix (Slide 3):
1. Known VASP Registry
2. Sweeper Engine
3. Gas Sponsor Profiling
4. Fan-In Topology

SIH 2026 Upgrade — ML-Enhanced VASP Attribution Engine:
- XGBoost Feature Extraction & Classification (Mock for Hackathon)
- Value Continuity Check (Exchange Pool Merge Detection)
- Confidence Threshold Gate (BNSS Sec 94 Legal Compliance)
- Chain Break Detection (DeFi / Mixer / Privacy Bridge)
- Unknown VASP Escalation (FIU-IND)
"""

import math
import hashlib
from typing import Dict, List, Tuple, Any, Optional

# ==============================================================================
# SECTION 1: Original Heuristic Scoring Functions (Preserved)
# ==============================================================================

def calculate_sweeper_score(latency_seconds: int, forwarded_ratio: float) -> int:
    # Rapid forwarding (< 60 sec) + emptying out majority balance => High Sweeper confidence
    score = 0
    if latency_seconds <= 30:
        score += 50
    elif latency_seconds <= 60:
        score += 35
    elif latency_seconds <= 180:
        score += 15

    if forwarded_ratio >= 0.95:
        score += 50
    elif forwarded_ratio >= 0.85:
        score += 35
    elif forwarded_ratio >= 0.70:
        score += 20

    return min(100, score)

def calculate_gas_sponsor_score(has_external_sponsor: bool, sponsor_shared_count: int) -> int:
    if not has_external_sponsor:
        return 0
    if sponsor_shared_count > 3:
        return 95  # Sybil/Mule gas supplier
    if sponsor_shared_count > 1:
        return 75
    return 40

def calculate_fan_in_score(in_degree: int, out_degree: int) -> int:
    # High Fan-In: Multiple incoming mule splits consolidating into a single address
    if in_degree >= 4 and out_degree <= 2:
        return 96
    if in_degree >= 2:
        return 65
    return 15

def compute_node_threat_score(vasp: int, sweeper: int, gas: int, fan_in: int, is_vasp: bool) -> int:
    if is_vasp:
        # Off-Ramp terminal node
        return max(90, int(0.4 * vasp + 0.3 * sweeper + 0.3 * fan_in))
    
    # Mule intermediate scoring
    composite = (0.35 * sweeper) + (0.35 * gas) + (0.20 * fan_in) + (0.10 * vasp)
    return int(min(99, max(5, composite)))


# ==============================================================================
# SECTION 2: ML Feature Extraction Pipeline (SIH 2026 — XGBoost Integration)
# ==============================================================================

def extract_wallet_features(wallet_data: Dict[str, Any]) -> Dict[str, float]:
    """
    Extracts tabular features from a wallet's on-chain behavioral profile 
    for XGBoost VASP classification. These features are derived from graph
    topology, temporal patterns, and value flow analysis.

    SIH 2026 — Feature Engineering for Graph ML VASP Classifier.

    Args:
        wallet_data: Dictionary containing on-chain wallet metrics.
            Expected keys: in_edges, out_edges, total_in_amount, total_out_amount,
            min_latency, avg_latency, in_degree, out_degree, has_gas_sponsor,
            sponsor_shared_count, balance, tx_count, time_window_hours

    Returns:
        Dictionary of extracted features for model inference.
    """
    in_degree = wallet_data.get("in_degree", 0)
    out_degree = wallet_data.get("out_degree", 0)
    total_in = wallet_data.get("total_in_amount", 0.0)
    total_out = wallet_data.get("total_out_amount", 0.0)
    min_latency = wallet_data.get("min_latency", 60)
    avg_latency = wallet_data.get("avg_latency", 120)
    balance = wallet_data.get("balance", 0.0)
    tx_count = wallet_data.get("tx_count", 1)
    time_window_hours = wallet_data.get("time_window_hours", 24.0)
    has_known_neighbor = wallet_data.get("has_known_neighbor", False)

    # Feature 1: Average time to sweep funds forward (seconds)
    # Lower values indicate automated mule behavior
    avg_time_to_sweep = float(avg_latency)

    # Feature 2: Fan-in degree (count of unique senders in 30-day window)
    # High fan-in on terminal nodes is a strong VASP indicator
    fan_in_degree = float(in_degree)

    # Feature 3: Fan-out degree (count of unique recipients)
    fan_out_degree = float(out_degree)

    # Feature 4: Transaction value entropy (variance in amounts)
    # Exchanges show high entropy; mules show low entropy (uniform forwarding)
    if total_in > 0 and total_out > 0:
        ratio = total_out / total_in
        tx_value_entropy = abs(math.log(max(0.01, ratio) + 1))
    else:
        tx_value_entropy = 0.0

    # Feature 5: Balance retention rate (% of funds held vs forwarded)
    # Exchanges retain significant balance; mules retain near-zero
    if total_in > 0:
        balance_retention_rate = min(1.0, balance / total_in) * 100.0
    else:
        balance_retention_rate = 100.0

    # Feature 6: Transaction frequency (transactions per hour)
    # High frequency indicates exchange hot wallet or automated bot
    tx_frequency = tx_count / max(1.0, time_window_hours)

    # Feature 7: Known neighbor score (0.0 to 1.0)
    # Whether this wallet has direct edges to known VASP wallets
    known_neighbor_score = 1.0 if has_known_neighbor else 0.0

    return {
        "avg_time_to_sweep": avg_time_to_sweep,
        "fan_in_degree": fan_in_degree,
        "fan_out_degree": fan_out_degree,
        "tx_value_entropy": tx_value_entropy,
        "balance_retention_rate": balance_retention_rate,
        "tx_frequency": tx_frequency,
        "known_neighbor_score": known_neighbor_score,
    }


# ==============================================================================
# SECTION 3: ML VASP Attribution Classifier (XGBoost Mock — SIH 2026)
# ==============================================================================

def predict_vasp_attribution(features: Dict[str, float]) -> Dict[str, Any]:
    """
    Simulates an XGBoost `predict_proba()` call for VASP identity attribution.
    Returns a probability distribution over known exchanges and an explainability
    object simulating SHAP feature importance values.

    TODO: Replace with trained .pkl model load in production.
          model = xgboost.Booster()
          model.load_model("vasp_classifier_v2.pkl")
          dmatrix = xgb.DMatrix(pd.DataFrame([features]))
          proba = model.predict(dmatrix)

    SIH 2026 — ML Explainability for Legal Evidence Chain:
    Each prediction includes SHAP-style feature contributions so that
    Investigating Officers can audit the AI's reasoning before issuing
    BNSS Sec 94 freeze notices. This satisfies the HITL requirement.
    """
    # --- Deterministic scoring heuristic simulating a trained classifier ---
    score = 0.0
    shap_contributions: List[Dict[str, Any]] = []

    # Fan-in is the strongest VASP indicator (exchanges receive from many users)
    fan_in = features.get("fan_in_degree", 0)
    if fan_in >= 4:
        contrib = min(0.35, fan_in * 0.04)
        score += contrib
        shap_contributions.append({
            "feature": "fan_in_degree",
            "value": fan_in,
            "contribution": round(contrib * 100, 1),
            "label": f"High Fan-in Degree ({int(fan_in)}) → +{round(contrib * 100, 1)}% confidence"
        })
    elif fan_in >= 2:
        contrib = 0.15
        score += contrib
        shap_contributions.append({
            "feature": "fan_in_degree",
            "value": fan_in,
            "contribution": round(contrib * 100, 1),
            "label": f"Moderate Fan-in Degree ({int(fan_in)}) → +{round(contrib * 100, 1)}% confidence"
        })

    # Fast sweep time indicates automated mule or exchange hot wallet
    sweep_time = features.get("avg_time_to_sweep", 999)
    if sweep_time < 30:
        contrib = 0.25
        score += contrib
        shap_contributions.append({
            "feature": "avg_time_to_sweep",
            "value": sweep_time,
            "contribution": round(contrib * 100, 1),
            "label": f"Fast Avg Sweep Time ({int(sweep_time)}s) → +{round(contrib * 100, 1)}% confidence"
        })
    elif sweep_time < 120:
        contrib = 0.15
        score += contrib
        shap_contributions.append({
            "feature": "avg_time_to_sweep",
            "value": sweep_time,
            "contribution": round(contrib * 100, 1),
            "label": f"Moderate Sweep Time ({int(sweep_time)}s) → +{round(contrib * 100, 1)}% confidence"
        })

    # Known neighbor proximity boosts confidence significantly
    known_neighbor = features.get("known_neighbor_score", 0)
    if known_neighbor >= 0.5:
        contrib = 0.20
        score += contrib
        shap_contributions.append({
            "feature": "known_neighbor_score",
            "value": known_neighbor,
            "contribution": round(contrib * 100, 1),
            "label": f"Known VASP Neighbor Detected → +{round(contrib * 100, 1)}% confidence"
        })

    # High transaction frequency is exchange behavior
    tx_freq = features.get("tx_frequency", 0)
    if tx_freq >= 2.0:
        contrib = min(0.15, tx_freq * 0.03)
        score += contrib
        shap_contributions.append({
            "feature": "tx_frequency",
            "value": tx_freq,
            "contribution": round(contrib * 100, 1),
            "label": f"High Tx Frequency ({round(tx_freq, 2)}/hr) → +{round(contrib * 100, 1)}% confidence"
        })

    # Low balance retention = forwarding mule (negative VASP indicator)
    retention = features.get("balance_retention_rate", 50)
    if retention < 5.0:
        contrib = 0.10
        score += contrib
        shap_contributions.append({
            "feature": "balance_retention_rate",
            "value": retention,
            "contribution": round(contrib * 100, 1),
            "label": f"Near-Zero Balance Retention ({round(retention, 1)}%) → +{round(contrib * 100, 1)}% confidence"
        })

    # Value entropy (diverse amounts = exchange)
    entropy = features.get("tx_value_entropy", 0)
    if entropy > 0.5:
        contrib = min(0.10, entropy * 0.08)
        score += contrib
        shap_contributions.append({
            "feature": "tx_value_entropy",
            "value": entropy,
            "contribution": round(contrib * 100, 1),
            "label": f"High Value Entropy ({round(entropy, 3)}) → +{round(contrib * 100, 1)}% confidence"
        })

    # Clamp final score to [0.0, 0.99]
    top_score = round(min(0.99, max(0.0, score)), 4)

    # --- Generate probability distribution over known exchanges ---
    # In production, this comes from the XGBoost softmax output layer
    remaining = round(1.0 - top_score, 4)
    vasp_probabilities = {}

    if top_score >= 0.60:
        # High confidence — attribute to a specific exchange
        # Deterministic mock: pick exchange name based on feature hash
        feature_hash = hashlib.md5(str(sorted(features.items())).encode()).hexdigest()
        exchange_pool = ["Binance", "WazirX", "CoinDCX", "CryptoGlobal Exchange", "KuCoin"]
        idx = int(feature_hash[:4], 16) % len(exchange_pool)
        primary_exchange = exchange_pool[idx]
        secondary_exchange = exchange_pool[(idx + 1) % len(exchange_pool)]

        vasp_probabilities = {
            primary_exchange: top_score,
            secondary_exchange: round(remaining * 0.6, 4),
            "Unknown": round(remaining * 0.4, 4),
        }
    else:
        # Low confidence — no strong exchange attribution
        vasp_probabilities = {
            "Unknown": round(remaining * 0.7, 4),
            "Unidentified CEX Pattern": top_score,
            "Decentralized Protocol": round(remaining * 0.3, 4),
        }

    # Sort by probability descending
    sorted_proba = dict(sorted(vasp_probabilities.items(), key=lambda x: x[1], reverse=True))
    top_vasp_name = list(sorted_proba.keys())[0]
    top_vasp_score = list(sorted_proba.values())[0]

    # Sort SHAP contributions by absolute contribution descending
    shap_contributions.sort(key=lambda x: abs(x["contribution"]), reverse=True)

    return {
        "vasp_probabilities": sorted_proba,
        "top_vasp_name": top_vasp_name,
        "top_vasp_score": round(top_vasp_score, 4),
        "composite_confidence": round(top_score * 100, 2),
        "shap_explainability": shap_contributions,
        "model_version": "XGBoost v2.1.0-SIH2026-mock",
        "feature_count": len(features),
    }


# ==============================================================================
# SECTION 4: Value Continuity Check (Exchange Pool Merge Detection)
# ==============================================================================

def check_value_continuity(
    initial_amount: float,
    terminal_amount: float,
    threshold_pct: float = 20.0
) -> Dict[str, Any]:
    """
    SIH 2026 — Value Continuity Check:
    Compares the amount leaving the victim's wallet to the amount arriving at
    the terminal off-ramp wallet. If the terminal amount is drastically higher
    (>20% discrepancy), funds have likely merged with other deposits in an
    exchange pool, risking freeze orders against innocent co-depositors.

    This check protects against false-positive freeze notices on shared 
    exchange deposit pools (a critical legal safeguard).

    Args:
        initial_amount: Total value exfiltrated from victim wallet.
        terminal_amount: Total value observed at terminal off-ramp wallet.
        threshold_pct: Maximum acceptable discrepancy percentage (default 20%).

    Returns:
        Dictionary with continuity analysis and merge risk flag.
    """
    if initial_amount <= 0:
        return {
            "initial_amount": initial_amount,
            "terminal_amount": terminal_amount,
            "discrepancy_pct": 0.0,
            "has_funds_merged": False,
            "risk_level": "UNKNOWN",
            "advisory": "Cannot compute value continuity — zero initial amount."
        }

    discrepancy_pct = abs(terminal_amount - initial_amount) / initial_amount * 100.0
    has_merged = discrepancy_pct > threshold_pct

    if has_merged and terminal_amount > initial_amount:
        risk_level = "HIGH_MERGE_RISK"
        advisory = (
            f"CAUTION: Terminal wallet holds {discrepancy_pct:.1f}% more than stolen amount. "
            f"Funds have likely merged with innocent co-depositor balances in an exchange pool. "
            f"Freeze notice must be scoped to exact stolen amount ({initial_amount:,.2f} USDT), "
            f"not the full wallet balance ({terminal_amount:,.2f} USDT)."
        )
    elif has_merged and terminal_amount < initial_amount:
        risk_level = "VALUE_LEAK"
        advisory = (
            f"WARNING: {discrepancy_pct:.1f}% value attrition detected between victim and terminal. "
            f"Funds may have been partially cashed out via intermediate off-ramps or "
            f"absorbed as network fees / mixer service charges."
        )
    else:
        risk_level = "CLEAN_TRACE"
        advisory = (
            f"Value continuity verified: {discrepancy_pct:.1f}% discrepancy is within "
            f"acceptable {threshold_pct}% threshold. Freeze notice can target full terminal balance."
        )

    return {
        "initial_amount": round(initial_amount, 2),
        "terminal_amount": round(terminal_amount, 2),
        "discrepancy_pct": round(discrepancy_pct, 2),
        "has_funds_merged": has_merged,
        "risk_level": risk_level,
        "advisory": advisory,
    }


# ==============================================================================
# SECTION 5: Confidence Threshold Gate (BNSS Sec 94 Legal Compliance)
# ==============================================================================

# SIH 2026 — Legal action status codes for confidence-based triage
STATUS_GENERATE_BNSS_NOTICE = "GENERATE_BNSS_SEC_94_DRAFT"
STATUS_MANUAL_REVIEW = "FLAG_FOR_SENIOR_IO_REVIEW"
STATUS_DEAD_END = "DEAD_END_MANUAL_ESCALATION"
STATUS_UNKNOWN_VASP_ESCALATION = "UNKNOWN_VASP_FIU_IND_ESCALATION"


def count_agreeing_signals(
    vasp_score: int,
    sweeper_score: int,
    gas_score: int,
    fan_in_score: int,
    threshold: int = 50
) -> int:
    """
    Counts the number of independent heuristic signals that exceed
    a confidence threshold. Used by the Confidence Gate to ensure
    multiple corroborating signals before auto-generating legal notices.

    SIH 2026 — Multi-signal agreement requirement (minimum 3 of 4).
    """
    signals = [vasp_score, sweeper_score, gas_score, fan_in_score]
    return sum(1 for s in signals if s >= threshold)


def evaluate_confidence(
    top_probability_score: float,
    vasp_name: str,
    agreeing_signal_count: int = 3
) -> Dict[str, Any]:
    """
    SIH 2026 — Confidence Threshold Gate:
    Implements the three-tier decision framework required for legal compliance
    when issuing BNSS Sec 94 freeze notices based on AI attribution.

    Tiers:
        ≥ 85% confidence AND ≥ 3 signals agree → Auto-generate BNSS Sec 94 Draft
        60–84% confidence → Flag for Senior IO Review (human escalation)
        < 60% confidence → Dead end / Manual investigation required

    Special case:
        If VASP name is "Unknown" but confidence ≥ 60% → FIU-IND escalation
        (exchange behavior detected but identity unresolvable)

    Args:
        top_probability_score: Highest VASP attribution probability (0.0 to 1.0).
        vasp_name: Predicted VASP identity string.
        agreeing_signal_count: Number of heuristic signals that agree (0 to 4).

    Returns:
        Dictionary with action status, tier, and human-readable rationale.
    """
    score_pct = round(top_probability_score * 100, 2)

    # Special case: Unknown VASP with moderate+ confidence → FIU-IND escalation
    if vasp_name == "Unknown" and top_probability_score >= 0.60:
        return {
            "status": STATUS_UNKNOWN_VASP_ESCALATION,
            "confidence_pct": score_pct,
            "vasp_name": vasp_name,
            "agreeing_signals": agreeing_signal_count,
            "tier": "UNKNOWN_VASP_ESCALATION",
            "action": "Generate FIU-IND Escalation Request instead of standard freeze notice.",
            "rationale": (
                f"Exchange behavior detected with {score_pct}% confidence, but VASP identity "
                f"could not be resolved. System recommends escalation to Financial Intelligence "
                f"Unit India (FIU-IND) for cross-referencing with national VASP registry."
            ),
            "is_auto_generate": False,
            "is_chain_break": False,
        }

    # Tier 1: High confidence + multi-signal agreement → Auto-generate
    if top_probability_score >= 0.85 and agreeing_signal_count >= 3:
        return {
            "status": STATUS_GENERATE_BNSS_NOTICE,
            "confidence_pct": score_pct,
            "vasp_name": vasp_name,
            "agreeing_signals": agreeing_signal_count,
            "tier": "AUTO_GENERATE",
            "action": "Generate BNSS Sec 94 Freeze Notice Draft for IO review and digital signature.",
            "rationale": (
                f"ML classifier confidence ({score_pct}%) exceeds 85% threshold with "
                f"{agreeing_signal_count}/4 independent signals in agreement. "
                f"System recommends auto-generating freeze notice draft for IO sign-off."
            ),
            "is_auto_generate": True,
            "is_chain_break": False,
        }

    # Tier 2: Moderate confidence → Senior IO Review
    if top_probability_score >= 0.60:
        return {
            "status": STATUS_MANUAL_REVIEW,
            "confidence_pct": score_pct,
            "vasp_name": vasp_name,
            "agreeing_signals": agreeing_signal_count,
            "tier": "SENIOR_IO_REVIEW",
            "action": "Flag case for Senior Investigating Officer manual review.",
            "rationale": (
                f"ML classifier confidence ({score_pct}%) falls in 60-84% range "
                f"with {agreeing_signal_count}/4 agreeing signals. Insufficient for "
                f"auto-generation. Case requires senior officer judgment."
            ),
            "is_auto_generate": False,
            "is_chain_break": False,
        }

    # Tier 3: Low confidence → Dead end
    return {
        "status": STATUS_DEAD_END,
        "confidence_pct": score_pct,
        "vasp_name": vasp_name,
        "agreeing_signals": agreeing_signal_count,
        "tier": "DEAD_END",
        "action": "Mark as dead end. Escalate to manual cyber forensics investigation.",
        "rationale": (
            f"ML classifier confidence ({score_pct}%) is below 60% minimum threshold. "
            f"Only {agreeing_signal_count}/4 signals agree. Automated attribution is "
            f"unreliable at this confidence level. Manual investigation required."
        ),
        "is_auto_generate": False,
        "is_chain_break": False,
    }


# ==============================================================================
# SECTION 6: Chain Break Detection (DeFi / Mixer / Privacy Bridge)
# ==============================================================================

# Known non-custodial protocol patterns (SIH 2026 — chain break identifiers)
CHAIN_BREAK_PATTERNS = [
    "tornado", "mixer", "blender", "wasabi", "joinmarket",
    "samourai", "chipmixer", "sinbad", "railgun", "aztec",
    "zcash", "monero", "bridge", "swap", "uniswap", "pancakeswap",
    "1inch", "curve", "sushiswap", "defi", "dex",
]

PRIVACY_BRIDGE_PATTERNS = [
    "tornado", "railgun", "aztec", "zcash", "monero",
    "mixer", "blender", "chipmixer", "sinbad",
]


def detect_chain_break(
    tx_type: str = "",
    to_address: str = "",
    contract_label: str = ""
) -> Dict[str, Any]:
    """
    SIH 2026 — Chain Break Detection:
    Identifies when fund flow enters a non-custodial protocol (DeFi swap,
    mixer, privacy bridge) where on-chain tracing becomes impossible.

    Instead of failing silently, the system must explicitly flag:
    "Chain Break Detected: Non-Custodial Protocol - Escalate to Manual Investigation"

    Returns:
        Dictionary with chain break status and protocol classification.
    """
    combined = f"{tx_type} {to_address} {contract_label}".lower()

    is_chain_break = False
    protocol_type = "NONE"
    protocol_name = None

    for pattern in PRIVACY_BRIDGE_PATTERNS:
        if pattern in combined:
            is_chain_break = True
            protocol_type = "PRIVACY_MIXER"
            protocol_name = pattern.title()
            break

    if not is_chain_break:
        for pattern in CHAIN_BREAK_PATTERNS:
            if pattern in combined:
                is_chain_break = True
                protocol_type = "DEFI_DEX"
                protocol_name = pattern.title()
                break

    if is_chain_break:
        return {
            "is_chain_break": True,
            "protocol_type": protocol_type,
            "protocol_name": protocol_name,
            "severity": "CRITICAL" if protocol_type == "PRIVACY_MIXER" else "HIGH",
            "message": (
                f"Chain Break Detected: Non-Custodial Protocol ({protocol_name}) — "
                f"Escalate to Manual Investigation. On-chain deterministic tracing "
                f"is not possible beyond this point."
            ),
        }

    return {
        "is_chain_break": False,
        "protocol_type": "NONE",
        "protocol_name": None,
        "severity": "NONE",
        "message": None,
    }


# ==============================================================================
# SECTION 7: Unknown VASP Detection (FIU-IND Escalation)
# ==============================================================================

def detect_unknown_vasp(
    is_exchange_behavior: bool,
    is_known_vasp: bool,
    vasp_name: Optional[str] = None
) -> Dict[str, Any]:
    """
    SIH 2026 — Unknown VASP Escalation:
    If the system detects exchange-like behavior (high fan-in, high volume,
    rapid processing) but cannot match it to any known VASP in the registry,
    it must output: "Unknown Centralized Exchange — Generate FIU-IND Escalation Request"
    instead of a standard freeze notice.
    """
    if is_exchange_behavior and not is_known_vasp:
        return {
            "is_unknown_vasp": True,
            "vasp_name": vasp_name or "Unidentified Centralized Exchange",
            "action": "GENERATE_FIU_IND_ESCALATION",
            "message": (
                "Unknown Centralized Exchange detected — exchange behavioral patterns "
                "confirmed but identity not found in VASP registry. Generate FIU-IND "
                "Escalation Request for cross-referencing with national compliance database."
            ),
        }

    return {
        "is_unknown_vasp": False,
        "vasp_name": vasp_name,
        "action": "STANDARD_FLOW",
        "message": None,
    }