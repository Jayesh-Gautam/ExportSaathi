/**
 * HSCodeSection Component
 * 
 * Displays HS code prediction with confidence indicator
 * 
 * Requirements: 2.1
 */

import React from 'react';

interface HSCodeSectionProps {
  hsCode: {
    code: string;
    confidence: number;
    description: string;
    alternatives?: Array<{ code: string; confidence: number }>;
  };
}

export const HSCodeSection: React.FC<HSCodeSectionProps> = ({ hsCode }) => {
  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 85) return 'text-green-600 bg-green-100';
    if (confidence >= 70) return 'text-yellow-600 bg-yellow-100';
    return 'text-red-600 bg-red-100';
  };

  const getConfidenceLabel = (confidence: number) => {
    if (confidence >= 85) return 'High Confidence';
    if (confidence >= 70) return 'Medium Confidence';
    return 'Low Confidence - Verification Recommended';
  };

  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <h2 className="text-2xl font-bold text-gray-900 mb-4">HS Code Classification</h2>
      
      <div className="flex items-center justify-between mb-4">
        <div>
          <p className="text-sm text-gray-600 mb-1">Predicted HS Code</p>
          <p className="text-3xl font-bold text-blue-600">{hsCode.code}</p>
        </div>
        <div className={`px-4 py-2 rounded-full ${getConfidenceColor(hsCode.confidence)}`}>
          <p className="text-sm font-semibold">{hsCode.confidence}%</p>
          <p className="text-xs">{getConfidenceLabel(hsCode.confidence)}</p>
        </div>
      </div>

      <p className="text-gray-700 mb-4">{hsCode.description}</p>

      {hsCode.confidence < 70 && (
        <div className="bg-yellow-50 border-l-4 border-yellow-400 p-4 mb-4">
          <div className="flex">
            <div className="flex-shrink-0">
              <svg className="h-5 w-5 text-yellow-400" viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
              </svg>
            </div>
            <div className="ml-3">
              <p className="text-sm text-yellow-700">
                <strong>Verification Recommended:</strong> The confidence level is below 70%. 
                Please verify this HS code with a customs broker or trade consultant before proceeding.
              </p>
            </div>
          </div>
        </div>
      )}

      {hsCode.alternatives && hsCode.alternatives.length > 0 && (
        <div className="mt-4">
          <h3 className="text-lg font-semibold text-gray-900 mb-2">Alternative HS Codes</h3>
          <div className="space-y-2">
            {hsCode.alternatives.map((alt, index) => (
              <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded-md">
                <span className="font-mono text-gray-900">{alt.code}</span>
                <span className="text-sm text-gray-600">{alt.confidence}% confidence</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default HSCodeSection;
