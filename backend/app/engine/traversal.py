import time
import networkx as nx
from typing import List, Dict, Tuple, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.wallet import Wallet
from app.models.transaction import Transaction
from app.models.vasp import VASPRegistry
from app.engine.heuristics import (
    calculate_sweeper_score,
    calculate_gas_sponsor_score,
    calculate_fan_in_score,
    compute_node_threat_score
)
from app.core.config import settings

async def run_5hop_bfs_traversal(
    db: AsyncSession, 
    root_target: str
) -> Tuple[List[Dict], List[Dict], Optional[str], int, float]:
    start_time = time.perf_counter()

    # 1. Fetch transactions up to 5 hops
    g = nx.DiGraph()
    
    # Get all transactions from DB for graph build
    tx_query = await db.execute(select(Transaction))
    transactions = tx_query.scalars().all()

    gas_sponsor_counts: Dict[str, int] = {}
    for tx in transactions:
        g.add_edge(
            tx.from_address,
            tx.to_address,
            amount=tx.amount,
            tx_hash=tx.tx_hash,
            latency=tx.latency_seconds,
            gas_sponsor=tx.gas_sponsor
        )
        if tx.gas_sponsor:
            gas_sponsor_counts[tx.gas_sponsor] = gas_sponsor_counts.get(tx.gas_sponsor, 0) + 1

    # 2. Determine initial stolen value reference
    root_out_edges = list(g.out_edges(root_target, data=True)) if root_target in g else []
    initial_stolen_value = sum(edge[2].get('amount', 0.0) for edge in root_out_edges) or 10000.0
    prune_threshold = (settings.DUST_FILTER_PERCENTAGE / 100.0) * initial_stolen_value

    # 3. BFS Traversal up to 5 Hops with dynamic pruning (<3%)
    visited_nodes = set()
    pruned_branches_count = 0
    current_level = {root_target}
    hops = 0

    while current_level and hops < settings.MAX_HOPS:
        next_level = set()
        for node in current_level:
            visited_nodes.add(node)
            for _, successor, data in g.out_edges(node, data=True):
                edge_amt = data.get('amount', 0.0)
                if edge_amt < prune_threshold:
                    pruned_branches_count += 1
                    continue
                if successor not in visited_nodes:
                    next_level.add(successor)
        visited_nodes.update(next_level)
        current_level = next_level
        hops += 1

    # Include visited nodes in the final subgraph
    if not visited_nodes:
        visited_nodes.add(root_target)

    subgraph = g.subgraph(visited_nodes)

    # 4. Fetch VASP Registry to pinpoint terminal off-ramp
    vasp_query = await db.execute(select(VASPRegistry))
    vasps = {v.hot_wallet_address: v for v in vasp_query.scalars().all()}

    # Batch query wallet database records
    w_query = await db.execute(select(Wallet).where(Wallet.address.in_(list(visited_nodes))))
    wallets_map = {w.address: w for w in w_query.scalars().all()}

    # 5. Build Formatted Nodes and Links
    nodes_result = []
    terminal_exchange_name = None

    for node_id in subgraph.nodes():
        wallet_record = wallets_map.get(node_id)

        is_vasp = node_id in vasps
        vasp_obj = vasps.get(node_id)
        if is_vasp and vasp_obj:
            terminal_exchange_name = vasp_obj.exchange_name

        in_deg = subgraph.in_degree(node_id)
        out_deg = subgraph.out_degree(node_id)

        # Dynamic edge properties for heuristics
        out_edges = list(subgraph.out_edges(node_id, data=True))
        in_edges = list(subgraph.in_edges(node_id, data=True))

        total_in = sum(e[2].get('amount', 0.0) for e in in_edges) or 1.0
        total_out = sum(e[2].get('amount', 0.0) for e in out_edges)
        forwarded_ratio = min(1.0, total_out / total_in) if out_deg > 0 else 0.0
        min_latency = min((e[2].get('latency', 60) for e in out_edges), default=15)

        has_gas_sponsor = any(e[2].get('gas_sponsor') is not None for e in in_edges + out_edges)
        shared_count = max([gas_sponsor_counts.get(e[2].get('gas_sponsor'), 0) for e in in_edges + out_edges if e[2].get('gas_sponsor')], default=0)

        # Dynamic Heuristic calculation
        vasp_match = 100 if is_vasp else 10
        sweeper_val = calculate_sweeper_score(latency_seconds=min_latency, forwarded_ratio=forwarded_ratio) if out_deg > 0 else 5
        gas_val = calculate_gas_sponsor_score(has_external_sponsor=has_gas_sponsor, sponsor_shared_count=shared_count)
        fan_in_val = calculate_fan_in_score(in_deg, out_deg)
        
        calculated_risk = compute_node_threat_score(vasp_match, sweeper_val, gas_val, fan_in_val, is_vasp)
        if node_id == root_target:
            calculated_risk = 5  # Victim origin baseline

        node_type = "victim" if node_id == root_target else ("exchange" if is_vasp else "mule")

        balance_val = wallet_record.balance if wallet_record else 1000.0

        nodes_result.append({
            "id": node_id,
            "label": vasp_obj.exchange_name if is_vasp else ("Victim Wallet" if node_id == root_target else f"Hop Mule {node_id[-4:]}"),
            "type": node_type,
            "riskScore": calculated_risk,
            "balance": f"{balance_val:,.2f} USDT",
            "cluster": "Terminal Off-Ramp" if is_vasp else ("Source" if node_id == root_target else "Layering Mule"),
            "exchangeName": vasp_obj.exchange_name if is_vasp else None,
            "jurisdiction": vasp_obj.jurisdiction if is_vasp else None,
            "heuristics": {
                "vaspMatch": vasp_match,
                "sweeper": sweeper_val,
                "gasSponsor": gas_val,
                "fanIn": fan_in_val
            }
        })

    links_result = []
    for u, v, data in subgraph.edges(data=True):
        suspicious_score = 90 if v in vasps else 75
        links_result.append({
            "source": u,
            "target": v,
            "amount": f"{data.get('amount', 0.0):,.2f} USDT",
            "txHash": data.get('tx_hash', '0xabc...'),
            "suspiciousScore": suspicious_score,
            "latency": f"{data.get('latency', 20)}s"
        })

    traversal_time_ms = round((time.perf_counter() - start_time) * 1000, 2)
    return nodes_result, links_result, terminal_exchange_name, pruned_branches_count, traversal_time_ms