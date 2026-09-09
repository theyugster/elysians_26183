import React, { useEffect } from 'react';
import { X, Printer, Check, Copy, Shield, Lock } from 'lucide-react';
import confetti from 'canvas-confetti';

export default function DossierModal({
  isOpen,
  onClose,
  dossierData,
  onCopyHash,
  hasCopiedHash,
}) {
  useEffect(() => {
    if (isOpen) {
      confetti({
        particleCount: 45,
        spread: 60,
        origin: { y: 0.7 },
        colors: ['#2563eb', '#3b82f6', '#93c5fd']
      });
    }
  }, [isOpen]);

  if (!isOpen || !dossierData) return null;

  const handlePrint = () => {
    window.print();
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-window" onClick={e => e.stopPropagation()}>
        {/* Header */}
        <div style={{ padding: '18px 24px', borderBottom: '1px solid var(--border-subtle)', display: 'flex', alignItems: 'center', justifyContent: 'space-between', backgroundColor: '#ffffff' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
            <span style={{ backgroundColor: 'var(--primary-soft)', color: 'var(--primary)', border: '1px solid var(--primary-border)', padding: '6px 12px', borderRadius: 'var(--radius-md)', fontSize: '0.74rem', fontWeight: 800, letterSpacing: '0.05em' }}>
              सत्यमेव जयते
            </span>
            <div>
              <h2 style={{ fontSize: '1.05rem', fontWeight: 800, color: 'var(--text-primary)', letterSpacing: '-0.01em' }}>
                FORMAL DIGITAL EVIDENCE REQUISITION NOTICE
              </h2>
              <span style={{ fontSize: '0.74rem', color: 'var(--text-muted)' }}>
                Under Section 94, Bharatiya Nagarik Suraksha Sanhita (BNSS), 2023
              </span>
            </div>
          </div>

          <button
            onClick={onClose}
            style={{ background: 'none', border: 'none', color: 'var(--text-light)', cursor: 'pointer', display: 'flex' }}
          >
            <X size={20} />
          </button>
        </div>

        {/* Document Body */}
        <div className="modal-doc-body">
          <div className="official-court-dossier">
            {/* Metadata Banner */}
            <div className="dossier-meta-row">
              <div>
                <span className="meta-field-label">REQUISITION REF NO:</span>
                <span className="meta-field-value" style={{ color: 'var(--primary)' }}>
                  {dossierData.dossierId}
                </span>
              </div>
              <div>
                <span className="meta-field-label">DATE OF ISSUANCE:</span>
                <span className="meta-field-value">
                  {new Date(dossierData.createdAt).toUTCString()}
                </span>
              </div>
              <div>
                <span className="meta-field-label">INVESTIGATING OFFICER:</span>
                <span className="meta-field-value">
                  {dossierData.officerId}
                </span>
              </div>
            </div>

            {/* Legal Notice */}
            <div className="notice-text-content">
              <div className="notice-callout">
                <strong>TO:</strong> Compliance Officer / Designated Grievance Officer<br />
                <strong>ENTITY:</strong> {dossierData.terminalExchange}<br />
                <strong>JURISDICTION:</strong> Seychelles / Non-Compliant Offshore Jurisdiction
              </div>

              <p>
                <strong>WHEREAS</strong> an investigation under the relevant provisions of the Bharatiya Nagarik Suraksha Sanhita, 2023 and the Information Technology Act, 2000 is ongoing regarding unauthorized exfiltration and layering of illicit cryptocurrency assets.
              </p>

              <p>
                <strong>AND WHEREAS</strong> deterministic 5-Hop forensic graph traversal has tracked stolen funds originating from victim wallet <code style={{ fontFamily: 'var(--font-mono)', backgroundColor: 'var(--bg-muted)', padding: '2px 6px', borderRadius: '4px', color: 'var(--primary)', fontWeight: 600 }}>{dossierData.targetWallet}</code> directly into hot wallet <code style={{ fontFamily: 'var(--font-mono)', backgroundColor: 'var(--bg-muted)', padding: '2px 6px', borderRadius: '4px', color: 'var(--danger)', fontWeight: 600 }}>0xVASP_GlobalEx</code> associated with your service terminal.
              </p>

              <p>
                <strong>NOW THEREFORE</strong>, you are hereby mandated under Section 94 of BNSS to:
              </p>

              <ol style={{ paddingLeft: '20px', display: 'flex', flexDirection: 'column', gap: '6px' }}>
                <li>Immediately freeze and halt all outbound transfers, withdrawals, and swap transactions associated with target deposit identifier.</li>
                <li>Furnish complete KYC records, registered IP access logs, associated banking off-ramp channels, and transaction hashes within <strong>24 hours</strong>.</li>
              </ol>

              {/* Cryptographic SHA-256 Audit Seal */}
              <div className="sha256-seal-box">
                <div style={{ color: 'var(--primary)' }}>
                  <Lock size={22} />
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
                  <span style={{ fontSize: '0.7rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase' }}>
                    Cryptographic Evidence Integrity Seal (SHA-256 Audit Hash):
                  </span>
                  <code className="seal-hash-code">
                    {dossierData.sha256AuditHash}
                  </code>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Modal Footer Actions */}
        <div style={{ padding: '16px 24px', borderTop: '1px solid var(--border-subtle)', display: 'flex', alignItems: 'center', justifyContent: 'flex-end', gap: '12px', backgroundColor: '#ffffff' }}>
          <button
            onClick={() => onCopyHash(dossierData.sha256AuditHash)}
            style={{ backgroundColor: '#ffffff', border: '1px solid var(--border-subtle)', color: 'var(--text-secondary)', padding: '9px 16px', borderRadius: 'var(--radius-md)', fontSize: '0.82rem', fontWeight: 600, cursor: 'pointer', display: 'inline-flex', alignItems: 'center', gap: '6px' }}
          >
            {hasCopiedHash ? <Check size={14} color="var(--success)" /> : <Copy size={14} />}
            {hasCopiedHash ? 'Copied Seal' : 'Copy Audit Hash'}
          </button>

          <button
            onClick={handlePrint}
            className="btn-primary-trace"
          >
            <Printer size={15} />
            Print / Export Legal Order
          </button>
        </div>
      </div>
    </div>
  );
}
