import { useParams } from 'react-router-dom'

export default function ReportPage() {
  const { sessionId } = useParams<{ sessionId: string }>()

  return (
    <main className="report-page">
      <h1>Discovery Report</h1>
      <p>Session: {sessionId}</p>
      {/* TODO: fetch and render report */}
    </main>
  )
}
