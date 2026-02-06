import { Routes, Route } from 'react-router-dom'

function App() {
  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white shadow">
        <div className="max-w-7xl mx-auto py-6 px-4 sm:px-6 lg:px-8">
          <h1 className="text-3xl font-bold text-gray-900">
            ExportSathi
          </h1>
          <p className="mt-1 text-sm text-gray-600">
            AI-Powered Export Compliance & Certification Co-Pilot
          </p>
        </div>
      </header>

      <main className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/reports" element={<ReportsPage />} />
          <Route path="/certifications" element={<CertificationsPage />} />
          <Route path="/documents" element={<DocumentsPage />} />
          <Route path="/finance" element={<FinancePage />} />
          <Route path="/logistics" element={<LogisticsPage />} />
        </Routes>
      </main>
    </div>
  )
}

// Placeholder components
function HomePage() {
  return (
    <div className="px-4 py-6 sm:px-0">
      <div className="border-4 border-dashed border-gray-200 rounded-lg h-96 flex items-center justify-center">
        <div className="text-center">
          <h2 className="text-2xl font-semibold text-gray-900 mb-4">
            Welcome to ExportSathi
          </h2>
          <p className="text-gray-600">
            Start your export journey in 7 days
          </p>
        </div>
      </div>
    </div>
  )
}

function ReportsPage() {
  return <div className="p-4">Reports Page - To be implemented</div>
}

function CertificationsPage() {
  return <div className="p-4">Certifications Page - To be implemented</div>
}

function DocumentsPage() {
  return <div className="p-4">Documents Page - To be implemented</div>
}

function FinancePage() {
  return <div className="p-4">Finance Page - To be implemented</div>
}

function LogisticsPage() {
  return <div className="p-4">Logistics Page - To be implemented</div>
}

export default App
