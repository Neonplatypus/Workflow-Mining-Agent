import React, { useState, useEffect } from 'react';
import { 
  LayoutDashboard, 
  Search, 
  Workflow, 
  Cpu, 
  CheckCircle, 
  Settings, 
  Layers, 
  ShieldAlert, 
  RefreshCw,
  Server
} from 'lucide-react';

import OverviewView from './views/OverviewView';
import TicketExplorerView from './views/TicketExplorerView';
import WorkflowOpportunitiesView from './views/WorkflowOpportunitiesView';
import AutomationStudioView from './views/AutomationStudioView';
import EvaluationCenterView from './views/EvaluationCenterView';
import ConfigView from './views/ConfigView';

export default function App() {
  const [activeTab, setActiveTab] = useState('overview');
  const [summary, setSummary] = useState(null);
  const [selectedWorkflowId, setSelectedWorkflowId] = useState(null);
  const [isRunningAnalysis, setIsRunningAnalysis] = useState(false);
  const [analysisStatusText, setAnalysisStatusText] = useState('');

  const fetchSummary = async () => {
    try {
      const res = await fetch('/api/dashboard/summary');
      if (res.ok) {
        const data = await res.json();
        setSummary(data);
      }
    } catch (err) {
      console.error('Failed to fetch dashboard summary:', err);
    }
  };

  useEffect(() => {
    fetchSummary();
  }, []);

  const handleRunAnalysis = async (hourlyRate = 65.0, automatablePct = 0.75) => {
    setIsRunningAnalysis(true);
    setAnalysisStatusText('Triggering workflow analysis pipeline...');
    try {
      const res = await fetch('/api/analysis/run', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          dataset_name: 'IT Service Tickets',
          hourly_labor_rate: Number(hourlyRate),
          automatable_percentage: Number(automatablePct),
          n_clusters: 6
        })
      });
      const data = await res.json();
      const runId = data.run_id;

      // Poll until completed
      const pollInterval = setInterval(async () => {
        try {
          const pollRes = await fetch(`/api/analysis/${runId}`);
          const pollData = await pollRes.json();
          setAnalysisStatusText(pollData.message || 'Processing...');
          if (pollData.status === 'COMPLETED' || pollData.status === 'FAILED') {
            clearInterval(pollInterval);
            setIsRunningAnalysis(false);
            setAnalysisStatusText('');
            await fetchSummary();
            setActiveTab('overview');
          }
        } catch (e) {
          clearInterval(pollInterval);
          setIsRunningAnalysis(false);
        }
      }, 1500);
    } catch (err) {
      console.error('Failed to start analysis run:', err);
      setIsRunningAnalysis(false);
      setAnalysisStatusText('');
    }
  };

  return (
    <div className="app-container">
      {/* Sidebar Navigation */}
      <aside className="sidebar">
        <div className="sidebar-header">
          <div className="brand-title">
            <Workflow size={22} color="#2563eb" />
            <span>Workflow Mining</span>
          </div>
          <div style={{ marginTop: '6px', display: 'flex', gap: '6px', alignItems: 'center' }}>
            <span className="brand-badge">AI Builder Cup 2026</span>
            <span className="badge badge-gray" style={{ fontSize: '0.65rem' }}>v1.0</span>
          </div>
        </div>

        <nav className="sidebar-nav">
          <button 
            className={`nav-item ${activeTab === 'overview' ? 'active' : ''}`}
            onClick={() => setActiveTab('overview')}
          >
            <LayoutDashboard size={18} />
            <span>Overview</span>
          </button>

          <button 
            className={`nav-item ${activeTab === 'tickets' ? 'active' : ''}`}
            onClick={() => setActiveTab('tickets')}
          >
            <Search size={18} />
            <span>Ticket Explorer</span>
          </button>

          <button 
            className={`nav-item ${activeTab === 'workflows' ? 'active' : ''}`}
            onClick={() => { setSelectedWorkflowId(null); setActiveTab('workflows'); }}
          >
            <Workflow size={18} />
            <span>Workflow Opportunities</span>
          </button>

          <button 
            className={`nav-item ${activeTab === 'studio' ? 'active' : ''}`}
            onClick={() => { setSelectedWorkflowId(null); setActiveTab('studio'); }}
          >
            <Cpu size={18} />
            <span>Automation Studio</span>
          </button>

          <button 
            className={`nav-item ${activeTab === 'evaluation' ? 'active' : ''}`}
            onClick={() => setActiveTab('evaluation')}
          >
            <CheckCircle size={18} />
            <span>Evaluation Center</span>
          </button>

          <button 
            className={`nav-item ${activeTab === 'config' ? 'active' : ''}`}
            onClick={() => setActiveTab('config')}
          >
            <Settings size={18} />
            <span>Data &amp; Config</span>
          </button>
        </nav>

        {/* Sidebar Footer */}
        <div className="sidebar-footer">
          <div style={{ fontSize: '0.78rem', color: '#64748b', display: 'flex', alignItems: 'center', gap: '6px' }}>
            <div style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#059669' }} />
            <span>Agent Active &bull; Human in the Loop</span>
          </div>
          <div style={{ fontSize: '0.72rem', color: '#94a3b8', marginTop: '4px' }}>
            Never executes automations automatically
          </div>
        </div>
      </aside>

      {/* Main Content Area */}
      <main className="main-content">
        {/* Top Header Bar */}
        <header className="top-bar">
          <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
            <h1 style={{ fontSize: '1.25rem', fontWeight: 700, letterSpacing: '-0.02em', textTransform: 'capitalize' }}>
              {activeTab === 'overview' && 'Executive Overview'}
              {activeTab === 'tickets' && 'Service Ticket Explorer'}
              {activeTab === 'workflows' && 'Workflow Opportunities & Ranking'}
              {activeTab === 'studio' && 'Automation Studio (Google ADK)'}
              {activeTab === 'evaluation' && 'Evaluation & Ground-Truth Center'}
              {activeTab === 'config' && 'Data Ingestion & GCP Configuration'}
            </h1>
            {isRunningAnalysis && (
              <span className="badge badge-amber" style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                <RefreshCw size={12} className="spin" /> {analysisStatusText}
              </span>
            )}
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <button 
              className="btn btn-outline btn-sm"
              onClick={fetchSummary}
              title="Refresh Metrics"
            >
              <RefreshCw size={14} /> Refresh
            </button>
            <button 
              className="btn btn-primary btn-sm"
              disabled={isRunningAnalysis}
              onClick={() => handleRunAnalysis(65.0, 0.75)}
            >
              Run Mining Agent
            </button>
          </div>
        </header>

        {/* Active Page View */}
        <div className="page-container">
          {activeTab === 'overview' && (
            <OverviewView 
              summary={summary}
              onNavigateToWorkflow={(wfId) => {
                setSelectedWorkflowId(wfId);
                setActiveTab('workflows');
              }}
              onNavigateToStudio={(wfId) => {
                setSelectedWorkflowId(wfId);
                setActiveTab('studio');
              }}
            />
          )}

          {activeTab === 'tickets' && (
            <TicketExplorerView 
              onNavigateToWorkflow={(wfId) => {
                setSelectedWorkflowId(wfId);
                setActiveTab('workflows');
              }}
            />
          )}

          {activeTab === 'workflows' && (
            <WorkflowOpportunitiesView 
              initialWorkflowId={selectedWorkflowId}
              onNavigateToStudio={(wfId) => {
                setSelectedWorkflowId(wfId);
                setActiveTab('studio');
              }}
            />
          )}

          {activeTab === 'studio' && (
            <AutomationStudioView 
              workflowId={selectedWorkflowId}
            />
          )}

          {activeTab === 'evaluation' && (
            <EvaluationCenterView 
              runId={summary?.active_run_id}
            />
          )}

          {activeTab === 'config' && (
            <ConfigView 
              onRunAnalysis={handleRunAnalysis}
              isRunningAnalysis={isRunningAnalysis}
            />
          )}
        </div>
      </main>
    </div>
  );
}
