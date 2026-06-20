import { useParams, Link } from 'react-router-dom'
import AppFooter from '../components/AppFooter'

export default function ReportPage() {
  const { sessionId } = useParams<{ sessionId: string }>()

  return (
    <>
      <header className="app-header">
        <div className="brand">
          <div className="brand-logo" aria-hidden="true">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/>
            </svg>
          </div>
          <div className="brand-text">
            <div className="brand-name">Discovery Orchestrator</div>
            <div className="brand-tagline">Powered by Azure AI</div>
          </div>
        </div>
      </header>

      <main className="page-main">
        <div className="glass-card">
          <div className="report-wrap">
            <div className="report-icon">🎉</div>
            <h1 className="report-title">Discovery Complete</h1>
            <p className="report-sub">
              Your AI consultant has finished the architecture discovery session.
              Your personalised Azure architecture report is ready to download.
            </p>

            <div className="report-actions">
              <a
                href={`/api/v1/reports/${sessionId}/download`}
                className="report-btn-primary"
                aria-label="Download your discovery report"
              >
                <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                  <path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/>
                </svg>
                Download Report
              </a>

              <Link to="/" className="report-btn-secondary">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                  <polyline points="15 18 9 12 15 6"/>
                </svg>
                Start New Session
              </Link>
            </div>

            {sessionId && (
              <p className="session-id">
                Session <code>{sessionId.slice(0, 8)}…</code>
              </p>
            )}
          </div>
        </div>
      </main>

      <AppFooter />
    </>
  )
}
