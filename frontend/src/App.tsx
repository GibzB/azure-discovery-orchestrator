import { BrowserRouter, Routes, Route } from 'react-router-dom'
import ChatPage from '../pages/ChatPage'
import ReportPage from '../pages/ReportPage'

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<ChatPage />} />
        <Route path="/reports/:sessionId" element={<ReportPage />} />
      </Routes>
    </BrowserRouter>
  )
}
