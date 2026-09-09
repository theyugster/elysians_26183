import React, { useState } from 'react';
import {
  Activity,
  ArrowRight,
  ShieldAlert,
  ShieldCheck,
  AlertTriangle,
  Clock,
  Zap,
  Filter,
  Copy,
  Check
} from 'lucide-react';

export default function ScoredTransactionsFeed({ transactions = [] }) {
  const [copiedKey, setCopiedKey] = useState(null);
  const [filterClass, setFilterClass] = useState('ALL');
  const [minScore, setMinScore] = useState(0);

  const copyToClipboard = (text, key) => {
    navigator.clipboard.writeText(text);
    setCopiedKey(key);
    setTimeout(() => setCopiedKey(null), 2000);
  };

  const filteredTxs = transactions.filter(tx => {
    if (filterClass !== 'ALL' && tx.classification !== filterClass) return false;
    if (tx.fraud_score < minScore) return false;
    return true;
  });

  const fraudCount = transactions.filter(t => t.classification === 'FRAUDULENT').length;
  const suspCount = transactions.filter(t => t.classification === 'SUSPICIOUS').length;
  const licitCount = transactions.filter(t => t.classification === 'LEGITIMATE').length;

  return (
    <div className="scored-transactions-feed" style={{
      backgroundColor: '#ffffff',
      border: '1px solid var(--border-subtle)',
      borderRadius: 'var(--radius-lg)',
      boxShadow: 'var(--shadow-sm)',
      padding: '24px',
      marginTop: '24px'
    }}>
      {/* Table Header */}
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'flex-start',
        flexWrap: 'wrap',
        gap: '16px',
        borderBottom: '1px solid var(--border-subtle)',
        paddingBottom: '18px',
        marginBottom: '16px'
      }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <div style={{
              width: 34,
              height: 34,
              borderRadius: '8px',
              backgroundColor: 'var(--primary-subtle)',
              color: 'var(--primary)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center'
            }}>
              <Activity size={18} />
            </div>
            <div>
              <h2 style={{ fontSize: '1.08rem', fontWeight: 800, color: 'var(--text-primary)', margin: 0 }}>
                Transactions Scored Against Graph Model
              </h2>
              <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>
                Every transaction evaluated with calibrated sigmoid probability, topological convergence &amp; velocity factors
              </span>
            </div>
          </div>
        </div>

        {/* Filter Badges */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap' }}>
          <button
            onClick={() => setFilterClass('ALL')}
            style={{
              padding: '6px 12px',
              fontSize: '0.74rem',
              fontWeight: 700,
              borderRadius: 'var(--radius-sm)',
              border: '1px solid',
              borderColor: filterClass === 'ALL' ? 'var(--primary)' : 'var(--border-subtle)',
              backgroundColor: filterClass === 'ALL' ? 'var(--primary-subtle)' : '#ffffff',
              color: filterClass === 'ALL' ? 'var(--primary)' : 'var(--text-secondary)',
              cursor: 'pointer'
            }}
          >
            All Transfers ({transactions.length})
          </button>

          <button
            onClick={() => setFilterClass('FRAUDULENT')}
            style={{
              padding: '6px 12px',
              fontSize: '0.74rem',
              fontWeight: 700,
              borderRadius: 'var(--radius-sm)',
              border: '1px solid',
              borderColor: filterClass === 'FRAUDULENT' ? 'var(--danger)' : 'var(--border-subtle)',
              backgroundColor: filterClass === 'FRAUDULENT' ? '#fee2e2' : '#ffffff',
              color: filterClass === 'FRAUDULENT' ? '#b91c1c' : 'var(--text-secondary)',
              cursor: 'pointer'
            }}
          >
            Fraudulent ({fraudCount})
          </button>

          <button
            onClick={() => setFilterClass('SUSPICIOUS')}
            style={{
              padding: '6px 12px',
              fontSize: '0.74rem',
              fontWeight: 700,
              borderRadius: 'var(--radius-sm)',
              border: '1px solid',
              borderColor: filterClass === 'SUSPICIOUS' ? 'var(--warning)' : 'var(--border-subtle)',
              backgroundColor: filterClass === 'SUSPICIOUS' ? '#fef3c7' : '#ffffff',
              color: filterClass === 'SUSPICIOUS' ? '#b45309' : 'var(--text-secondary)',
              cursor: 'pointer'
            }}
          >
            Suspicious ({suspCount})
          </button>

          <button
            onClick={() => setFilterClass('LEGITIMATE')}
            style={{
              padding: '6px 12px',
              fontSize: '0.74rem',
              fontWeight: 700,
              borderRadius: 'var(--radius-sm)',
              border: '1px solid',
              borderColor: filterClass === 'LEGITIMATE' ? 'var(--success)' : 'var(--border-subtle)',
              backgroundColor: filterClass === 'LEGITIMATE' ? '#dcfce7' : '#ffffff',
              color: filterClass === 'LEGITIMATE' ? '#15803d' : 'var(--text-secondary)',
              cursor: 'pointer'
            }}
          >
            Legitimate ({licitCount})
          </button>
        </div>
      </div>

      {/* Transactions Table */}
      <div style={{ overflowX: 'auto' }}>
        <table style={{
          width: '100%',
          borderCollapse: 'separate',
          borderSpacing: '0 6px',
          fontSize: '0.78rem'
        }}>
          <thead>
            <tr style={{ color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.04em', fontSize: '0.7rem' }}>
              <th style={{ padding: '8px 12px', textAlign: 'left', fontWeight: 700 }}>Tx Hash</th>
              <th style={{ padding: '8px 12px', textAlign: 'left', fontWeight: 700 }}>Flow Path</th>
              <th style={{ padding: '8px 12px', textAlign: 'right', fontWeight: 700 }}>Amount</th>
              <th style={{ padding: '8px 12px', textAlign: 'center', fontWeight: 700 }}>Graph ML Score</th>
              <th style={{ padding: '8px 12px', textAlign: 'center', fontWeight: 700 }}>Classification</th>
              <th style={{ padding: '8px 12px', textAlign: 'left', fontWeight: 700 }}>Contributing Risk Factors</th>
            </tr>
          </thead>
          <tbody>
            {filteredTxs.map((tx, idx) => {
              const isFraud = tx.classification === 'FRAUDULENT';
              const isSusp = tx.classification === 'SUSPICIOUS';
              const badgeBg = isFraud ? '#fee2e2' : (isSusp ? '#fef3c7' : '#dcfce7');
              const badgeColor = isFraud ? '#b91c1c' : (isSusp ? '#b45309' : '#15803d');

              return (
                <tr
                  key={tx.tx_hash || idx}
                  style={{
                    backgroundColor: '#ffffff',
                    boxShadow: '0 1px 3px rgba(0,0,0,0.03)',
                    borderRadius: '6px',
                    border: '1px solid var(--border-subtle)',
                    transition: 'background-color 0.1s ease'
                  }}
                >
                  {/* Tx Hash */}
                  <td style={{ padding: '10px 12px', whiteSpace: 'nowrap' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                      <span style={{ fontFamily: 'var(--font-mono)', fontWeight: 700, color: 'var(--text-primary)' }}>
                        {tx.tx_hash}
                      </span>
                      <button
                        onClick={() => copyToClipboard(tx.tx_hash, `tx-${idx}`)}
                        style={{ background: 'none', border: 'none', color: 'var(--text-light)', cursor: 'pointer' }}
                        title="Copy Tx Hash"
                      >
                        {copiedKey === `tx-${idx}` ? <Check size={12} color="var(--success)" /> : <Copy size={12} />}
                      </button>
                    </div>
                    {tx.latency_seconds > 0 && (
                      <span style={{ fontSize: '0.68rem', color: 'var(--text-muted)', display: 'flex', alignItems: 'center', gap: '3px', marginTop: '2px' }}>
                        <Clock size={10} /> Latency: {tx.latency_seconds}s
                      </span>
                    )}
                  </td>

                  {/* Flow Path */}
                  <td style={{ padding: '10px 12px' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontFamily: 'var(--font-mono)', fontSize: '0.74rem' }}>
                      <span style={{ color: tx.from_address.includes('Vic') ? 'var(--primary)' : 'var(--text-primary)' }}>
                        {tx.from_address}
                      </span>
                      <ArrowRight size={12} color="var(--text-light)" />
                      <span style={{ color: tx.to_address.includes('VASP') ? 'var(--danger)' : 'var(--text-primary)', fontWeight: 700 }}>
                        {tx.to_address}
                      </span>
                    </div>
                    {tx.gas_sponsor && (
                      <span style={{ fontSize: '0.66rem', color: 'var(--purple)', display: 'block', marginTop: '2px' }}>
                        Gas Sponsor: {tx.gas_sponsor}
                      </span>
                    )}
                  </td>

                  {/* Amount */}
                  <td style={{ padding: '10px 12px', textAlign: 'right', whiteSpace: 'nowrap' }}>
                    <div style={{ fontWeight: 700, color: 'var(--text-primary)', fontFamily: 'var(--font-mono)' }}>
                      {tx.formatted_amount || `${tx.amount.toLocaleString()} USDT`}
                    </div>
                  </td>

                  {/* Score & Progress */}
                  <td style={{ padding: '10px 12px', textAlign: 'center', minWidth: '120px' }}>
                    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '3px' }}>
                      <span style={{ fontWeight: 800, color: badgeColor, fontSize: '0.86rem' }}>
                        {tx.fraud_score} / 100
                      </span>
                      <div style={{
                        width: '80px',
                        height: '5px',
                        backgroundColor: '#e2e8f0',
                        borderRadius: '3px',
                        overflow: 'hidden'
                      }}>
                        <div style={{
                          width: `${tx.fraud_score}%`,
                          height: '100%',
                          backgroundColor: badgeColor
                        }} />
                      </div>
                      <span style={{ fontSize: '0.66rem', color: 'var(--text-muted)' }}>
                        P: {(tx.fraud_probability * 100).toFixed(1)}%
                      </span>
                    </div>
                  </td>

                  {/* Classification */}
                  <td style={{ padding: '10px 12px', textAlign: 'center', whiteSpace: 'nowrap' }}>
                    <span style={{
                      padding: '4px 8px',
                      borderRadius: '4px',
                      fontSize: '0.7rem',
                      fontWeight: 800,
                      backgroundColor: badgeBg,
                      color: badgeColor
                    }}>
                      {tx.classification}
                    </span>
                  </td>

                  {/* Contributing Risk Factors */}
                  <td style={{ padding: '10px 12px' }}>
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: '4px' }}>
                      {(tx.risk_factors || []).map((rf, rIdx) => (
                        <span
                          key={rIdx}
                          style={{
                            padding: '2px 6px',
                            borderRadius: '3px',
                            fontSize: '0.66rem',
                            fontWeight: 600,
                            backgroundColor: isFraud ? '#fff1f2' : (isSusp ? '#fffbeb' : '#f8fafc'),
                            border: `1px solid ${isFraud ? '#fecdd3' : (isSusp ? '#fde68a' : '#e2e8f0')}`,
                            color: isFraud ? '#9f1239' : (isSusp ? '#92400e' : '#475569')
                          }}
                        >
                          {rf}
                        </span>
                      ))}
                    </div>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
