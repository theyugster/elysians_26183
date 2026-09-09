import React, { useState } from 'react';
import {
  ShieldAlert,
  UserCheck,
  Building2,
  CreditCard,
  MapPin,
  Mail,
  Phone,
  Globe2,
  Copy,
  Check,
  FileText,
  Search,
  ArrowRight,
  Fingerprint,
  AlertTriangle,
  Eye,
} from 'lucide-react';

export default function CulpritKYCPanel({
  culprits = [],
  onSelectCulprit,
  onGenerateDossier,
  selectedWallet = null
}) {
  const [copiedKey, setCopiedKey] = useState(null);
  const [filterRole, setFilterRole] = useState('ALL');
  const [searchTerm, setSearchTerm] = useState('');

  const copyToClipboard = (text, key) => {
    navigator.clipboard.writeText(text);
    setCopiedKey(key);
    setTimeout(() => setCopiedKey(null), 2000);
  };

  const filteredCulprits = culprits.filter(c => {
    if (filterRole !== 'ALL' && c.role !== filterRole) return false;
    if (searchTerm) {
      const q = searchTerm.toLowerCase();
      const addr = (c.address || '').toLowerCase();
      const name = (c.kyc?.identity?.primary_beneficiary || '').toLowerCase();
      const natId = (c.kyc?.identity?.national_id || '').toLowerCase();
      return addr.includes(q) || name.includes(q) || natId.includes(q);
    }
    return true;
  });

  return (
    <div className="culprit-kyc-panel" style={{
      backgroundColor: '#ffffff',
      border: '1px solid var(--border-subtle)',
      borderRadius: 'var(--radius-lg)',
      boxShadow: 'var(--shadow-sm)',
      padding: '24px',
      marginTop: '24px'
    }}>
      {/* Panel Header */}
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'flex-start',
        flexWrap: 'wrap',
        gap: '16px',
        borderBottom: '1px solid var(--border-subtle)',
        paddingBottom: '18px',
        marginBottom: '20px'
      }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <div style={{
              width: 34,
              height: 34,
              borderRadius: '8px',
              backgroundColor: '#fee2e2',
              color: 'var(--danger)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center'
            }}>
              <Fingerprint size={18} />
            </div>
            <div>
              <h2 style={{ fontSize: '1.08rem', fontWeight: 800, color: 'var(--text-primary)', margin: 0 }}>
                Flagged Culprits &amp; KYC Unmasking Intelligence
              </h2>
              <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>
                Graph ML Model Detection &bull; Real-World Identity Resolution &bull; Downstream Off-Ramp Tracing
              </span>
            </div>
          </div>
        </div>

        {/* Filter Pills & Search */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px', flexWrap: 'wrap' }}>
          <div style={{ position: 'relative', minWidth: '220px' }}>
            <Search size={14} style={{ position: 'absolute', left: 10, top: 10, color: 'var(--text-light)' }} />
            <input
              type="text"
              placeholder="Search name, ID, or wallet..."
              value={searchTerm}
              onChange={e => setSearchTerm(e.target.value)}
              style={{
                width: '100%',
                padding: '7px 12px 7px 30px',
                fontSize: '0.78rem',
                border: '1px solid var(--border-subtle)',
                borderRadius: 'var(--radius-md)',
                backgroundColor: 'var(--bg-main)',
                outline: 'none'
              }}
            />
          </div>

          <div style={{ display: 'flex', gap: '6px' }}>
            {['ALL', 'CULPRIT_OFFRAMP', 'CULPRIT_CONSOLIDATOR', 'CULPRIT_MULE', 'SYBIL_GAS_MASTER'].map(role => (
              <button
                key={role}
                onClick={() => setFilterRole(role)}
                style={{
                  padding: '6px 10px',
                  fontSize: '0.72rem',
                  fontWeight: 600,
                  borderRadius: 'var(--radius-sm)',
                  border: '1px solid',
                  borderColor: filterRole === role ? 'var(--primary)' : 'var(--border-subtle)',
                  backgroundColor: filterRole === role ? 'var(--primary-subtle)' : '#ffffff',
                  color: filterRole === role ? 'var(--primary)' : 'var(--text-secondary)',
                  cursor: 'pointer'
                }}
              >
                {role === 'ALL' ? 'All Culprits' : role.replace('CULPRIT_', '').replace('_', ' ')}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Culprit Cards Grid */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fill, minmax(360px, 1fr))',
        gap: '16px'
      }}>
        {filteredCulprits.map((culprit, idx) => {
          const kyc = culprit.kyc || {};
          const identity = kyc.identity || {};
          const isDirect = kyc.match_type === 'DIRECT_KYC_MATCH';
          const isOfframpTraced = kyc.match_type === 'DOWNSTREAM_OFFRAMP_LINKAGE';
          const hasIdent = identity.primary_beneficiary && !identity.primary_beneficiary.includes('Unknown');

          // SIH 2026 — Unknown VASP Escalation Detection
          // If exchange behavior detected but identity not in VASP registry,
          // show "Unidentified Centralized Exchange" and change action button.
          const isUnknownVASP = (
            culprit.role === 'CULPRIT_OFFRAMP' &&
            (!identity.entity_name ||
             identity.entity_name.includes('Unknown') ||
             identity.entity_name.includes('Unidentified') ||
             identity.entity_name.includes('Unhosted'))
          ) || (identity.entity_name && identity.entity_name.includes('Unidentified'));

          return (
            <div
              key={culprit.address || idx}
              style={{
                border: '1px solid var(--border-subtle)',
                borderRadius: 'var(--radius-md)',
                backgroundColor: selectedWallet === culprit.address ? '#f8fafc' : '#ffffff',
                boxShadow: selectedWallet === culprit.address ? '0 0 0 2px var(--primary)' : 'none',
                padding: '18px',
                display: 'flex',
                flexDirection: 'column',
                gap: '14px',
                transition: 'all 0.15s ease'
              }}
            >
              {/* Card Header */}
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: '8px' }}>
                <div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
                    <span style={{
                      padding: '3px 7px',
                      fontSize: '0.68rem',
                      fontWeight: 800,
                      borderRadius: '4px',
                      backgroundColor: '#fee2e2',
                      color: '#b91c1c'
                    }}>
                      {culprit.role}
                    </span>

                    <span style={{
                      padding: '3px 7px',
                      fontSize: '0.68rem',
                      fontWeight: 700,
                      borderRadius: '4px',
                      backgroundColor: isDirect ? '#dcfce7' : (isOfframpTraced ? '#f3e8ff' : '#f1f5f9'),
                      color: isDirect ? '#15803d' : (isOfframpTraced ? '#7e22ce' : '#64748b')
                    }}>
                      {isDirect ? 'Direct KYC Match' : (isOfframpTraced ? 'Traced via Off-Ramp' : 'Unhosted Mule')}
                    </span>
                  </div>

                  <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                    <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.84rem', fontWeight: 700, color: 'var(--text-primary)' }}>
                      {culprit.address}
                    </span>
                    <button
                      onClick={() => copyToClipboard(culprit.address, `addr-${idx}`)}
                      style={{ background: 'none', border: 'none', color: 'var(--text-light)', cursor: 'pointer' }}
                      title="Copy Address"
                    >
                      {copiedKey === `addr-${idx}` ? <Check size={13} color="var(--success)" /> : <Copy size={13} />}
                    </button>
                  </div>
                </div>

                {/* Threat Score Pill */}
                <div style={{
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'flex-end'
                }}>
                  <div style={{
                    padding: '4px 10px',
                    borderRadius: '20px',
                    backgroundColor: culprit.threat_score >= 80 ? '#fee2e2' : '#fef3c7',
                    color: culprit.threat_score >= 80 ? '#b91c1c' : '#b45309',
                    fontSize: '0.82rem',
                    fontWeight: 800
                  }}>
                    {culprit.threat_score} / 100
                  </div>
                  <span style={{ fontSize: '0.66rem', color: 'var(--text-muted)', marginTop: 2 }}>Model Threat</span>
                </div>
              </div>

              {/* SIH 2026 — Unknown VASP Escalation Banner */}
              {isUnknownVASP && (
                <div style={{
                  padding: '12px',
                  backgroundColor: '#faf5ff',
                  border: '2px solid #a855f7',
                  borderRadius: 'var(--radius-sm)',
                  marginBottom: '10px',
                }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '6px' }}>
                    <Eye size={15} color="#7e22ce" />
                    <span style={{ fontSize: '0.78rem', fontWeight: 800, color: '#7e22ce', textTransform: 'uppercase' }}>
                      Unidentified Centralized Exchange
                    </span>
                  </div>
                  <p style={{ fontSize: '0.72rem', color: '#6b21a8', margin: 0, lineHeight: 1.5 }}>
                    Exchange behavioral patterns confirmed but identity not found in VASP registry.
                    Generate <strong>FIU-IND Escalation Request</strong> for cross-referencing.
                  </p>
                </div>
              )}

              {/* Resolved Real-World Identity */}
              <div style={{
                backgroundColor: 'var(--bg-main)',
                border: '1px solid var(--border-subtle)',
                borderRadius: 'var(--radius-sm)',
                padding: '12px'
              }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '8px' }}>
                  <UserCheck size={14} color={hasIdent ? 'var(--success)' : 'var(--text-muted)'} />
                  <span style={{ fontSize: '0.74rem', fontWeight: 800, textTransform: 'uppercase', letterSpacing: '0.04em', color: 'var(--text-secondary)' }}>
                    Resolved Real-World Identity
                  </span>
                </div>

                <div style={{ fontSize: '0.9rem', fontWeight: 700, color: isUnknownVASP ? '#7e22ce' : 'var(--text-primary)', marginBottom: '4px' }}>
                  {isUnknownVASP ? 'Unidentified Centralized Exchange' : (identity.primary_beneficiary || 'Pending Intermediary Subpoena')}
                </div>

                {identity.entity_name && identity.entity_name !== identity.primary_beneficiary && (
                  <div style={{ fontSize: '0.76rem', color: 'var(--text-muted)', marginBottom: '8px' }}>
                    Entity: {identity.entity_name}
                  </div>
                )}

                {/* Key Credentials Table */}
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px', marginTop: '8px', fontSize: '0.74rem' }}>
                  <div>
                    <span style={{ color: 'var(--text-muted)', display: 'block' }}>National ID / Passport</span>
                    <span style={{ fontWeight: 600, color: 'var(--text-primary)', fontFamily: 'var(--font-mono)' }}>
                      {identity.national_id || 'N/A'}
                    </span>
                  </div>

                  <div>
                    <span style={{ color: 'var(--text-muted)', display: 'block' }}>Tax Identifier / PAN</span>
                    <span style={{ fontWeight: 600, color: 'var(--text-primary)', fontFamily: 'var(--font-mono)' }}>
                      {identity.tax_id || 'N/A'}
                    </span>
                  </div>
                </div>

                {/* Physical Location */}
                {identity.physical_address && identity.physical_address !== 'N/A' && (
                  <div style={{ display: 'flex', alignItems: 'flex-start', gap: '6px', marginTop: '10px', fontSize: '0.74rem', color: 'var(--text-secondary)' }}>
                    <MapPin size={13} style={{ flexShrink: 0, marginTop: 2, color: 'var(--primary)' }} />
                    <span>{identity.physical_address}</span>
                  </div>
                )}

                {/* Bank Account */}
                {identity.linked_bank_accounts && identity.linked_bank_accounts.length > 0 && (
                  <div style={{
                    marginTop: '10px',
                    padding: '8px 10px',
                    backgroundColor: '#ffffff',
                    border: '1px solid var(--border-subtle)',
                    borderRadius: '4px',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between'
                  }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                      <CreditCard size={13} color="var(--primary)" />
                      <span style={{ fontSize: '0.72rem', fontWeight: 600, color: 'var(--text-primary)' }}>
                        {identity.linked_bank_accounts[0].bank_name} &bull; {identity.linked_bank_accounts[0].account_number}
                      </span>
                    </div>
                    <span style={{ fontSize: '0.68rem', fontWeight: 700, color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
                      {identity.linked_bank_accounts[0].ifsc || identity.linked_bank_accounts[0].swift_bic}
                    </span>
                  </div>
                )}

                {/* Downstream Trace Indicator */}
                {isOfframpTraced && kyc.traced_cashout_wallet && (
                  <div style={{
                    marginTop: '8px',
                    padding: '6px 8px',
                    backgroundColor: '#faf5ff',
                    border: '1px solid #e9d5ff',
                    borderRadius: '4px',
                    fontSize: '0.72rem',
                    color: '#6b21a8',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '4px'
                  }}>
                    <ArrowRight size={12} />
                    <span>Traced downstream ({kyc.hops_to_cashout} hop) to terminal account: <strong>{kyc.traced_cashout_wallet}</strong></span>
                  </div>
                )}
              </div>

              {/* Action Buttons */}
              <div style={{ display: 'flex', gap: '8px', marginTop: 'auto' }}>
                <button
                  onClick={() => onSelectCulprit && onSelectCulprit(culprit.address)}
                  style={{
                    flex: 1,
                    padding: '7px 12px',
                    fontSize: '0.76rem',
                    fontWeight: 600,
                    borderRadius: 'var(--radius-sm)',
                    border: '1px solid var(--border-subtle)',
                    backgroundColor: '#ffffff',
                    color: 'var(--text-primary)',
                    cursor: 'pointer'
                  }}
                >
                  Locate on Graph
                </button>

                <button
                  onClick={() => onGenerateDossier && onGenerateDossier(culprit.address, identity.entity_name || culprit.address)}
                  style={{
                    flex: 1,
                    padding: '7px 12px',
                    fontSize: '0.76rem',
                    fontWeight: 700,
                    borderRadius: 'var(--radius-sm)',
                    border: 'none',
                    backgroundColor: isUnknownVASP ? '#7e22ce' : 'var(--primary)',
                    color: '#ffffff',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    gap: '6px',
                    cursor: 'pointer'
                  }}
                >
                  {isUnknownVASP ? <AlertTriangle size={13} /> : <FileText size={13} />}
                  {isUnknownVASP ? 'Export FIU-IND Escalation Request' : 'Issue BNSS-94'}
                </button>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
