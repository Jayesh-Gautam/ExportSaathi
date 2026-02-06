import React from 'react';

export const ReportsPage: React.FC = () => {
  return (
    <div className="px-4 py-6">
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-2xl font-bold text-gray-900 mb-4">
          Export Readiness Reports
        </h2>
        <p className="text-gray-600">
          View and manage your export readiness reports. This page will display:
        </p>
        <ul className="mt-4 space-y-2 text-gray-600">
          <li className="flex items-start">
            <span className="mr-2">•</span>
            List of all generated reports
          </li>
          <li className="flex items-start">
            <span className="mr-2">•</span>
            Report details including HS code, certifications, and compliance roadmap
          </li>
          <li className="flex items-start">
            <span className="mr-2">•</span>
            Risk scores and cost estimates
          </li>
          <li className="flex items-start">
            <span className="mr-2">•</span>
            7-day action plan with progress tracking
          </li>
        </ul>
        <div className="mt-6 p-4 bg-blue-50 rounded-md">
          <p className="text-sm text-blue-800">
            <strong>Coming soon:</strong> Full report generation and management functionality
          </p>
        </div>
      </div>
    </div>
  );
};
