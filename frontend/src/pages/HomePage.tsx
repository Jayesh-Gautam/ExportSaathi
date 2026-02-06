/**
 * HomePage Component
 * 
 * Main page with query form and report display
 * Simplified MVP focusing on core report generation flow
 */

import React, { useState } from 'react';
import QueryForm from '../components/QueryForm';
import ReportDisplay from '../components/ReportDisplay';
import { ErrorBoundary } from '../components/common/ErrorBoundary';
import { LoadingSpinner } from '../components/common/LoadingSpinner';
import { useApi } from '../hooks/useApi';
import { api, ExportReadinessReport, QueryInput } from '../services/api';

export const HomePage: React.FC = () => {
  const [report, setReport] = useState<ExportReadinessReport | null>(null);
  const { loading, error, execute } = useApi(api.generateReport.bind(api));

  const handleQuerySubmit = async (query: QueryInput) => {
    const result = await execute(query);
    if (result) {
      setReport(result);
    }
  };

  return (
    <ErrorBoundary>
      <div className="min-h-screen bg-gray-50">
        {/* Header */}
        <header className="bg-white shadow-sm">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
            <div className="flex items-center justify-between">
              <div>
                <h1 className="text-3xl font-bold text-blue-600">ExportSathi</h1>
                <p className="text-sm text-gray-600 mt-1">
                  AI-Powered Export Compliance & Certification Co-Pilot
                </p>
              </div>
              <div className="text-right">
                <p className="text-sm font-medium text-gray-900">Start Exporting in 7 Days</p>
                <p className="text-xs text-gray-500">For Indian MSMEs</p>
              </div>
            </div>
          </div>
        </header>

        {/* Main Content */}
        <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          {!report && !loading && (
            <div className="mb-8">
              <h2 className="text-2xl font-bold text-gray-900 mb-2">
                Get Your Export Readiness Report
              </h2>
              <p className="text-gray-600 mb-6">
                Enter your product details to receive a comprehensive analysis of export requirements,
                certifications, costs, and timeline.
              </p>
              <QueryForm onSubmit={handleQuerySubmit} />
            </div>
          )}

          {loading && (
            <div className="bg-white rounded-lg shadow-md p-8">
              <LoadingSpinner
                message="Generating your export readiness report..."
                estimatedTime={30}
              />
              <div className="mt-6 text-center">
                <p className="text-sm text-gray-600">
                  We're analyzing your product, identifying required certifications,
                  calculating risks, and creating your personalized action plan.
                </p>
              </div>
            </div>
          )}

          {error && (
            <div className="bg-red-50 border-l-4 border-red-400 p-4 mb-6">
              <div className="flex">
                <div className="flex-shrink-0">
                  <svg className="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                  </svg>
                </div>
                <div className="ml-3">
                  <h3 className="text-sm font-medium text-red-800">Error Generating Report</h3>
                  <p className="mt-2 text-sm text-red-700">{error}</p>
                  <button
                    onClick={() => setReport(null)}
                    className="mt-3 text-sm font-medium text-red-800 hover:text-red-900"
                  >
                    Try Again →
                  </button>
                </div>
              </div>
            </div>
          )}

          {report && !loading && (
            <div>
              <div className="mb-6 flex items-center justify-between">
                <div>
                  <h2 className="text-2xl font-bold text-gray-900">Your Export Readiness Report</h2>
                  <p className="text-sm text-gray-600 mt-1">
                    Generated on {new Date(report.generated_at).toLocaleDateString()}
                  </p>
                </div>
                <button
                  onClick={() => setReport(null)}
                  className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
                >
                  New Query
                </button>
              </div>
              <ReportDisplay report={report} businessType="Manufacturing" />
            </div>
          )}
        </main>

        {/* Footer */}
        <footer className="bg-white border-t border-gray-200 mt-12">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
            <p className="text-center text-sm text-gray-500">
              ExportSathi provides guidance only and does not issue certificates, approvals, or financing.
              Always verify information with official authorities.
            </p>
          </div>
        </footer>
      </div>
    </ErrorBoundary>
  );
};

export default HomePage;
