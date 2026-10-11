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
  Server
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
