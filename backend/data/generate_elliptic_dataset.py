"""
Elliptic++ Format Synthetic Dataset Generator for ChainTrace-I4C.

Generates 5,000 Bitcoin transactions in the exact Elliptic++ CSV schema:
  - txs_features.csv: [txId, timestep, feature_1..feature_166, local_feature_1..local_feature_17]
  - txs_classes.csv:  [txId, class]  (1=illicit, 2=licit, 3=unknown)
  - txs_edgelist.csv: [txId1, txId2]  (directed money-flow edges)
  - wallets_map.csv:  [txId, from_wallet, to_wallet, amount_btc, timestamp]

Class distribution mirrors real Elliptic++:
  ~2.2% illicit (class 1) => ~110 transactions
  ~20.6% licit  (class 2) => ~1030 transactions
  ~77.2% unknown(class 3) => ~3860 transactions

Usage:
    python generate_elliptic_dataset.py
"""
import os
import csv
import json
import random
import math
import hashlib
from datetime import datetime, timedelta

# ─── Configuration ─────────────────────────────────────────────
NUM_TRANSACTIONS = 5000
NUM_TIMESTEPS = 49
NUM_ELLIPTIC_FEATURES = 166       # Original Elliptic features
NUM_LOCAL_FEATURES = 17           # Elliptic++ additional local features
TOTAL_FEATURES = NUM_ELLIPTIC_FEATURES + NUM_LOCAL_FEATURES  # 183

# Class distribution matching Elliptic++
ILLICIT_RATIO = 0.022    # ~2.2%
LICIT_RATIO   = 0.206    # ~20.6%
# remainder = unknown   ~77.2%

OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))

random.seed(42)

# ─── Wallet Address Generation ─────────────────────────────────
def generate_wallet_address(seed_val, prefix="1"):
    """Generates a Bitcoin-style Base58 wallet address from a seed."""
    h = hashlib.sha256(str(seed_val).encode()).hexdigest()[:30]
    # Convert hex chars to Base58-like chars
    base58_chars = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
    addr = prefix
    for i in range(0, len(h), 2):
        idx = int(h[i:i+2], 16) % len(base58_chars)
        addr += base58_chars[idx]
    return addr[:34]  # Standard BTC address length

# Generate wallet pools
NUM_ILLICIT_WALLETS = 80
NUM_LICIT_WALLETS = 300
NUM_EXCHANGE_WALLETS = 15
NUM_UNKNOWN_WALLETS = 200

illicit_wallets = [generate_wallet_address(f"illicit_{i}", "1") for i in range(NUM_ILLICIT_WALLETS)]
licit_wallets = [generate_wallet_address(f"licit_{i}", "1") for i in range(NUM_LICIT_WALLETS)]
exchange_wallets = [generate_wallet_address(f"exchange_{i}", "3") for i in range(NUM_EXCHANGE_WALLETS)]
unknown_wallets = [generate_wallet_address(f"unknown_{i}", "1") for i in range(NUM_UNKNOWN_WALLETS)]

all_wallets = illicit_wallets + licit_wallets + exchange_wallets + unknown_wallets

