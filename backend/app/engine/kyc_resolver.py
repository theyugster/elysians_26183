import json
import os
import networkx as nx
from typing import Dict, List, Any, Optional

class KYCResolver:
    """
    KYC Intelligence & Real-World Culprit Resolution Engine.
    Resolves on-chain culprit wallets to real-world identities, national IDs,
    bank accounts, and physical addresses.
    Supports direct KYC match as well as downstream graph path-tracing for unhosted mules.
    """

    def __init__(self, kyc_path: Optional[str] = None):
        self.kyc_path = kyc_path or os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..", "..", "data", "kyc_records_elliptic.json")
        )
        self.records: Dict[str, Dict[str, Any]] = {}
        self.is_loaded = False
        self.load_records()

    def load_records(self, custom_path: Optional[str] = None) -> int:
        """Loads verified KYC records from JSON store."""
        path = custom_path or self.kyc_path
        if not os.path.exists(path):
            raise FileNotFoundError(f"KYC records file not found at: {path}")

        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        self.records = {item["wallet_address"].strip().lower(): item for item in data}
        self.is_loaded = True
        return len(self.records)

    def get_direct_kyc(self, wallet_address: str) -> Optional[Dict[str, Any]]:
        """Retrieves direct verified KYC profile for a wallet address if registered."""
        if not self.is_loaded:
            self.load_records()
        return self.records.get(wallet_address.strip().lower())

    def resolve_wallet_kyc(
        self,
        wallet_address: str,
        graph: Optional[nx.DiGraph] = None
    ) -> Dict[str, Any]:
        """
        Resolves KYC for any wallet.
        1. If directly known, returns full verified identity.
        2. If unhosted mule without direct KYC, traces downstream along transaction graph
           to find the terminal off-ramp or consolidation node where KYC is registered.
        """
        clean_addr = wallet_address.strip()
        direct = self.get_direct_kyc(clean_addr)

        if direct:
            return {
                "wallet_address": clean_addr,
                "resolution_status": "IDENTIFIED",
                "match_type": "DIRECT_KYC_MATCH",
                "identity": {
                    "entity_name": direct.get("entity_name"),
                    "primary_beneficiary": direct.get("primary_beneficiary"),
                    "national_id": direct.get("national_id"),
                    "tax_id": direct.get("tax_id"),
                    "jurisdiction": direct.get("jurisdiction"),
                    "physical_address": direct.get("physical_address"),
                    "registered_email": direct.get("registered_email"),
                    "registered_phone": direct.get("registered_phone"),
                    "associated_ips": direct.get("associated_ips", []),
                    "linked_bank_accounts": direct.get("linked_bank_accounts", [])
                },
                "kyc_tier": direct.get("kyc_status", "VERIFIED"),
                "risk_classification": direct.get("risk_classification", "FLAGGED_CULPRIT"),
                "legal_readiness": "READY_FOR_BNSS_SEC_94_REQUISITION",
                "downstream_trace": None
            }

        # Downstream graph traversal for unhosted private mules
        if graph and clean_addr in graph:
            visited = set()
            queue = [(clean_addr, 0, [clean_addr])]

            while queue:
                curr, depth, path = queue.pop(0)
                if depth > 4:
                    continue

                for _, succ in graph.out_edges(curr):
                    succ_clean = succ.strip()
                    if succ_clean in visited:
                        continue
                    visited.add(succ_clean)
                    direct_succ = self.get_direct_kyc(succ_clean)
                    if direct_succ:
                        # Found downstream KYC anchor!
                        return {
                            "wallet_address": clean_addr,
                            "resolution_status": "IDENTIFIED_VIA_OFFRAMP",
                            "match_type": "DOWNSTREAM_OFFRAMP_LINKAGE",
                            "traced_cashout_wallet": succ_clean,
                            "hops_to_cashout": depth + 1,
                            "flow_path": path + [succ_clean],
                            "identity": {
                                "entity_name": f"{direct_succ.get('entity_name')} (Cash-Out Destination for {clean_addr})",
                                "primary_beneficiary": direct_succ.get("primary_beneficiary"),
                                "national_id": direct_succ.get("national_id"),
                                "tax_id": direct_succ.get("tax_id"),
                                "jurisdiction": direct_succ.get("jurisdiction"),
                                "physical_address": direct_succ.get("physical_address"),
                                "registered_email": direct_succ.get("registered_email"),
                                "registered_phone": direct_succ.get("registered_phone"),
                                "associated_ips": direct_succ.get("associated_ips", []),
                                "linked_bank_accounts": direct_succ.get("linked_bank_accounts", [])
                            },
                            "kyc_tier": direct_succ.get("kyc_status", "OFFRAMP_IDENTIFIED"),
                            "risk_classification": "UNHOSTED_MULE_LINKED_TO_CULPRIT",
                            "legal_readiness": "READY_FOR_BNSS_SEC_94_REQUISITION",
                            "downstream_trace": {
                                "terminal_wallet": succ_clean,
                                "hops": depth + 1,
                                "path": path + [succ_clean]
                            }
                        }
                    queue.append((succ_clean, depth + 1, path + [succ_clean]))

        # Unidentified unhosted wallet
        return {
            "wallet_address": clean_addr,
            "resolution_status": "UNHOSTED_UNVERIFIED",
            "match_type": "NO_KYC_RECORD",
            "identity": {
                "entity_name": "Unhosted Private Mule / Autonomous Smart Wallet",
                "primary_beneficiary": "Unknown Actor (Pending Intermediary VASP Subpoena)",
                "national_id": "N/A (Non-Custodial)",
                "tax_id": "N/A",
                "jurisdiction": "Decentralized (On-Chain)",
                "physical_address": "N/A",
                "registered_email": "N/A",
                "registered_phone": "N/A",
                "associated_ips": [],
                "linked_bank_accounts": []
            },
            "kyc_tier": "UNHOSTED",
            "risk_classification": "INTERMEDIARY_MULE",
            "legal_readiness": "SUBPOENA_REQUIRED",
            "downstream_trace": None
        }

    def resolve_all_culprits(
        self,
        culprits: List[Dict[str, Any]],
        graph: Optional[nx.DiGraph] = None
    ) -> List[Dict[str, Any]]:
        """Resolves real-world identities and KYC dossiers for a list of flagged culprits."""
        resolved = []
        for c in culprits:
            addr = c.get("address") or c.get("id") or ""
            if not addr:
                continue
            kyc_info = self.resolve_wallet_kyc(addr, graph=graph)
            combined = {
                **c,
                "kyc": kyc_info
            }
            resolved.append(combined)
        return resolved

# Global Singleton Instance
kyc_resolver_engine = KYCResolver()
