/**
 * ReportViewPage
 * 
 * Page for viewing a generated export readiness report
 * Fetches and displays the report using ReportDisplay component
 */

import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ReportDisplay } from '../components/ReportDisplay';
import { api } from '../services/api';
import type { ExportReadinessReport } from '../types';

export const ReportViewPage: React.FC = () => {
  const { reportId } = useParams<{ reportId: string }>();
  const navigate = useNavigate();
  
  const [report, setReport] = useState<ExportReadinessReport | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchReport = async () => {
      if (!reportId) {
        setError('No report ID provided');
        setIsLoading(false);
        return;
      }

      try {
        setIsLoading(true);
        setError(null);
        
        const response = await api.getReport(reportId);
        setReport(response.data.report);
      } catch (err: any) {
        console.error('Error fetching report:', err);
        
        if (err.response?.status === 404) {
          setError('Report not found. It may have been deleted or the ID is incorrect.');
        } else if (err.response?.data?.error) {
          setError(err.response.data.error);
        } else if (err.message) {
          setError(err.message);
        } else {
          setError('Failed to load report. Please try again.');
        }
      } finally {
        setIsLoading(false);
      }
    };

    fetchReport();
  }, [reportId]);

  return (
    <div className="max-w-6xl mx-auto px-4 py-8">
      {/* Header */}
      <div className="mb-6">
        <button
          onClick={() => navigate('/reports')}
          className="text-blue-600 hover:text-blue-800 flex items-center mb-4"
        >
          <svg className="w-5 h-5 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
          </svg>
          Back to Reports
        </button>
      </div>

      {/* Report Display */}
      <ReportDisplay
        report={report}
        isLoading={isLoading}
        error={error || undefined}
      />

      {/* Action Buttons */}
      {report && !isLoading && !error && (
        <div className="mt-8 flex flex-wrap gap-4">
          <button
            onClick={() => navigate(`/reports/${reportId}/action-plan`)}
            className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-medium"
          >
            View 7-Day Action Plan
          </button>
          
          <button
            onClick={() => navigate(`/reports/${reportId}/chat`)}
            className="px-6 py-3 bg-white border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors font-medium"
          >
            Ask Questions (Chat)
          </button>
          
          <button
            onClick={() => navigate(`/documents/generate?reportId=${reportId}`)}
            className="px-6 py-3 bg-white border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors font-medium"
          >
            Generate Documents
          </button>
          
          <button
            onClick={() => window.print()}
            className="px-6 py-3 bg-white border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors font-medium"
          >
            Print Report
          </button>
        </div>
      )}
    </div>
  );
};
