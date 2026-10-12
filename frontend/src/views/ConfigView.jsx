import React, { useState, useEffect } from 'react';
import { 
  Database, 
  Cloud, 
  UploadCloud, 
  Settings2, 
  Play, 
  AlertTriangle, 
  CheckCircle, 
  RefreshCw,
  Sparkles,
  Server,
  ShieldCheck,
  Lock,
  Link2,
  Check,
  Radio
} from 'lucide-react';

export default function ConfigView({ onRunAnalysis, isRunningAnalysis }) {
  const [health, setHealth] = useState(null);
  const [synthCount, setSynthCount] = useState(3000);
  const [synthSeed, setSynthSeed] = useState(42);
  const [hourlyRate, setHourlyRate] = useState(65.0);
  const [autoPct, setAutoPct] = useState(75);
  const [uploadStatus, setUploadStatus] = useState(null);
  const [generating, setGenerating] = useState(false);

  useEffect(() => {
    fetch('/health')
      .then(res => res.json())
      .then(data => setHealth(data))
      .catch(err => console.error('Health check failed:', err));
  }, []);

  const handleGenerateSynthetic = async () => {
    setGenerating(true);
    setUploadStatus(null);
    try {
      const res = await fetch('/api/datasets/generate-synthetic', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ count: Number(synthCount), seed: Number(synthSeed) })
      });
      const data = await res.json();
      setUploadStatus({
        type: 'success',
        message: `Generated and ingested ${synthCount.toLocaleString()} synthetic tickets.`
      });
    } catch (err) {
      setUploadStatus({ type: 'error', message: 'Failed to generate synthetic dataset.' });
    } finally {
      setGenerating(false);
    }
  };

  const handleFileUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;
    const formData = new FormData();
    formData.append('file', file);
    setUploadStatus({ type: 'info', message: 'Uploading and parsing CSV...' });
    try {
      const res = await fetch('/api/datasets/upload', {
        method: 'POST',
        body: formData
      });
      const data = await res.json();
      if (data.invalid_records > 0) {
        setUploadStatus({
          type: 'warning',
          message: `Ingested ${data.valid_records} valid tickets (${data.invalid_records} invalid rows skipped).`
        });
      } else {
        setUploadStatus({
          type: 'success',
          message: `Successfully ingested ${data.valid_records} tickets from ${file.name}.`
        });
      }
    } catch (err) {
      setUploadStatus({ type: 'error', message: 'CSV upload failed.' });
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      {/* Cloud & Mode Architecture Status */}
      <div className="card">
        <h3 className="card-title">
          <Server size={18} color="#2563eb" /> Environment &amp; GCP Architecture Status
        </h3>
        <p className="card-desc">
          Honest environment status. The system clearly indicates whether it is operating in Local Demo Mode or Cloud Run / GCP Mode.
        </p>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '16px', marginTop: '12px' }}>
          <div style={{ background: '#f8fafc', padding: '16px', borderRadius: '8px', border: '1px solid #e2e8f0' }}>
            <div style={{ fontSize: '0.8rem', fontWeight: 600, color: '#64748b', textTransform: 'uppercase' }}>Operational Mode</div>
            <div style={{ fontSize: '1.15rem', fontWeight: 700, marginTop: '4px' }}>
              <span className={`badge ${health?.is_cloud_mode_ready ? 'badge-green' : 'badge-purple'}`}>
                {health?.is_cloud_mode_ready ? 'GCP Cloud Mode' : 'Local Standalone Demo Mode'}
              </span>
            </div>
            <div style={{ fontSize: '0.78rem', color: '#64748b', marginTop: '6px' }}>
              {health?.is_cloud_mode_ready 
                ? 'Connected to Vertex AI & BigQuery' 
                : 'Deterministic local embeddings & SQLite analytics'}
            </div>
          </div>

          <div style={{ background: '#f8fafc', padding: '16px', borderRadius: '8px', border: '1px solid #e2e8f0' }}>
            <div style={{ fontSize: '0.8rem', fontWeight: 600, color: '#64748b', textTransform: 'uppercase' }}>BigQuery Storage</div>
            <div style={{ fontSize: '1.15rem', fontWeight: 700, marginTop: '4px' }}>
              <code>workflow_mining</code>
            </div>
            <div style={{ fontSize: '0.78rem', color: '#64748b', marginTop: '6px' }}>
              Analytical dataset holding canonical schemas &amp; SQL scripts
            </div>
          </div>

          <div style={{ background: '#f8fafc', padding: '16px', borderRadius: '8px', border: '1px solid #e2e8f0' }}>
            <div style={{ fontSize: '0.8rem', fontWeight: 600, color: '#64748b', textTransform: 'uppercase' }}>AI Orchestrator</div>
            <div style={{ fontSize: '1.15rem', fontWeight: 700, marginTop: '4px' }}>
              Google ADK + Gemini
            </div>
            <div style={{ fontSize: '0.78rem', color: '#64748b', marginTop: '6px' }}>
              Multi-step drafting agent with human review gate
            </div>
          </div>
        </div>
      </div>

      {/* Dataset Generation & CSV Ingestion */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '24px' }}>
        {/* Synthetic Dataset Generator */}
        <div className="card">
          <h3 className="card-title">
            <Sparkles size={18} color="#7c3aed" /> Synthetic Dataset Generator
          </h3>
          <p className="card-desc">
            Generate between 2,000 and 5,000 realistic IT service tickets with 6 planted repetitive workflows and ground truth.
          </p>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px', marginBottom: '16px' }}>
            <div>
              <label style={{ fontSize: '0.8rem', fontWeight: 600, color: '#475569' }}>Ticket Count</label>
              <select 
                value={synthCount} 
                onChange={(e) => setSynthCount(e.target.value)}
                style={{ width: '100%', padding: '8px', borderRadius: '6px', border: '1px solid #cbd5e1', marginTop: '4px' }}
              >
                <option value="1000">1,000 Tickets</option>
                <option value="3000">3,000 Tickets (Default)</option>
                <option value="5000">5,000 Tickets (Stress Test)</option>
              </select>
            </div>

            <div>
              <label style={{ fontSize: '0.8rem', fontWeight: 600, color: '#475569' }}>Deterministic Seed</label>
              <input 
                type="number"
                value={synthSeed}
                onChange={(e) => setSynthSeed(e.target.value)}
                style={{ width: '100%', padding: '8px', borderRadius: '6px', border: '1px solid #cbd5e1', marginTop: '4px' }}
              />
            </div>
          </div>

          <button 
            className="btn btn-primary"
            disabled={generating}
            onClick={handleGenerateSynthetic}
            style={{ width: '100%' }}
          >
            <RefreshCw size={15} /> {generating ? 'Generating tickets...' : 'Generate & Ingest Synthetic Tickets'}
          </button>
        </div>

        {/* Custom CSV Upload */}
        <div className="card">
          <h3 className="card-title">
            <UploadCloud size={18} color="#2563eb" /> Upload Enterprise Service Tickets (CSV)
          </h3>
          <p className="card-desc">
            Upload custom IT service tickets. Column names will be automatically mapped to the canonical schema.
          </p>

          <div 
            style={{ 
              border: '2px dashed #cbd5e1', 
              borderRadius: '8px', 
              padding: '24px', 
              textAlign: 'center', 
              background: '#f8fafc',
              cursor: 'pointer'
            }}
          >
            <UploadCloud size={32} color="#94a3b8" style={{ margin: '0 auto 10px' }} />
            <div style={{ fontSize: '0.9rem', fontWeight: 600, color: '#334155' }}>
              Select CSV File
            </div>
            <div style={{ fontSize: '0.78rem', color: '#64748b', marginTop: '4px' }}>
              Supports title, description, category, timestamps, resolution notes
            </div>
            <input 
              type="file" 
              accept=".csv" 
              onChange={handleFileUpload} 
              style={{ marginTop: '12px', fontSize: '0.82rem' }}
            />
          </div>
        </div>
      </div>

      {uploadStatus && (
        <div className={`alert ${uploadStatus.type === 'success' ? 'alert-success' : 'alert-info'}`}>
          {uploadStatus.message}
        </div>
      )}

      {/* Enterprise ITSM Connectors & Cloud DLP Section */}
      <EnterpriseConnectorsSection />

      {/* Analysis Parameters & Re-Run Control */}
      <div className="card">
        <h3 className="card-title">
          <Settings2 size={18} color="#059669" /> Mining &amp; Financial Quantification Controls
        </h3>
        <p className="card-desc">
          Adjust financial rate assumptions used by deterministic BigQuery calculations and re-run workflow discovery.
        </p>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '16px', marginBottom: '20px' }}>
          <div>
            <label style={{ fontSize: '0.8rem', fontWeight: 600, color: '#475569' }}>Hourly Labor Rate ($/hour)</label>
            <input 
              type="number"
              value={hourlyRate}
              onChange={(e) => setHourlyRate(e.target.value)}
              style={{ width: '100%', padding: '8px', borderRadius: '6px', border: '1px solid #cbd5e1', marginTop: '4px' }}
            />
          </div>

          <div>
            <label style={{ fontSize: '0.8rem', fontWeight: 600, color: '#475569' }}>Default Automatable Ratio (%)</label>
            <input 
              type="number"
              value={autoPct}
              onChange={(e) => setAutoPct(e.target.value)}
              style={{ width: '100%', padding: '8px', borderRadius: '6px', border: '1px solid #cbd5e1', marginTop: '4px' }}
            />
          </div>

          <div>
            <label style={{ fontSize: '0.8rem', fontWeight: 600, color: '#475569' }}>Workflow Clusters (k)</label>
            <select 
              defaultValue="6"
              style={{ width: '100%', padding: '8px', borderRadius: '6px', border: '1px solid #cbd5e1', marginTop: '4px' }}
            >
              <option value="6">6 Clusters (Planted Benchmark)</option>
              <option value="8">8 Clusters</option>
              <option value="10">10 Clusters</option>
            </select>
          </div>
        </div>

        <button 
          className="btn btn-primary"
          disabled={isRunningAnalysis}
          onClick={() => onRunAnalysis(hourlyRate, autoPct / 100.0)}
          style={{ width: '100%' }}
        >
          <Play size={16} /> {isRunningAnalysis ? 'Analysis in Progress...' : 'Re-Run End-to-End Workflow Mining Analysis'}
        </button>
      </div>
    </div>
  );
}


