/**
 * NewReportPage
 * 
 * Page for creating a new export readiness report
 * Contains the QueryForm and handles report generation
 */

import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { QueryForm } from '../components/QueryForm';
import { api } from '../services/api';
import type { GenerateReportResponse } from '../types/api';

export const NewReportPage: React.FC = () => {
  const navigate = useNavigate();
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (formData: FormData) => {
    setIsLoading(true);
    setError(null);

    try {
      const response = await api.generateReport(formData);
      const data: GenerateReportResponse = response.data;

      if (data.status === 'completed' && data.reportId) {
        // Navigate to the report page
        navigate(`/reports/${data.reportId}`);
      } else if (data.status === 'processing') {
        // Navigate to status page if processing
        navigate(`/reports/${data.reportId}/status`);
      } else {
        setError('Failed to generate report. Please try again.');
      }
    } catch (err: any) {
      console.error('Error generating report:', err);
      
      if (err.response?.data?.detail) {
        // Handle validation errors
        if (Array.isArray(err.response.data.detail)) {
          const errorMessages = err.response.data.detail
            .map((e: any) => e.msg)
            .join(', ');
          setError(`Validation error: ${errorMessages}`);
        } else {
          setError(err.response.data.detail);
        }
      } else if (err.response?.data?.error) {
        setError(err.response.data.error);
      } else if (err.message) {
        setError(err.message);
      } else {
        setError('An unexpected error occurred. Please try again.');
      }
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto px-4 py-8">
      {/* Header */}
      <div className="mb-8">
        <button
          onClick={() => navigate('/')}
          className="text-blue-600 hover:text-blue-800 flex items-center mb-4"
        >
          <svg className="w-5 h-5 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
          </svg>
          Back to Home
        </button>
        
        <h1 className="text-3xl font-bold text-gray-900 mb-2">
          Export Readiness Assessment
        </h1>
        <p className="text-gray-600">
          Tell us about your product and destination to get a comprehensive export readiness report
        </p>
      </div>

      {/* Error Display */}
      {error && (
        <div className="mb-6 bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg flex items-start">
          <svg className="w-5 h-5 mr-3 flex-shrink-0 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
          </svg>
          <div>
            <p className="font-medium">Error generating report</p>
            <p className="text-sm mt-1">{error}</p>
          </div>
        </div>
      )}

      {/* Form Card */}
      <div className="bg-white rounded-lg shadow-lg p-6 md:p-8">
        <QueryForm onSubmit={handleSubmit} isLoading={isLoading} />
      </div>

      {/* Help Section */}
      <div className="mt-8 bg-gray-50 rounded-lg p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-3">
          Need Help?
        </h2>
        <div className="space-y-2 text-sm text-gray-600">
          <p>
            <strong>Product Name:</strong> Enter the common name of your product (e.g., "Organic Turmeric Powder", "LED Bulbs")
          </p>
          <p>
            <strong>Product Image:</strong> Upload a clear image of your product. This helps our AI predict the correct HS code.
          </p>
          <p>
            <strong>Ingredients/BOM:</strong> List the main ingredients or components. This helps identify restricted substances.
          </p>
          <p>
            <strong>Destination Country:</strong> Select where you want to export. Different countries have different requirements.
          </p>
        </div>
      </div>
    </div>
  );
};
