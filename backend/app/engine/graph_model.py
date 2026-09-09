import math
import time
import os
import pandas as pd
import numpy as np
import networkx as nx
from typing import Dict, List, Tuple, Any, Optional
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler

class GraphFraudModel:
    """
    Graph Machine Learning Fraud Detection Engine for Elliptic++ Dataset.

    Loads the Elliptic++ 3-file format (txs_features.csv, txs_classes.csv, txs_edgelist.csv)
    plus a wallet mapping file. Trains a Random Forest classifier on labeled transactions
    using 183 Elliptic features + computed graph-topological features (PageRank, HITS,
    degree centrality), then scores every transaction in the dataset.
    """

    def __init__(self, data_dir: Optional[str] = None):
        self.data_dir = data_dir or os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..", "..", "data")
        )
        self.g = nx.DiGraph()
        self.transactions_df = pd.DataFrame()
        self.wallet_map_df = pd.DataFrame()
        self.scored_transactions: List[Dict[str, Any]] = []
        self.scored_wallets: Dict[str, Dict[str, Any]] = {}
        self.culprits: List[Dict[str, Any]] = []
        self.is_loaded = False
        self.node_features: Dict[str, Dict[str, float]] = {}
        self.classifier = None
        self.scaler = None
        self.dataset_info: Dict[str, Any] = {}

    def load_dataset(self, custom_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Loads the Elliptic++ format dataset:
          - txs_features.csv: [txId, timestep, feature_1..feature_183]
          - txs_classes.csv:  [txId, class] (1=illicit, 2=licit, 3=unknown)
          - txs_edgelist.csv: [txId1, txId2] (directed edges)
          - wallets_map.csv:  [txId, from_wallet, to_wallet, amount_btc, timestamp]
        """
        data_dir = custom_path or self.data_dir

        features_path = os.path.join(data_dir, "txs_features.csv")
        classes_path = os.path.join(data_dir, "txs_classes.csv")
        edgelist_path = os.path.join(data_dir, "txs_edgelist.csv")
        wallet_map_path = os.path.join(data_dir, "wallets_map.csv")

        # Validate all required files exist
        for fpath, fname in [(features_path, "txs_features.csv"), (classes_path, "txs_classes.csv"),
                             (edgelist_path, "txs_edgelist.csv"), (wallet_map_path, "wallets_map.csv")]:
            if not os.path.exists(fpath):
                raise FileNotFoundError(f"Elliptic++ dataset file not found: {fname} in {data_dir}")

        start_time = time.time()

        # 1. Load features
        features_df = pd.read_csv(features_path)
        feature_cols = [c for c in features_df.columns if c.startswith("feature_") or c.startswith("local_feature_")]

        # 2. Load classes
        classes_df = pd.read_csv(classes_path)
        classes_df.columns = ["txId", "class"]

        # 3. Merge features + classes
        merged = features_df.merge(classes_df, on="txId", how="left")
        merged["class"] = merged["class"].fillna(3).astype(int)

        # 4. Load edges
        edges_df = pd.read_csv(edgelist_path)

        # 5. Load wallet map
        self.wallet_map_df = pd.read_csv(wallet_map_path)

        # Store merged transaction data
        self.transactions_df = merged

        # 6. Build NetworkX graph from edges
        self.g.clear()
        for _, row in edges_df.iterrows():
            self.g.add_edge(str(int(row["txId1"])), str(int(row["txId2"])))

        # Also add all transaction nodes (some may not have edges)
        for tx_id in merged["txId"].values:
            self.g.add_node(str(int(tx_id)))

        # 7. Extract graph-topological features
        graph_features = self._extract_graph_topological_features()

        # 8. Train Random Forest on labeled data & score all transactions
        self._train_and_score(merged, feature_cols, graph_features)

        elapsed = round((time.time() - start_time) * 1000, 1)

        # Dataset info
        self.dataset_info = {
            "total_transactions": len(merged),
            "total_edges": len(edges_df),
            "unique_wallets": self.wallet_map_df[["from_wallet", "to_wallet"]].stack().nunique(),
            "num_features": len(feature_cols),
            "timesteps": int(merged["timestep"].max()) if "timestep" in merged.columns else 49,
            "class_distribution": {
                "illicit": int((merged["class"] == 1).sum()),
                "licit": int((merged["class"] == 2).sum()),
                "unknown": int((merged["class"] == 3).sum()),
            },
            "graph_nodes": self.g.number_of_nodes(),
            "graph_edges": self.g.number_of_edges(),
            "model_training_time_ms": elapsed
        }

        self.is_loaded = True

        return {
            "status": "LOADED",
            "total_transactions": len(merged),
            "unique_wallets": self.dataset_info["unique_wallets"],
            "graph_edges": self.g.number_of_edges(),
            "culprits_detected": len(self.culprits),
            "dataset_file": "Elliptic++ (txs_features.csv + txs_classes.csv + txs_edgelist.csv)"
        }

    def _extract_graph_topological_features(self) -> Dict[str, Dict[str, float]]:
        """Computes graph-topological features for every node in the transaction graph."""
        n_nodes = max(1, self.g.number_of_nodes())

        # PageRank
        try:
            pagerank = nx.pagerank(self.g, alpha=0.85, max_iter=100)
        except Exception:
            pagerank = {n: 1.0 / n_nodes for n in self.g.nodes()}

        # Degree Centrality
        deg_centrality = nx.degree_centrality(self.g)

        # HITS
        try:
            hubs, authorities = nx.hits(self.g, max_iter=50)
        except Exception:
            hubs = {n: 0.0 for n in self.g.nodes()}
            authorities = {n: 0.0 for n in self.g.nodes()}

        graph_features = {}
        for node in self.g.nodes():
            in_deg = self.g.in_degree(node)
            out_deg = self.g.out_degree(node)

            graph_features[node] = {
                "in_degree": in_deg,
                "out_degree": out_deg,
                "pagerank": pagerank.get(node, 0.0),
                "deg_centrality": deg_centrality.get(node, 0.0),
                "hub_score": hubs.get(node, 0.0),
                "authority_score": authorities.get(node, 0.0),
                "fan_in_ratio": in_deg / max(1, in_deg + out_deg),
                "fan_out_ratio": out_deg / max(1, in_deg + out_deg),
            }

        self.node_features = graph_features
        return graph_features

    def _train_and_score(self, merged_df: pd.DataFrame, feature_cols: List[str],
                         graph_features: Dict[str, Dict[str, float]]):
        """
        Trains a Random Forest on labeled (illicit vs licit) transactions using
        Elliptic features + graph-topological features, then scores ALL transactions.
        """
        # Add graph features to merged dataframe
        graph_feature_names = ["in_degree", "out_degree", "pagerank", "deg_centrality",
                               "hub_score", "authority_score", "fan_in_ratio", "fan_out_ratio"]

        for gf_name in graph_feature_names:
            merged_df[f"graph_{gf_name}"] = merged_df["txId"].apply(
                lambda tx: graph_features.get(str(int(tx)), {}).get(gf_name, 0.0)
            )

        all_feature_cols = feature_cols + [f"graph_{gf}" for gf in graph_feature_names]

        # Prepare training data (only labeled: class 1 or 2)
        labeled_mask = merged_df["class"].isin([1, 2])
        labeled_df = merged_df[labeled_mask].copy()

        X_train = labeled_df[all_feature_cols].fillna(0.0).values
        y_train = (labeled_df["class"] == 1).astype(int).values  # 1=illicit, 0=licit

        # Scale features
        self.scaler = StandardScaler()
        X_train_scaled = self.scaler.fit_transform(X_train)

        # Train Random Forest
        self.classifier = RandomForestClassifier(
            n_estimators=100,
            max_depth=12,
            min_samples_split=5,
            min_samples_leaf=2,
            class_weight="balanced",  # Handle class imbalance
            random_state=42,
            n_jobs=-1
        )
        self.classifier.fit(X_train_scaled, y_train)

        # Score ALL transactions (including unknown)
        X_all = merged_df[all_feature_cols].fillna(0.0).values
        X_all_scaled = self.scaler.transform(X_all)

        # Get fraud probabilities
        fraud_probs = self.classifier.predict_proba(X_all_scaled)[:, 1]

        # Build wallet lookup from wallet_map
        wallet_lookup = {}
        for _, row in self.wallet_map_df.iterrows():
            wallet_lookup[int(row["txId"])] = {
                "from_wallet": str(row["from_wallet"]),
                "to_wallet": str(row["to_wallet"]),
                "amount_btc": float(row["amount_btc"]),
                "timestamp": str(row["timestamp"])
            }

        # Build scored transactions list
        scored_txs = []
        wallet_threat_scores: Dict[str, List[float]] = {}

        for idx, row in merged_df.iterrows():
            tx_id = int(row["txId"])
            prob = float(fraud_probs[idx])
            fraud_score = int(round(prob * 100))
            elliptic_class = int(row["class"])
            timestep = int(row.get("timestep", 1))

            if fraud_score >= 70:
                classification = "FRAUDULENT"
            elif fraud_score >= 40:
                classification = "SUSPICIOUS"
            else:
                classification = "LEGITIMATE"

            # Get wallet info
            winfo = wallet_lookup.get(tx_id, {})
            from_addr = winfo.get("from_wallet", f"wallet_{tx_id}_src")
            to_addr = winfo.get("to_wallet", f"wallet_{tx_id}_dst")
            amount = winfo.get("amount_btc", 0.0)
            timestamp = winfo.get("timestamp", "")

            # Build risk factors from top feature importances
            risk_factors = self._compute_risk_factors(row, all_feature_cols, fraud_score, elliptic_class)

            scored_txs.append({
                "tx_hash": f"tx_{tx_id}",
                "from_address": from_addr,
                "to_address": to_addr,
                "amount": amount,
                "formatted_amount": f"{amount:.6f} BTC",
                "latency_seconds": max(1, int(abs(row.get("feature_6", 60)))),
                "gas_sponsor": None,
                "tx_type": self._infer_tx_type(fraud_score, elliptic_class),
                "fraud_probability": round(prob, 4),
                "fraud_score": fraud_score,
                "classification": classification,
                "risk_factors": risk_factors,
                "timestamp": timestamp,
                "time_step": timestep,
                "elliptic_class": elliptic_class
            })

            # Track wallet threat scores
            for addr in [from_addr, to_addr]:
                if addr not in wallet_threat_scores:
                    wallet_threat_scores[addr] = []
                wallet_threat_scores[addr].append(fraud_score)

        self.scored_transactions = scored_txs

        # Build wallet classifications
        self._classify_wallets(wallet_threat_scores)

    def _compute_risk_factors(self, row, feature_cols: List[str],
                              fraud_score: int, elliptic_class: int) -> List[str]:
        """Generates human-readable risk factor explanations based on features."""
        factors = []

        if elliptic_class == 1:
            factors.append("Ground-Truth Labeled ILLICIT in Elliptic++ Dataset")

        if fraud_score >= 85:
            factors.append("Extreme Fraud Probability (≥85%) from Random Forest Ensemble")
        elif fraud_score >= 70:
            factors.append("High Fraud Probability (≥70%) from Random Forest Ensemble")

        # Check specific Elliptic features
        if hasattr(row, "feature_1") and row.get("feature_1", 0) > 7.0:
            factors.append(f"Anomalous Transaction Volume (feature_1={row['feature_1']:.2f})")

        if hasattr(row, "feature_5") and row.get("feature_5", 0) > 0.75:
            factors.append(f"High Output Concentration ({row['feature_5']:.2f}) — Layering Indicator")

        if hasattr(row, "feature_7") and row.get("feature_7", 0) > 0.80:
            factors.append(f"Rapid Forward Ratio ({row['feature_7']:.2f}) — Automated Sweeper Pattern")

        if hasattr(row, "graph_pagerank") and row.get("graph_pagerank", 0) > 0.005:
            factors.append(f"High PageRank Centrality ({row['graph_pagerank']:.4f}) — Hub Node")

        if hasattr(row, "graph_in_degree") and row.get("graph_in_degree", 0) >= 3:
            factors.append(f"Fan-In Convergence (in_degree={int(row['graph_in_degree'])}) — Consolidation Pattern")

        if hasattr(row, "local_feature_15") and row.get("local_feature_15", 0) > 0.7:
            factors.append("Rapid Hop Indicator — Automated Fund Movement")

        if hasattr(row, "local_feature_16") and row.get("local_feature_16", 0) > 0.5:
            factors.append("Sybil Cluster Scoring — Linked Coordinated Addresses")

        if not factors:
            if fraud_score < 30:
                factors.append("Standard Bitcoin Transfer — No Anomalies Detected")
            else:
                factors.append("Moderate Risk — Mixed Feature Signals")

        return factors

    def _infer_tx_type(self, fraud_score: int, elliptic_class: int) -> str:
        """Infers transaction type from fraud score and class label."""
        if elliptic_class == 1:
            if fraud_score >= 80:
                return "illicit_laundering"
            return "illicit_transfer"
        elif elliptic_class == 2:
            return "licit_transfer"
        else:
            if fraud_score >= 70:
                return "suspected_illicit"
            elif fraud_score >= 40:
                return "suspicious_transfer"
            return "unknown_transfer"

    def _classify_wallets(self, wallet_threat_scores: Dict[str, List[float]]):
        """Classifies wallets based on aggregated transaction fraud scores."""
        culprit_list = []
        wallet_dict = {}

        for addr, scores in wallet_threat_scores.items():
            avg_score = int(round(sum(scores) / len(scores)))
            max_score = max(scores)
            tx_count = len(scores)

            # Graph features for this wallet's transactions
            graph_feat = self.node_features.get(addr, {})

            # Role classification
            if avg_score >= 75:
                if max_score >= 90:
                    role = "CULPRIT_OFFRAMP"
                else:
                    role = "CULPRIT_MULE"
                is_culprit = True
            elif avg_score >= 55:
                role = "CULPRIT_CONSOLIDATOR"
                is_culprit = True
            elif avg_score >= 35:
                role = "SUSPICIOUS_INTERMEDIARY"
                is_culprit = False
            else:
                role = "LEGITIMATE_USER"
                is_culprit = False

            wallet_entry = {
                "address": addr,
                "threat_score": avg_score,
                "role": role,
                "is_culprit": is_culprit,
                "in_degree": graph_feat.get("in_degree", 0),
                "out_degree": graph_feat.get("out_degree", 0),
                "pagerank": round(graph_feat.get("pagerank", 0.0), 6),
                "in_volume": 0.0,
                "out_volume": 0.0,
                "tx_count": tx_count,
                "max_fraud_score": max_score
            }

            # Compute volumes from wallet map
            from_txs = self.wallet_map_df[self.wallet_map_df["from_wallet"] == addr]
            to_txs = self.wallet_map_df[self.wallet_map_df["to_wallet"] == addr]
            wallet_entry["out_volume"] = round(float(from_txs["amount_btc"].sum()), 6)
            wallet_entry["in_volume"] = round(float(to_txs["amount_btc"].sum()), 6)

            wallet_dict[addr] = wallet_entry

            if is_culprit:
                culprit_list.append(wallet_entry)

        self.scored_wallets = wallet_dict
        self.culprits = sorted(culprit_list, key=lambda x: x["threat_score"], reverse=True)

    def get_scored_subgraph(self, root_target: str, max_hops: int = 5) -> Dict[str, Any]:
        """Returns a scored sub-network graph starting from root_target."""
        if not self.is_loaded:
            self.load_dataset()

        # Find matching wallet/txId
        target_wallets = set()

        # Check if root_target is a tx_hash like "tx_123"
        if root_target.startswith("tx_"):
            tx_id = root_target.replace("tx_", "")
            matches = self.wallet_map_df[self.wallet_map_df["txId"].astype(str) == tx_id]
            if not matches.empty:
                target_wallets.update(matches["from_wallet"].values)
                target_wallets.update(matches["to_wallet"].values)
        else:
            # Direct wallet address
            target_wallets.add(root_target)

        if not target_wallets:
            # Fall back: use first available wallet
            if not self.wallet_map_df.empty:
                target_wallets.add(self.wallet_map_df.iloc[0]["from_wallet"])

        # Collect all wallets in the subgraph by BFS through transactions
        visited_wallets = set()
        current_wallets = target_wallets.copy()
        hops = 0

        while current_wallets and hops < max_hops:
            next_wallets = set()
            for w in current_wallets:
                visited_wallets.add(w)
                # Find transactions involving this wallet
                related = self.wallet_map_df[
                    (self.wallet_map_df["from_wallet"] == w) |
                    (self.wallet_map_df["to_wallet"] == w)
                ]
                for _, r in related.iterrows():
                    fw = str(r["from_wallet"])
                    tw = str(r["to_wallet"])
                    if fw not in visited_wallets:
                        next_wallets.add(fw)
                    if tw not in visited_wallets:
                        next_wallets.add(tw)
            visited_wallets.update(next_wallets)
            current_wallets = next_wallets
            hops += 1

            # Limit subgraph size for performance
            if len(visited_wallets) > 200:
                break

        if not visited_wallets:
            visited_wallets = set(self.wallet_map_df["from_wallet"].head(20).values)

        # Build subgraph nodes
        subgraph_nodes = []
        for w in visited_wallets:
            w_info = self.scored_wallets.get(w, {
                "address": w, "threat_score": 5, "role": "UNKNOWN", "is_culprit": False
            })

            node_type = "mule"
            if w_info.get("role") == "LEGITIMATE_USER":
                node_type = "victim"  # Use victim styling for legit
            elif "OFFRAMP" in w_info.get("role", ""):
                node_type = "exchange"
            elif "CONSOLIDATOR" in w_info.get("role", ""):
                node_type = "consolidator"

            subgraph_nodes.append({
                "id": w,
                "label": w[:12] + "..." if len(w) > 14 else w,
                "type": node_type,
                "riskScore": w_info.get("threat_score", 5),
                "role": w_info.get("role", "UNKNOWN"),
                "isCulprit": w_info.get("is_culprit", False),
                "pagerank": w_info.get("pagerank", 0.0)
            })

        # Build subgraph links from scored transactions
        subgraph_links = [
            tx for tx in self.scored_transactions
            if tx["from_address"] in visited_wallets and tx["to_address"] in visited_wallets
        ]

        # Limit links for performance
        subgraph_links = subgraph_links[:500]

        terminal_exchange = next(
            (n["id"] for n in subgraph_nodes if n["type"] == "exchange" or "OFFRAMP" in n.get("role", "")),
            None
        )

        return {
            "target": root_target,
            "terminalExchange": terminal_exchange,
            "nodes": subgraph_nodes,
            "links": subgraph_links,
            "culprits_detected": [c for c in self.culprits if c["address"] in visited_wallets],
            "total_nodes": len(subgraph_nodes),
            "total_links": len(subgraph_links)
        }

    def get_dataset_info(self) -> Dict[str, Any]:
        """Returns detailed Elliptic++ dataset statistics."""
        if not self.is_loaded:
            self.load_dataset()
        return self.dataset_info

# Global Singleton Instance
graph_model_engine = GraphFraudModel()
