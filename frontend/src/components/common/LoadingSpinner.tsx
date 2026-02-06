/**
 * LoadingSpinner Component
 * 
 * Displays loading spinner with optional message and estimated time
 * 
 * Requirements: 15.5
 */

import React from 'react';

interface LoadingSpinnerProps {
  message?: string;
  estimatedTime?: number;
}

export const LoadingSpinner: React.FC<LoadingSpinnerProps> = ({
  message = 'Loading...',
  estimatedTime,
}) => {
  return (
    <div className="flex flex-col items-center justify-center p-8">
      <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-blue-600"></div>
      <p className="mt-4 text-gray-700 font-medium">{message}</p>
      {estimatedTime && (
        <p className="mt-2 text-sm text-gray-500">
          Estimated time: {estimatedTime} seconds
        </p>
      )}
    </div>
  );
};

export default LoadingSpinner;