# ─── Feature Distribution Profiles ────────────────────────────
def generate_illicit_features():
    """Illicit transactions: high volume, rapid timing, clustered patterns."""
    features = []
    # Features 1-94: Local transaction features (amount, fee, timing, etc.)
    features.append(random.gauss(8.5, 2.0))       # f1: log_amount (higher)
    features.append(random.gauss(0.002, 0.001))    # f2: fee_ratio (lower fees)
    features.append(random.gauss(2.1, 1.5))        # f3: input_count
    features.append(random.gauss(2.8, 1.8))        # f4: output_count
    features.append(random.gauss(0.85, 0.15))      # f5: output_concentration (high)
    features.append(random.gauss(45, 30))           # f6: time_since_last_tx (seconds, fast)
    features.append(random.gauss(0.92, 0.08))       # f7: forwarded_ratio (very high)
    # Fill remaining 87 local features with illicit-skewed distributions
    for i in range(7, 94):
        if i % 5 == 0:
            features.append(random.gauss(0.7, 0.2))   # Higher activity signals
        elif i % 7 == 0:
            features.append(random.gauss(-0.3, 0.5))   # Anomalous negative signals
        else:
            features.append(random.gauss(0.1, 0.4))
    # Features 95-166: Aggregated neighborhood features
    for i in range(94, NUM_ELLIPTIC_FEATURES):
        if i < 120:
            features.append(random.gauss(0.6, 0.3))   # High neighbor activity
        else:
            features.append(random.gauss(0.2, 0.5))
    # Local features 1-17 (Elliptic++ extension)
    features.append(random.gauss(5.2, 1.5))        # lf1: degree_centrality_local
    features.append(random.gauss(0.008, 0.003))     # lf2: pagerank_local
    features.append(random.gauss(3.1, 1.2))         # lf3: clustering_coeff
    features.append(random.gauss(0.75, 0.15))       # lf4: betweenness_centrality
    features.append(random.gauss(2.8, 0.8))         # lf5: in_degree
    features.append(random.gauss(3.5, 1.0))         # lf6: out_degree
    features.append(random.gauss(0.9, 0.1))         # lf7: flow_velocity
    features.append(random.gauss(0.82, 0.12))       # lf8: fan_in_ratio
    features.append(random.gauss(7.2, 2.0))         # lf9: total_volume_log
    features.append(random.gauss(0.65, 0.2))        # lf10: hub_score
    features.append(random.gauss(0.58, 0.25))       # lf11: authority_score
    features.append(random.gauss(4.5, 1.5))         # lf12: neighbor_illicit_ratio
    features.append(random.gauss(0.3, 0.15))        # lf13: time_regularity
    features.append(random.gauss(1.2, 0.5))         # lf14: amount_variance
    features.append(random.gauss(0.88, 0.1))        # lf15: rapid_hop_indicator
    features.append(random.gauss(0.7, 0.2))         # lf16: sybil_cluster_score
    features.append(random.gauss(0.45, 0.2))        # lf17: consolidation_index
    return features

def generate_licit_features():
    """Licit transactions: normal volume, regular timing, diverse patterns."""
    features = []
    features.append(random.gauss(4.5, 2.5))        # f1: log_amount (normal)
    features.append(random.gauss(0.01, 0.005))      # f2: fee_ratio (standard)
    features.append(random.gauss(1.5, 0.8))         # f3: input_count
    features.append(random.gauss(2.0, 1.0))         # f4: output_count
    features.append(random.gauss(0.5, 0.2))         # f5: output_concentration (spread)
    features.append(random.gauss(3600, 2000))        # f6: time_since_last_tx (slow)
    features.append(random.gauss(0.3, 0.2))          # f7: forwarded_ratio (low)
    for i in range(7, 94):
        features.append(random.gauss(0.0, 0.3))
    for i in range(94, NUM_ELLIPTIC_FEATURES):
        features.append(random.gauss(0.0, 0.3))
    # Local features (Elliptic++)
    features.append(random.gauss(1.5, 0.8))         # lf1
    features.append(random.gauss(0.001, 0.0005))    # lf2
    features.append(random.gauss(0.5, 0.3))         # lf3
    features.append(random.gauss(0.15, 0.1))        # lf4
    features.append(random.gauss(1.2, 0.5))         # lf5
    features.append(random.gauss(1.5, 0.7))         # lf6
    features.append(random.gauss(0.15, 0.1))        # lf7
    features.append(random.gauss(0.2, 0.15))        # lf8
    features.append(random.gauss(3.5, 1.5))         # lf9
    features.append(random.gauss(0.1, 0.08))        # lf10
    features.append(random.gauss(0.12, 0.08))       # lf11
    features.append(random.gauss(0.05, 0.03))       # lf12
    features.append(random.gauss(0.8, 0.15))        # lf13
    features.append(random.gauss(0.3, 0.15))        # lf14
    features.append(random.gauss(0.05, 0.05))       # lf15
    features.append(random.gauss(0.02, 0.02))       # lf16
    features.append(random.gauss(0.1, 0.08))        # lf17
    return features

