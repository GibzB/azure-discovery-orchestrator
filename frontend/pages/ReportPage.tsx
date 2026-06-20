import { useParams, Link } from 'react-router-dom'

export default function ReportPage() {
  const { sessionId } = useParams<{ sessionId: string }>()

  return (
    <>
      <header className="app-header">
        <div className="brand">
          <div className="brand-icon" aria-hidden="true">⬡</div>
          <div className="brand-name">Azure Discovery Orchestrator</div>
        </div>
      </header>

      <main className="page-main">
        <div className="report-card">
          <div style={{ fontSize: 40, marginBottom: 16 }}>✅</div>
          <h1 className="report-title">Discovery Session Complete</h1>
          <p className="report-sub">
            Your architecture report is being generated. You'll receive it
            via email shortly, or download it below once ready.
          </p>

          <div style={{ display: 'flex', gap: 12, justifyContent: 'center', flexWrap: 'wrap' }}>
            <a
              href={`/api/v1/reports/${sessionId}/download`}
              className="report-btn"
              aria-label="Download discovery report"
            >
              ⬇ Download Report
            </a>
            <Link
              to="/"
              className="end-btn"
              style={{ textDecoration: 'none', padding: '11px 22px', borderRadius: 999 }}
            >
              ← Start New Session
            </Link>
          </div>

          {sessionId && (
            <p style={{ marginTop: 24, fontSize: 12, color: 'var(--text-muted)' }}>
              Session ID: <code>{sessionId}</code>
            </p>
          )}
        </div>
      </main>
    </>
  )
}