function EnterpriseConnectorsSection() {
  const [connectors, setConnectors] = useState([]);
  const [loading, setLoading] = useState(true);
  const [actionStatus, setActionStatus] = useState({});
  const [syncingId, setSyncingId] = useState(null);
  const [testingId, setTestingId] = useState(null);

  // DLP state
  const [dlpSample, setDlpSample] = useState(
    "Root password set to Pwd!Secure987 on host 10.240.0.14 while testing deploy with token ghp_99887766554433221100aabbccddeeff0011 by admin john.doe@enterprise.corp."
  );
  const [dlpResult, setDlpResult] = useState(null);
  const [dlpLoading, setDlpLoading] = useState(false);

  useEffect(() => {
    fetchConnectors();
  }, []);

  const fetchConnectors = async () => {
    try {
      const res = await fetch('/api/connectors');
      const data = await res.json();
      setConnectors(data || []);
    } catch (err) {
      console.error('Failed to load connectors:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleTestConnection = async (connectorId) => {
    setTestingId(connectorId);
    setActionStatus(prev => ({ ...prev, [connectorId]: { type: 'info', message: 'Testing connectivity...' } }));
    try {
      const res = await fetch(`/api/connectors/${connectorId}/test`, { method: 'POST' });
      const data = await res.json();
      if (res.ok) {
        setActionStatus(prev => ({ ...prev, [connectorId]: { type: 'success', message: data.message } }));
      } else {
        setActionStatus(prev => ({ ...prev, [connectorId]: { type: 'error', message: data.detail || 'Connection test failed.' } }));
      }
    } catch (err) {
      setActionStatus(prev => ({ ...prev, [connectorId]: { type: 'error', message: 'Network error communicating with connector.' } }));
    } finally {
      setTestingId(null);
    }
  };

  const handleSyncTickets = async (connectorId) => {
    setSyncingId(connectorId);
    setActionStatus(prev => ({ ...prev, [connectorId]: { type: 'info', message: 'Syncing and sanitizing tickets...' } }));
    try {
      const res = await fetch(`/api/connectors/${connectorId}/sync`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ max_records: 50 })
      });
      const data = await res.json();
      if (res.ok && data.status === 'SUCCESS') {
        setActionStatus(prev => ({
          ...prev,
          [connectorId]: { 
            type: 'success', 
            message: `Successfully ingested ${data.tickets_ingested} tickets (sanitized with Cloud DLP in ${data.duration_seconds}s).` 
          }
        }));
        fetchConnectors();
      } else {
        setActionStatus(prev => ({ ...prev, [connectorId]: { type: 'error', message: data.errors?.[0] || 'Sync failed.' } }));
      }
    } catch (err) {
      setActionStatus(prev => ({ ...prev, [connectorId]: { type: 'error', message: 'Sync request failed.' } }));
    } finally {
      setSyncingId(null);
    }
  };

  const handleRunDlpPreview = async () => {
    setDlpLoading(true);
    try {
      const res = await fetch('/api/connectors/dlp/preview', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          sample_text: dlpSample,
          mask_pii: true,
          mask_secrets: true,
          mask_network: true,
          mask_financial: true
        })
      });
      const data = await res.json();
      setDlpResult(data);
    } catch (err) {
      console.error('DLP preview error:', err);
    } finally {
      setDlpLoading(false);
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      {/* Enterprise Connectors Card */}
      <div className="card">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            <h3 className="card-title">
              <Link2 size={18} color="#0284c7" /> Enterprise ITSM Connectors (Jira &amp; ServiceNow)
            </h3>
            <p className="card-desc">
              Connect directly to Jira Cloud, Jira Data Center, and ServiceNow ITSM instances with OAuth 2.0, API tokens, and automatic schema normalization.
            </p>
          </div>
          <span className="badge badge-blue">Enterprise Integration Layer</span>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '16px', marginTop: '16px' }}>
          {connectors.map(c => {
            const status = actionStatus[c.connector_id];
            const isJira = c.connector_type === 'JIRA';
            return (
              <div 
                key={c.connector_id} 
                style={{ 
                  background: '#f8fafc', 
                  border: '1px solid #e2e8f0', 
                  borderRadius: '10px', 
                  padding: '20px',
                  display: 'flex',
                  flexDirection: 'column',
                  justifyContent: 'space-between'
                }}
              >
                <div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '12px' }}>
                    <div>
                      <div style={{ fontWeight: 700, fontSize: '1rem', color: '#0f172a' }}>
                        {c.name}
                      </div>
                      <div style={{ fontSize: '0.8rem', color: '#64748b', marginTop: '2px' }}>
                        <code>{c.base_url}</code>
                      </div>
                    </div>
                    <span className={`badge ${isJira ? 'badge-blue' : 'badge-purple'}`}>
                      {c.connector_type}
                    </span>
                  </div>

                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px', fontSize: '0.8rem', color: '#475569', marginBottom: '14px' }}>
                    <div><strong>Auth:</strong> {c.auth_type}</div>
                    <div><strong>Tickets Synced:</strong> {c.total_tickets_synced?.toLocaleString() || 0}</div>
                    <div style={{ gridColumn: 'span 2' }}>
                      <strong>Filter Query:</strong> <code style={{ fontSize: '0.75rem' }}>{c.query_filter?.substring(0, 45)}...</code>
                    </div>
                  </div>

                  {status && (
                    <div 
                      style={{ 
                        fontSize: '0.8rem', 
                        padding: '8px 12px', 
                        borderRadius: '6px', 
                        marginBottom: '12px',
                        background: status.type === 'success' ? '#ecfdf5' : status.type === 'error' ? '#fef2f2' : '#f0f9ff',
                        color: status.type === 'success' ? '#065f46' : status.type === 'error' ? '#991b1b' : '#0369a1',
                        border: `1px solid ${status.type === 'success' ? '#a7f3d0' : status.type === 'error' ? '#fecaca' : '#bae6fd'}`
                      }}
                    >
                      {status.message}
                    </div>
                  )}
                </div>

                <div style={{ display: 'flex', gap: '8px', marginTop: '12px' }}>
                  <button 
                    className="btn btn-secondary" 
                    style={{ flex: 1, fontSize: '0.8rem', padding: '8px' }}
                    disabled={testingId === c.connector_id || syncingId === c.connector_id}
                    onClick={() => handleTestConnection(c.connector_id)}
                  >
                    {testingId === c.connector_id ? 'Testing...' : 'Test Connection'}
                  </button>
                  <button 
                    className="btn btn-primary" 
                    style={{ flex: 1, fontSize: '0.8rem', padding: '8px' }}
                    disabled={testingId === c.connector_id || syncingId === c.connector_id}
                    onClick={() => handleSyncTickets(c.connector_id)}
                  >
                    {syncingId === c.connector_id ? 'Syncing...' : 'Sync Tickets'}
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Google Cloud Sensitive Data Protection (DLP) Privacy Gate */}
      <div className="card">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            <h3 className="card-title">
              <ShieldCheck size={18} color="#059669" /> Data Hygiene &amp; Privacy Gate (Google Cloud DLP)
            </h3>
            <p className="card-desc">
              Guarantees zero leakage into LLM prompts or vector embeddings. Automatically redacts employee PII, credentials, API tokens, passwords, and private internal IP addresses before mining.
            </p>
          </div>
          <span className="badge badge-green">Zero-Leakage Privacy Policy</span>
        </div>

        <div style={{ marginTop: '16px' }}>
          <label style={{ fontSize: '0.8rem', fontWeight: 600, color: '#475569' }}>
            Test Raw Ticket Text (Type or test with secrets, IPs, and PII):
          </label>
          <textarea
            value={dlpSample}
            onChange={(e) => setDlpSample(e.target.value)}
            rows={3}
            style={{
              width: '100%',
              marginTop: '6px',
              padding: '10px',
              borderRadius: '6px',
              border: '1px solid #cbd5e1',
              fontFamily: 'monospace',
              fontSize: '0.85rem'
            }}
          />

          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '10px' }}>
            <div style={{ display: 'flex', gap: '12px', fontSize: '0.8rem', color: '#64748b' }}>
              <span>✅ Passwords &amp; API Keys</span>
              <span>✅ Private Hostnames &amp; IPs</span>
              <span>✅ Employee Emails &amp; PII</span>
            </div>
            <button 
              className="btn btn-secondary" 
              onClick={handleRunDlpPreview}
              disabled={dlpLoading}
              style={{ fontSize: '0.82rem' }}
            >
              {dlpLoading ? 'Sanitizing...' : 'Preview DLP Redaction'}
            </button>
          </div>

          {dlpResult && (
            <div style={{ marginTop: '16px', background: '#f8fafc', padding: '16px', borderRadius: '8px', border: '1px solid #e2e8f0' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                <span style={{ fontSize: '0.85rem', fontWeight: 700, color: '#0f172a' }}>
                  Sanitized Text (Safe for Vector Embeddings &amp; Gemini Prompts):
                </span>
                <span className="badge badge-purple">
                  {dlpResult.total_redactions} redactions applied
                </span>
              </div>
              <div style={{ background: '#ffffff', padding: '12px', borderRadius: '6px', border: '1px solid #cbd5e1', fontFamily: 'monospace', fontSize: '0.85rem', color: '#047857' }}>
                {dlpResult.sanitized_text}
              </div>
              <div style={{ display: 'flex', gap: '8px', marginTop: '10px', flexWrap: 'wrap' }}>
                {dlpResult.redactions.map((r, i) => (
                  <span key={i} className="badge badge-blue" style={{ fontSize: '0.75rem' }}>
                    {r.type}: {r.count}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