def generate_unknown_features():
    """Unknown transactions: mixed distribution between illicit and licit."""
    features = []
    features.append(random.gauss(5.5, 3.0))
    features.append(random.gauss(0.006, 0.004))
    features.append(random.gauss(1.8, 1.0))
    features.append(random.gauss(2.3, 1.2))
    features.append(random.gauss(0.6, 0.25))
    features.append(random.gauss(1800, 1500))
    features.append(random.gauss(0.5, 0.3))
    for i in range(7, 94):
        features.append(random.gauss(0.05, 0.35))
    for i in range(94, NUM_ELLIPTIC_FEATURES):
        features.append(random.gauss(0.1, 0.35))
    # Local features
    for _ in range(NUM_LOCAL_FEATURES):
        features.append(random.gauss(0.3, 0.4))
    return features

# ─── Main Generation ───────────────────────────────────────────
def generate_dataset():
    print("=" * 60)
    print("Elliptic++ Format Dataset Generator for ChainTrace-I4C")
    print("=" * 60)

    num_illicit = int(NUM_TRANSACTIONS * ILLICIT_RATIO)
    num_licit = int(NUM_TRANSACTIONS * LICIT_RATIO)
    num_unknown = NUM_TRANSACTIONS - num_illicit - num_licit

    print(f"  Generating {NUM_TRANSACTIONS} transactions:")
    print(f"    Illicit (class 1): {num_illicit}")
    print(f"    Licit   (class 2): {num_licit}")
    print(f"    Unknown (class 3): {num_unknown}")
    print(f"  Features per transaction: {TOTAL_FEATURES}")
    print(f"  Time steps: {NUM_TIMESTEPS}")

    # Assign classes
    classes = []
    classes.extend([1] * num_illicit)
    classes.extend([2] * num_licit)
    classes.extend([3] * num_unknown)
    random.shuffle(classes)

    # Generate transaction IDs (sequential integers like real Elliptic++)
    tx_ids = list(range(1, NUM_TRANSACTIONS + 1))

    # Assign timesteps
    timesteps = []
    for i in range(NUM_TRANSACTIONS):
        ts = (i * NUM_TIMESTEPS) // NUM_TRANSACTIONS + 1
        timesteps.append(min(ts, NUM_TIMESTEPS))

    # Generate features based on class
    all_features = []
    for i in range(NUM_TRANSACTIONS):
        cls = classes[i]
        if cls == 1:
            feats = generate_illicit_features()
        elif cls == 2:
            feats = generate_licit_features()
        else:
            feats = generate_unknown_features()
        all_features.append(feats)

    # ─── Write txs_features.csv ───
    features_path = os.path.join(OUTPUT_DIR, "txs_features.csv")
    header = ["txId", "timestep"]
    header.extend([f"feature_{i+1}" for i in range(NUM_ELLIPTIC_FEATURES)])
    header.extend([f"local_feature_{i+1}" for i in range(NUM_LOCAL_FEATURES)])

    with open(features_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(header)
        for i in range(NUM_TRANSACTIONS):
            row = [tx_ids[i], timesteps[i]]
            row.extend([round(v, 6) for v in all_features[i]])
            writer.writerow(row)
    print(f"\n  ✓ Written: txs_features.csv ({NUM_TRANSACTIONS} rows × {len(header)} cols)")

    # ─── Write txs_classes.csv ───
    classes_path = os.path.join(OUTPUT_DIR, "txs_classes.csv")
    with open(classes_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["txId", "class"])
        for i in range(NUM_TRANSACTIONS):
            writer.writerow([tx_ids[i], classes[i]])
    print(f"  ✓ Written: txs_classes.csv ({NUM_TRANSACTIONS} rows)")

    # ─── Generate Edges (txs_edgelist.csv) ───
    # Create realistic money-flow patterns:
    # - Illicit txs form chains/trees (layering)
    # - Licit txs have random connections
    # - Unknown txs have moderate connectivity
    edges = []
    illicit_ids = [tx_ids[i] for i in range(NUM_TRANSACTIONS) if classes[i] == 1]
    licit_ids = [tx_ids[i] for i in range(NUM_TRANSACTIONS) if classes[i] == 2]
    unknown_ids = [tx_ids[i] for i in range(NUM_TRANSACTIONS) if classes[i] == 3]

    # Illicit chains: create laundering paths (fan-out then fan-in)
    for i in range(0, len(illicit_ids) - 1, 3):
        # Create small laundering clusters
        cluster_size = min(random.randint(3, 8), len(illicit_ids) - i)
        cluster = illicit_ids[i:i+cluster_size]

        # Fan-out from first node
        if len(cluster) >= 2:
            for j in range(1, min(4, len(cluster))):
                edges.append((cluster[0], cluster[j]))

        # Fan-in to last node
        if len(cluster) >= 3:
            for j in range(1, len(cluster) - 1):
                edges.append((cluster[j], cluster[-1]))

        # Connect cluster to an exchange (off-ramp)
        if random.random() < 0.4:
            # Pick a random unknown tx that connects to exchange
            if unknown_ids:
                offramp_tx = random.choice(unknown_ids[:100])
                edges.append((cluster[-1], offramp_tx))

    # Licit connections: sparse random edges
    for lid in licit_ids:
        num_conn = random.randint(0, 2)
        for _ in range(num_conn):
            target = random.choice(licit_ids + unknown_ids)
            if target != lid:
                edges.append((lid, target))

    # Unknown connections: moderate
    for uid in unknown_ids[:500]:
        if random.random() < 0.3:
            target = random.choice(all_wallets[:50])
            target_id = random.choice(unknown_ids + licit_ids)
            if target_id != uid:
                edges.append((uid, target_id))

    # Cross-class edges (illicit to licit via unknown)
    for i in range(min(30, len(illicit_ids))):
        if unknown_ids:
            edges.append((illicit_ids[i], random.choice(unknown_ids)))

    # Deduplicate edges
    edges = list(set(edges))
    random.shuffle(edges)

    edgelist_path = os.path.join(OUTPUT_DIR, "txs_edgelist.csv")
    with open(edgelist_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["txId1", "txId2"])
        for e in edges:
            writer.writerow(e)
    print(f"  ✓ Written: txs_edgelist.csv ({len(edges)} edges)")

    # ─── Generate Wallet Map (wallets_map.csv) ───
    # Maps each transaction to from/to wallet addresses with synthetic amounts
    base_time = datetime(2019, 1, 1)
    wallet_map_path = os.path.join(OUTPUT_DIR, "wallets_map.csv")

    # Pre-assign wallets to transaction classes
    tx_wallet_from = {}
    tx_wallet_to = {}

    for i in range(NUM_TRANSACTIONS):
        cls = classes[i]
        if cls == 1:  # illicit
            tx_wallet_from[tx_ids[i]] = random.choice(illicit_wallets)
            # Illicit txs send to other illicit wallets or exchanges
            if random.random() < 0.3:
                tx_wallet_to[tx_ids[i]] = random.choice(exchange_wallets)
            else:
                tx_wallet_to[tx_ids[i]] = random.choice(illicit_wallets)
        elif cls == 2:  # licit
            tx_wallet_from[tx_ids[i]] = random.choice(licit_wallets)
            if random.random() < 0.2:
                tx_wallet_to[tx_ids[i]] = random.choice(exchange_wallets)
            else:
                tx_wallet_to[tx_ids[i]] = random.choice(licit_wallets)
        else:  # unknown
            tx_wallet_from[tx_ids[i]] = random.choice(unknown_wallets + licit_wallets)
            tx_wallet_to[tx_ids[i]] = random.choice(unknown_wallets + exchange_wallets + licit_wallets)

    with open(wallet_map_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["txId", "from_wallet", "to_wallet", "amount_btc", "timestamp"])
        for i in range(NUM_TRANSACTIONS):
            tid = tx_ids[i]
            cls = classes[i]
            ts = timesteps[i]

            if cls == 1:
                amount = round(random.uniform(0.5, 50.0), 8)
            elif cls == 2:
                amount = round(random.uniform(0.001, 5.0), 8)
            else:
                amount = round(random.uniform(0.01, 15.0), 8)

            tx_time = base_time + timedelta(days=ts * 7, hours=random.randint(0, 23), minutes=random.randint(0, 59))

            writer.writerow([
                tid,
                tx_wallet_from[tid],
                tx_wallet_to[tid],
                amount,
                tx_time.strftime("%Y-%m-%dT%H:%M:%SZ")
            ])
    print(f"  ✓ Written: wallets_map.csv ({NUM_TRANSACTIONS} rows)")

    # ─── Generate KYC Records for Flagged Wallets ───
    generate_kyc_records(illicit_wallets, exchange_wallets)

    # Summary
    print(f"\n{'='*60}")
    print(f"Dataset generation complete!")
    print(f"  Output directory: {OUTPUT_DIR}")
    print(f"  Total transactions: {NUM_TRANSACTIONS}")
    print(f"  Total edges: {len(edges)}")
    print(f"  Unique wallets: {len(set(list(tx_wallet_from.values()) + list(tx_wallet_to.values())))}")
    print(f"{'='*60}")


def generate_kyc_records(illicit_wallets, exchange_wallets):
    """Generates synthetic KYC records for flagged wallets."""

    # Synthetic identity pools (Indian + International)
    indian_names = [
        ("Vikram Aditya Malhotra", "AADHAAR-IN-XXXX-XXXX-9142", "PAN-AAPPM9102K", "New Delhi, India", "H-24, Sector 15, Rohini, New Delhi, 110089"),
        ("Rohit Surendra Verma", "AADHAAR-IN-XXXX-XXXX-4419", "PAN-BKUPV4419M", "Mumbai, Maharashtra, India", "Flat 304, Sea Breeze Apt, Andheri West, Mumbai, 400058"),
        ("Karan Singhania", "AADHAAR-IN-XXXX-XXXX-1102", "PAN-AQZPS1102B", "Bengaluru, Karnataka, India", "42, 4th Cross, Indiranagar, Bengaluru, 560038"),
        ("Priya Nair", "AADHAAR-IN-XXXX-XXXX-7733", "PAN-CPNPN7733A", "Kochi, Kerala, India", "12A, Marine Drive, Ernakulam, Kochi, 682031"),
        ("Deepak Choudhury", "AADHAAR-IN-XXXX-XXXX-5561", "PAN-DLCPC5561R", "Kolkata, West Bengal, India", "22/1, Park Street, Kolkata, 700016"),
        ("Suresh Kumar Patel", "AADHAAR-IN-XXXX-XXXX-8890", "PAN-FRKPP8890S", "Ahmedabad, Gujarat, India", "B-45, Satellite Road, Ahmedabad, 380015"),
        ("Anil Rajput", "AADHAAR-IN-XXXX-XXXX-2234", "PAN-GHAPR2234T", "Jaipur, Rajasthan, India", "C-12, Malviya Nagar, Jaipur, 302017"),
        ("Mohammed Farooq", "AADHAAR-IN-XXXX-XXXX-6678", "PAN-HJKMF6678U", "Hyderabad, Telangana, India", "8-2-120, Banjara Hills, Hyderabad, 500034"),
        ("Rajesh Gupta", "AADHAAR-IN-XXXX-XXXX-3345", "PAN-IKJRG3345V", "Lucknow, Uttar Pradesh, India", "14, Gomti Nagar, Lucknow, 226010"),
        ("Neha Sharma", "AADHAAR-IN-XXXX-XXXX-9901", "PAN-JLKNS9901W", "Pune, Maharashtra, India", "B-12, Green Acres, Baner Road, Pune, 411045"),
    ]

    international_names = [
        ("Mikhail A. Volkov", "PASSPORT-RUS-78192044", "TAX-SEY-990141", "Victoria, Mahé, Seychelles", "Suite 402, Eden Plaza, Eden Island, Mahe, Seychelles"),
        ("Chen Wei", "PASSPORT-HKG-E8819204", "HK-BRN-6601928", "Hong Kong SAR / Belize", "Room 1804, Hollywood Commercial Center, Mong Kok, Hong Kong"),
        ("Marcus Sterling", "PASSPORT-GBR-55419028", "BVI-CO-88192", "Road Town, Tortola, BVI", "Wickhams Cay 1, P.O. Box 3140, Road Town, Tortola, BVI"),
        ("Sergey Bogdanov", "PASSPORT-RUS-45091823", "INN-7704192081", "Almaty, Kazakhstan", "Dostyk Ave 105, Almaty 050051, Kazakhstan"),
        ("Andrei Petrov", "PASSPORT-RUS-62810933", "INN-7709441022", "Moscow, Russia", "Ul. Tverskaya 15, Moscow, 125009, Russia"),
        ("Li Jun", "PASSPORT-CHN-G4429100", "CN-TAX-310101992", "Shanghai, China", "Pudong New Area, Lujiazui, Shanghai, 200120"),
        ("Omar Al-Rashid", "PASSPORT-UAE-A9921001", "UAE-TRN-100199288", "Dubai, UAE", "Business Bay, Dubai, UAE"),
        ("James O'Brien", "PASSPORT-IRL-PP9912044", "IE-TIN-8812901S", "Dublin, Ireland", "14 Fitzwilliam Square, Dublin 2, Ireland"),
    ]

    indian_banks = [
        {"bank_name": "HDFC Bank Ltd", "swift_bic": "HDFCINBB", "ifsc": "HDFC0001204", "currency": "INR"},
        {"bank_name": "ICICI Bank Ltd", "swift_bic": "ICICINBB", "ifsc": "ICIC0000014", "currency": "INR"},
        {"bank_name": "State Bank of India", "swift_bic": "SBININBB", "ifsc": "SBIN0000812", "currency": "INR"},
        {"bank_name": "Axis Bank Ltd", "swift_bic": "AXISINBB", "ifsc": "UTIB0000037", "currency": "INR"},
        {"bank_name": "Punjab National Bank", "swift_bic": "PUNBINBB", "ifsc": "PUNB0024200", "currency": "INR"},
        {"bank_name": "Bank of Baroda", "swift_bic": "BARBINBB", "ifsc": "BARB0ANDHEW", "currency": "INR"},
    ]

    offshore_banks = [
        {"bank_name": "Offshore Merchant Bank of Vanuatu", "swift_bic": "OMBVVUVU", "currency": "USD"},
        {"bank_name": "East Asia Merchant Bank Ltd", "swift_bic": "EAMBHKHH", "currency": "USD"},
        {"bank_name": "BVI Commercial Bank", "swift_bic": "BVICVGAA", "currency": "USD"},
        {"bank_name": "Kaspi Bank JSC", "swift_bic": "CASPKZKA", "currency": "KZT"},
        {"bank_name": "Dubai Islamic Bank", "swift_bic": "DUIBAEADXXX", "currency": "AED"},
    ]

    kyc_records = []

    # Generate KYC for illicit wallets (mules, consolidators)
    for i, wallet in enumerate(illicit_wallets[:30]):
        identity = indian_names[i % len(indian_names)]
        bank = indian_banks[i % len(indian_banks)]
        acct_num = f"{random.randint(10000000000, 99999999999)}"
        kyc_records.append({
            "wallet_address": wallet,
            "entity_name": f"{identity[0]} (Flagged Mule Node {i+1})",
            "entity_type": "MULE_OPERATOR" if i % 3 == 0 else "MULE_CONSOLIDATOR",
            "kyc_status": "VERIFIED_MULE_ACC" if random.random() < 0.6 else "UNHOSTED_WALLET_LINKED",
            "primary_beneficiary": identity[0],
            "national_id": identity[1],
            "tax_id": identity[2],
            "jurisdiction": identity[3],
            "physical_address": identity[4],
            "registered_email": f"{identity[0].split()[0].lower()}.{random.randint(100,999)}@gmail.com",
            "registered_phone": f"+91 {random.randint(70000,99999)} {random.randint(10000,99999)}",
            "linked_bank_accounts": [{
                **bank,
                "account_number": acct_num
            }],
            "associated_ips": [f"{random.randint(1,223)}.{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}" for _ in range(random.randint(1, 3))],
            "account_creation_date": f"2025-{random.randint(1,12):02d}-{random.randint(1,28):02d}T{random.randint(0,23):02d}:00:00Z",
            "risk_classification": random.choice(["PRIMARY_SYNDICATE_CULPRIT", "FORWARDING_MULE", "MULE_RING_OPERATOR"])
        })

    # Generate KYC for exchange wallets (off-ramps)
    for i, wallet in enumerate(exchange_wallets):
        identity = international_names[i % len(international_names)]
        bank = offshore_banks[i % len(offshore_banks)]
        exchange_names = [
            "CryptoGlobal Exchange Services Ltd",
            "OffshoreX Trading Terminal BVI",
            "Pacific Digital Assets Exchange",
            "Meridian Crypto Holdings",
            "SilkRoute Exchange DMCC",
            "CoinNest International Ltd",
            "Phoenix Trading Terminal",
            "Atlas Digital Exchange",
            "Vertex Crypto OTC Desk",
            "NovaPay Exchange Services",
            "Eclipse Trading Platform",
            "Orion Crypto Exchange Ltd",
            "Delta OTC Trading Corp",
            "Zenith Digital Markets",
            "Quantum Exchange BVI"
        ]
        kyc_records.append({
            "wallet_address": wallet,
            "entity_name": f"{exchange_names[i]} (Hot Wallet {i+1:02d})",
            "entity_type": "CENTRALIZED_EXCHANGE",
            "kyc_status": random.choice(["UNCOOPERATIVE_OFFSHORE", "SHELL_JURISDICTION", "FLAGGED_HIGH_RISK"]),
            "primary_beneficiary": f"{identity[0]} / {exchange_names[i]}",
            "national_id": identity[1],
            "tax_id": identity[2],
            "jurisdiction": identity[3],
            "physical_address": identity[4],
            "registered_email": f"compliance@{exchange_names[i].lower().replace(' ', '-')[:20]}.io",
            "registered_phone": f"+{random.choice([852, 971, 65, 1, 248])} {random.randint(1000,9999)} {random.randint(1000,9999)}",
            "linked_bank_accounts": [{
                **bank,
                "account_number": f"{random.choice(['VG','KY','BZ','HK','SG'])}{random.randint(10,99)}-{random.randint(1000,9999)}-{random.randint(1000,9999)}"
            }],
            "associated_ips": [f"{random.randint(1,223)}.{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}" for _ in range(2)],
            "account_creation_date": f"2024-{random.randint(1,12):02d}-{random.randint(1,28):02d}T{random.randint(0,23):02d}:00:00Z",
            "risk_classification": random.choice(["CRITICAL_OFFRAMP_SUSPECT", "OFFRAMP_HOST", "AUTOMATION_COORDINATOR"])
        })

    # Add a few licit user KYC records
    licit_identities = [
        ("Ananya Sharma", "AADHAAR-IN-XXXX-XXXX-5501", "PAN-BKKPS5501A", "Pune, Maharashtra, India", "B-12, Green Acres, Baner Road, Pune, 411045"),
        ("Ravi Krishnamurthy", "AADHAAR-IN-XXXX-XXXX-6612", "PAN-CLKRK6612B", "Chennai, Tamil Nadu, India", "15, Anna Salai, T. Nagar, Chennai, 600017"),
        ("Sunita Desai", "AADHAAR-IN-XXXX-XXXX-7723", "PAN-DMKSD7723C", "Bangalore, Karnataka, India", "23, MG Road, Bangalore, 560001"),
    ]
    for i, wallet in enumerate(licit_wallets[:3]):
        identity = licit_identities[i]
        bank = indian_banks[i % len(indian_banks)]
        kyc_records.append({
            "wallet_address": wallet,
            "entity_name": f"{identity[0]} (Verified Retail Trader)",
            "entity_type": "LICIT_RETAIL_USER",
            "kyc_status": "TIER_2_VERIFIED",
            "primary_beneficiary": identity[0],
            "national_id": identity[1],
            "tax_id": identity[2],
            "jurisdiction": identity[3],
            "physical_address": identity[4],
            "registered_email": f"{identity[0].split()[0].lower()}.verified@gmail.com",
            "registered_phone": f"+91 {random.randint(70000,99999)} {random.randint(10000,99999)}",
            "linked_bank_accounts": [{
                **bank,
                "account_number": f"{random.randint(10000000000, 99999999999)}"
            }],
            "associated_ips": [f"14.139.{random.randint(1,255)}.{random.randint(1,255)}"],
            "account_creation_date": f"2023-{random.randint(1,12):02d}-{random.randint(1,28):02d}T12:00:00Z",
            "risk_classification": "LEGITIMATE_USER"
        })

    kyc_path = os.path.join(OUTPUT_DIR, "kyc_records_elliptic.json")
    with open(kyc_path, "w", encoding="utf-8") as f:
        json.dump(kyc_records, f, indent=2, ensure_ascii=False)
    print(f"  ✓ Written: kyc_records_elliptic.json ({len(kyc_records)} records)")


if __name__ == "__main__":
    generate_dataset()
