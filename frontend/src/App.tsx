import { Routes, Route } from 'react-router-dom'
import Layout from './components/layout/Layout'
import DashboardPage from './pages/DashboardPage'
import ChatPage from './pages/ChatPage'
import EvaluationsPage from './pages/EvaluationsPage'
import GoldenSetsPage from './pages/GoldenSetsPage'
import GoldenSetDetailPage from './pages/GoldenSetDetailPage'

function App() {
  return (
    <Layout>
      <Routes>
        <Route path="/" element={<DashboardPage />} />
        <Route path="/chat" element={<ChatPage />} />
        <Route path="/evaluations" element={<EvaluationsPage />} />
        <Route path="/golden-sets" element={<GoldenSetsPage />} />
        <Route path="/golden-sets/:id" element={<GoldenSetDetailPage />} />
      </Routes>
    </Layout>
  )
}

export default App
