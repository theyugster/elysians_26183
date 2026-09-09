"""
Multi-Signal Heuristic Attribution Matrix (Slide 3):
1. Known VASP Registry
2. Sweeper Engine
3. Gas Sponsor Profiling
4. Fan-In Topology
"""

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