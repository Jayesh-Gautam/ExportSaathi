import React from 'react';

interface LoadingSpinnerProps {
  message?: string;
  estimatedTime?: number;
}

export const LoadingSpinner: React.FC<LoadingSpinnerProps> = ({ 
  message = 'Loading...', 
  estimatedTime 
}) => {
  return (
    <div className="flex flex-col items-center justify-center p-8">
      <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      <p className="mt-4 text-gray-600 text-sm">{message}</p>
      {estimatedTime && (
        <p className="mt-2 text-gray-500 text-xs">
          Estimated time: {estimatedTime} seconds
        </p>
      )}
    </div>
  );
};
