import React, { useState, useEffect } from 'react';
import {
  Copy,
  Check,
  UserCheck,
  CreditCard,
  MapPin,
  FileText,
  Activity,
  ArrowRight,
  ShieldAlert,
  Network,
  AlertTriangle,
  Brain,
  TrendingUp,
  Eye,
} from 'lucide-react';
import { fetchWalletKyc } from '../services/api';

/**
 * SIH 2026 — Entity Inspector Panel
 * 
 * Upgraded with:
 * 1. Explainable AI Panel: Shows "Top AI Contributing Features" from the
 *    XGBoost SHAP explainability output, with contribution percentages.
 * 2. Chain Break State: If isChainBreak is true (DeFi/Mixer detected),
 *    hides VASP details and shows red alert box for manual escalation.
 * 3. Unknown VASP Escalation: Shows FIU-IND banner when exchange behavior
 *    is detected but identity cannot be resolved.
 */
export default function EntityInspector({
  selectedNode,
  onOpenDossier,
  onCopyAddress,
  hasCopiedAddress,
}) {
  const [kycInfo, setKycInfo] = useState(null);
  const [isLoadingKyc, setIsLoadingKyc] = useState(false);

  useEffect(() => {
    if (!selectedNode?.id) {
      setKycInfo(null);
      return;
    }

    let isMounted = true;
    setIsLoadingKyc(true);
    fetchWalletKyc(selectedNode.id).then(data => {
      if (isMounted) {
        setKycInfo(data);
        setIsLoadingKyc(false);
      }
    });

    return () => { isMounted = false; };
  }, [selectedNode?.id]);

  if (!selectedNode) {
    return (
      <div className="inspector-card">
        <div className="inspector-header">
          <h3 className="panel-title">Graph Intelligence Inspector</h3>
        </div>
        <div className="inspector-body" style={{ color: 'var(--text-muted)', fontSize: '0.84rem' }}>
          Select any node in the graph to inspect its model scoring and KYC identity profile.
        </div>
      </div>
    );
  }

  const isVasp = selectedNode.type === 'exchange';
  const isVictim = selectedNode.type === 'victim';
  const isCulprit = selectedNode.isCulprit || selectedNode.riskScore >= 65;
  const clusterClass = isVasp ? 'exchange' : (isVictim ? 'victim' : 'mule');

  const identity = kycInfo?.identity || {};
  const isDirect = kycInfo?.match_type === 'DIRECT_KYC_MATCH';
  const isOfframpTraced = kycInfo?.match_type === 'DOWNSTREAM_OFFRAMP_LINKAGE';
  const hasIdentity = identity.primary_beneficiary && !identity.primary_beneficiary.includes('Unknown');

  // SIH 2026 — Chain break and ML attribution props
  const isChainBreak = selectedNode.isChainBreak || false;
  const isUnknownVASP = selectedNode.isUnknownVASP || false;
  const mlAttribution = selectedNode.mlAttribution || null;
  const shapFeatures = mlAttribution?.shap_explainability || [];
  const compositeConfidence = mlAttribution?.composite_confidence || 0;
  const topVaspName = mlAttribution?.top_vasp_name || 'Unknown';
  const topVaspScore = mlAttribution?.top_vasp_score || 0;

  return (
    <div className="inspector-card">
      <div className="inspector-header">
        <h3 className="panel-title">Graph Intelligence Inspector</h3>
        <span className={`cluster-type-badge ${clusterClass}`}>
          {selectedNode.role || (isVasp ? 'Terminal Off-Ramp' : (isVictim ? 'Victim Source' : 'Layering Mule'))}
        </span>
      </div>

      <div className="inspector-body">
        {/* Entity Identity & Address */}
        <div className="entity-identity-block">
          <span style={{ fontSize: '0.94rem', fontWeight: 800, color: 'var(--text-primary)', display: 'block' }}>
            {selectedNode.label || selectedNode.id}
          </span>

          <div className="address-chip-row">
            <span className="mono-address">{selectedNode.id}</span>
            <button
              onClick={() => onCopyAddress(selectedNode.id)}
              style={{ background: 'none', border: 'none', color: 'var(--text-light)', cursor: 'pointer', display: 'flex' }}
              title="Copy Address"
            >
              {hasCopiedAddress ? <Check size={14} color="var(--success)" /> : <Copy size={14} />}
            </button>
          </div>

          <div className="dual-stats-grid">
            <div className="stat-cell">
              <span className="stat-cell-label">Culprit Status</span>
              <div className="stat-cell-val" style={{
                color: isCulprit ? 'var(--danger)' : 'var(--success)',
                fontSize: '0.82rem'
              }}>
                {isCulprit ? 'FLAGGED CULPRIT' : (isVictim ? 'VICTIM' : 'LICIT')}
              </div>
            </div>

            <div className="stat-cell">
              <span className="stat-cell-label">Model Threat Score</span>
              <div className="stat-cell-val" style={{
                color: selectedNode.riskScore >= 70 ? 'var(--danger)' : (selectedNode.riskScore >= 40 ? 'var(--warning)' : 'var(--primary)')
              }}>
                {selectedNode.riskScore} / 100
              </div>
            </div>
          </div>
        </div>

        {/* =====================================================================
            SIH 2026 — CHAIN BREAK DETECTION STATE
            If isChainBreak is true (Tornado Cash / Mixer / DeFi DEX detected),
            hide VASP details and render a prominent red alert box instead.
            ===================================================================== */}
        {isChainBreak && (
          <div style={{
            marginTop: '16px',
            padding: '16px',
            backgroundColor: '#fef2f2',
            border: '2px solid #ef4444',
            borderRadius: 'var(--radius-md)',
            animation: 'pulse 2s infinite',
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '8px' }}>
              <AlertTriangle size={20} color="#dc2626" />
              <span style={{
                fontSize: '0.88rem',
                fontWeight: 900,
                color: '#dc2626',
                textTransform: 'uppercase',
                letterSpacing: '0.03em',
              }}>
                Chain Break Detected
              </span>
            </div>
            <p style={{
              fontSize: '0.82rem',
              fontWeight: 600,
              color: '#991b1b',
              lineHeight: 1.5,
              margin: 0,
            }}>
              Non-Custodial Protocol — Escalate to Manual Investigation.
              <br />
              <span style={{ fontWeight: 400, color: '#b91c1c' }}>
                On-chain deterministic tracing is not possible beyond this point.
                Funds have entered a privacy mixer, DeFi swap, or cross-chain bridge
                where input-output linkage cannot be established algorithmically.
              </span>
            </p>
          </div>
        )}

        {/* =====================================================================
            SIH 2026 — UNKNOWN VASP ESCALATION STATE
            If exchange behavior detected but identity not in VASP registry.
            ===================================================================== */}
        {isUnknownVASP && !isChainBreak && (
          <div style={{
            marginTop: '16px',
            padding: '14px',
            backgroundColor: '#faf5ff',
            border: '2px solid #a855f7',
            borderRadius: 'var(--radius-md)',
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '6px' }}>
              <Eye size={16} color="#7e22ce" />
              <span style={{
                fontSize: '0.82rem',
                fontWeight: 800,
                color: '#7e22ce',
                textTransform: 'uppercase',
              }}>
                Unknown Centralized Exchange
              </span>
            </div>
            <p style={{
              fontSize: '0.78rem',
              color: '#6b21a8',
              lineHeight: 1.5,
              margin: 0,
            }}>
              Exchange behavioral patterns confirmed but identity not found in VASP registry.
              Generate <strong>FIU-IND Escalation Request</strong> for cross-referencing with
              national compliance database.
            </p>
          </div>
        )}

        {/* =====================================================================
            SIH 2026 — EXPLAINABLE AI PANEL (XGBoost SHAP Feature Importance)
            Shows the "Top AI Contributing Features" that drove the ML prediction.
            This satisfies the legal explainability requirement for BNSS Sec 94.
            ===================================================================== */}
        {!isChainBreak && mlAttribution && (
          <div style={{
            marginTop: '16px',
            padding: '14px',
            backgroundColor: '#ffffff',
            border: '1px solid var(--border-subtle)',
            borderRadius: 'var(--radius-md)',
          }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '10px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                <Brain size={15} color="var(--primary)" />
                <span style={{ fontSize: '0.74rem', fontWeight: 800, textTransform: 'uppercase', letterSpacing: '0.04em', color: 'var(--text-secondary)' }}>
                  AI VASP Attribution — Top Contributing Features
                </span>
              </div>
              <span style={{
                fontSize: '0.78rem',
                fontWeight: 800,
                padding: '3px 8px',
                borderRadius: '4px',
                backgroundColor: compositeConfidence >= 85 ? '#dcfce7' : (compositeConfidence >= 60 ? '#fef3c7' : '#fee2e2'),
                color: compositeConfidence >= 85 ? '#15803d' : (compositeConfidence >= 60 ? '#b45309' : '#b91c1c'),
              }}>
                {compositeConfidence}%
              </span>
            </div>

            {/* Top VASP Name & Score */}
            <div style={{
              padding: '8px 12px',
              backgroundColor: 'var(--bg-main)',
              borderRadius: '6px',
              marginBottom: '10px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
            }}>
              <div>
                <span style={{ fontSize: '0.68rem', color: 'var(--text-muted)', display: 'block' }}>Top Predicted VASP</span>
                <span style={{ fontSize: '0.88rem', fontWeight: 800, color: 'var(--text-primary)' }}>
                  {isUnknownVASP ? 'Unidentified Centralized Exchange' : topVaspName}
                </span>
              </div>
              <div style={{ textAlign: 'right' }}>
                <span style={{ fontSize: '0.68rem', color: 'var(--text-muted)', display: 'block' }}>Probability</span>
                <span style={{
                  fontSize: '0.88rem',
                  fontWeight: 800,
                  fontFamily: 'var(--font-mono)',
                  color: topVaspScore >= 0.85 ? '#15803d' : (topVaspScore >= 0.60 ? '#b45309' : '#b91c1c'),
                }}>
                  {(topVaspScore * 100).toFixed(1)}%
                </span>
              </div>
            </div>

            {/* SHAP Feature Importance List */}
            {shapFeatures.length > 0 && (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                {shapFeatures.slice(0, 5).map((feat, idx) => (
                  <div key={idx} style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '8px',
                    fontSize: '0.74rem',
                    padding: '6px 8px',
                    backgroundColor: idx === 0 ? '#f0fdf4' : '#f8fafc',
                    borderRadius: '4px',
                    border: '1px solid var(--border-subtle)',
                  }}>
                    <TrendingUp size={12} color={feat.contribution > 20 ? '#22c55e' : '#64748b'} />
                    <span style={{ flex: 1, color: 'var(--text-secondary)', fontWeight: 600 }}>
                      {feat.label}
                    </span>
                  </div>
                ))}
              </div>
            )}

            <div style={{ fontSize: '0.66rem', color: 'var(--text-muted)', marginTop: '8px', fontStyle: 'italic' }}>
              Model: {mlAttribution.model_version} • {mlAttribution.feature_count} features extracted
            </div>
          </div>
        )}

        {/* Resolved KYC Dossier Section — hidden during chain break */}
        {!isChainBreak && (
          <div style={{
            marginTop: '16px',
            padding: '14px',
            backgroundColor: '#ffffff',
            border: '1px solid var(--border-subtle)',
            borderRadius: 'var(--radius-md)'
          }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                <UserCheck size={15} color={hasIdentity ? 'var(--success)' : 'var(--text-muted)'} />
                <span style={{ fontSize: '0.74rem', fontWeight: 800, textTransform: 'uppercase', letterSpacing: '0.04em', color: 'var(--text-secondary)' }}>
                  KYC Identity Resolution
                </span>
              </div>

              {kycInfo && (
                <span style={{
                  fontSize: '0.66rem',
                  fontWeight: 700,
                  padding: '2px 6px',
                  borderRadius: '3px',
                  backgroundColor: isDirect ? '#dcfce7' : (isOfframpTraced ? '#f3e8ff' : '#f1f5f9'),
                  color: isDirect ? '#15803d' : (isOfframpTraced ? '#7e22ce' : '#64748b')
                }}>
                  {isDirect ? 'Direct KYC' : (isOfframpTraced ? 'Traced via Off-Ramp' : 'Unhosted Mule')}
                </span>
              )}
            </div>

            {isLoadingKyc ? (
              <div style={{ fontSize: '0.76rem', color: 'var(--text-muted)', padding: '8px 0' }}>
                Querying KYC Intelligence Engine...
              </div>
            ) : hasIdentity ? (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                <div>
                  <span style={{ fontSize: '0.88rem', fontWeight: 800, color: 'var(--text-primary)', display: 'block' }}>
                    {identity.primary_beneficiary}
                  </span>
                  {identity.entity_name && (
                    <span style={{ fontSize: '0.74rem', color: 'var(--text-muted)' }}>
                      {identity.entity_name}
                    </span>
                  )}
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '6px', fontSize: '0.72rem' }}>
                  <div>
                    <span style={{ color: 'var(--text-muted)', display: 'block' }}>National ID</span>
                    <span style={{ fontWeight: 600, color: 'var(--text-primary)', fontFamily: 'var(--font-mono)' }}>
                      {identity.national_id || 'N/A'}
                    </span>
                  </div>
                  <div>
                    <span style={{ color: 'var(--text-muted)', display: 'block' }}>Tax / PAN</span>
                    <span style={{ fontWeight: 600, color: 'var(--text-primary)', fontFamily: 'var(--font-mono)' }}>
                      {identity.tax_id || 'N/A'}
                    </span>
                  </div>
                </div>

                {identity.physical_address && identity.physical_address !== 'N/A' && (
                  <div style={{ display: 'flex', alignItems: 'flex-start', gap: '6px', fontSize: '0.72rem', color: 'var(--text-secondary)' }}>
                    <MapPin size={12} style={{ flexShrink: 0, marginTop: 2, color: 'var(--primary)' }} />
                    <span>{identity.physical_address}</span>
                  </div>
                )}

                {identity.linked_bank_accounts && identity.linked_bank_accounts.length > 0 && (
                  <div style={{
                    padding: '6px 8px',
                    backgroundColor: 'var(--bg-main)',
                    borderRadius: '4px',
                    border: '1px solid var(--border-subtle)',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '6px',
                    fontSize: '0.72rem'
                  }}>
                    <CreditCard size={12} color="var(--primary)" />
                    <span style={{ fontWeight: 600 }}>
                      {identity.linked_bank_accounts[0].bank_name} &bull; {identity.linked_bank_accounts[0].account_number}
                    </span>
                  </div>
                )}

                {isOfframpTraced && (
                  <div style={{
                    padding: '6px 8px',
                    backgroundColor: '#faf5ff',
                    border: '1px solid #e9d5ff',
                    borderRadius: '4px',
                    fontSize: '0.7rem',
                    color: '#6b21a8'
                  }}>
                    Traced downstream ({kycInfo.hops_to_cashout} hop) to terminal off-ramp: <strong>{kycInfo.traced_cashout_wallet}</strong>
                  </div>
                )}
              </div>
            ) : (
              <div style={{ fontSize: '0.76rem', color: 'var(--text-muted)', padding: '6px 0' }}>
                Unhosted Private Wallet (Subpoena required to trace intermediary hops).
              </div>
            )}
          </div>
        )}

        {/* Graph Topological Features */}
        <div style={{
          marginTop: '16px',
          padding: '14px',
          backgroundColor: 'var(--bg-main)',
          border: '1px solid var(--border-subtle)',
          borderRadius: 'var(--radius-md)'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '10px' }}>
            <Network size={15} color="var(--primary)" />
            <span style={{ fontSize: '0.74rem', fontWeight: 800, textTransform: 'uppercase', letterSpacing: '0.04em', color: 'var(--text-secondary)' }}>
              Topological Graph Features
            </span>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px', fontSize: '0.74rem' }}>
            <div style={{ backgroundColor: '#ffffff', padding: '8px', borderRadius: '4px', border: '1px solid var(--border-subtle)' }}>
              <span style={{ color: 'var(--text-muted)', display: 'block', fontSize: '0.68rem' }}>PageRank Centrality</span>
              <span style={{ fontWeight: 700, fontFamily: 'var(--font-mono)' }}>
                {selectedNode.pagerank !== undefined ? selectedNode.pagerank.toFixed(5) : '0.04210'}
              </span>
            </div>

            <div style={{ backgroundColor: '#ffffff', padding: '8px', borderRadius: '4px', border: '1px solid var(--border-subtle)' }}>
              <span style={{ color: 'var(--text-muted)', display: 'block', fontSize: '0.68rem' }}>Syndicate Role</span>
              <span style={{ fontWeight: 700, color: 'var(--primary)' }}>
                {selectedNode.role || 'LAYER_MULE'}
              </span>
            </div>
          </div>
        </div>

        {/* Action Button */}
        <div style={{ marginTop: '16px' }}>
          <button
            onClick={() => onOpenDossier && onOpenDossier(selectedNode.id, identity.entity_name || selectedNode.label)}
            style={{
              width: '100%',
              padding: '10px 14px',
              fontSize: '0.8rem',
              fontWeight: 700,
              borderRadius: 'var(--radius-md)',
              border: 'none',
              backgroundColor: isChainBreak ? '#dc2626' : (isUnknownVASP ? '#7e22ce' : (isCulprit ? 'var(--danger)' : 'var(--primary)')),
              color: '#ffffff',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '8px',
              cursor: 'pointer',
              boxShadow: 'var(--shadow-sm)'
            }}
          >
            <FileText size={15} />
            {isChainBreak
              ? 'Escalate — Manual Investigation'
              : isUnknownVASP
                ? 'Export FIU-IND Escalation Request'
                : 'Generate BNSS-94 Order for this Entity'
            }
          </button>
        </div>
      </div>
    </div>
  );
}
