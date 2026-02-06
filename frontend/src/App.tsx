import { Routes, Route, Link, useLocation } from 'react-router-dom';
import { ErrorBoundary } from './components/common';
import {
  HomePage,
  ReportsPage,
  NewReportPage,
  ReportViewPage,
  CertificationsPage,
  DocumentsPage,
  FinancePage,
  LogisticsPage,
} from './pages';

function App() {
  const location = useLocation();

  const navigation = [
    { name: 'Home', path: '/' },
    { name: 'Reports', path: '/reports' },
    { name: 'Certifications', path: '/certifications' },
    { name: 'Documents', path: '/documents' },
    { name: 'Finance', path: '/finance' },
    { name: 'Logistics', path: '/logistics' },
  ];

  return (
    <ErrorBoundary>
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
          <nav className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex space-x-8 border-t border-gray-200">
              {navigation.map((item) => (
                <Link
                  key={item.path}
                  to={item.path}
                  className={`
                    py-4 px-1 border-b-2 font-medium text-sm transition-colors
                    ${
                      location.pathname === item.path
                        ? 'border-blue-500 text-blue-600'
                        : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                    }
                  `}
                >
                  {item.name}
                </Link>
              ))}
            </div>
          </nav>
        </header>

        <main className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
          <Routes>
            <Route path="/" element={<HomePage />} />
            <Route path="/reports" element={<ReportsPage />} />
            <Route path="/reports/new" element={<NewReportPage />} />
            <Route path="/reports/:reportId" element={<ReportViewPage />} />
            <Route path="/certifications" element={<CertificationsPage />} />
            <Route path="/documents" element={<DocumentsPage />} />
            <Route path="/finance" element={<FinancePage />} />
            <Route path="/logistics" element={<LogisticsPage />} />
          </Routes>
        </main>

        <footer className="bg-white border-t border-gray-200 mt-12">
          <div className="max-w-7xl mx-auto py-6 px-4 sm:px-6 lg:px-8">
            <p className="text-center text-sm text-gray-500">
              © 2024 ExportSathi. Helping Indian MSMEs start exporting in 7 days.
            </p>
          </div>
        </footer>
      </div>
    </ErrorBoundary>
  );
}

export default App;
