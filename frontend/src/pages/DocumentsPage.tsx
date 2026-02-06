import React from 'react';

export const DocumentsPage: React.FC = () => {
  return (
    <div className="px-4 py-6">
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-2xl font-bold text-gray-900 mb-4">
          Smart Documentation Layer
        </h2>
        <p className="text-gray-600 mb-6">
          Auto-generate and validate all export documents with AI-powered error checking.
        </p>

        <div className="space-y-4 mb-6">
          <div className="border-l-4 border-blue-500 bg-blue-50 p-4">
            <h3 className="font-semibold text-gray-900 mb-1">Commercial Invoice</h3>
            <p className="text-sm text-gray-600">
              Generate India-specific commercial invoices with automatic validation
            </p>
          </div>
          <div className="border-l-4 border-green-500 bg-green-50 p-4">
            <h3 className="font-semibold text-gray-900 mb-1">Packing List</h3>
            <p className="text-sm text-gray-600">
              Create detailed packing lists compliant with customs requirements
            </p>
          </div>
          <div className="border-l-4 border-purple-500 bg-purple-50 p-4">
            <h3 className="font-semibold text-gray-900 mb-1">Shipping Bill</h3>
            <p className="text-sm text-gray-600">
              Generate shipping bills with port code validation
            </p>
          </div>
          <div className="border-l-4 border-yellow-500 bg-yellow-50 p-4">
            <h3 className="font-semibold text-gray-900 mb-1">GST LUT</h3>
            <p className="text-sm text-gray-600">
              Letter of Undertaking for GST-free exports with refund rejection guard
            </p>
          </div>
          <div className="border-l-4 border-red-500 bg-red-50 p-4">
            <h3 className="font-semibold text-gray-900 mb-1">SOFTEX</h3>
            <p className="text-sm text-gray-600">
              Software export declaration for SaaS and service exporters
            </p>
          </div>
          <div className="border-l-4 border-indigo-500 bg-indigo-50 p-4">
            <h3 className="font-semibold text-gray-900 mb-1">Certificate of Origin</h3>
            <p className="text-sm text-gray-600">
              Generate certificates of origin for preferential trade agreements
            </p>
          </div>
        </div>

        <div className="bg-gray-50 rounded-lg p-4 mb-6">
          <h3 className="font-semibold text-gray-900 mb-2">AI Validation Features:</h3>
          <ul className="space-y-1 text-sm text-gray-600">
            <li>✓ Port code mismatch detection</li>
            <li>✓ Invoice format validation</li>
            <li>✓ GST vs Shipping Bill matching</li>
            <li>✓ RMS risk trigger detection</li>
            <li>✓ GST refund rejection guard</li>
          </ul>
        </div>

        <div className="mt-6 p-4 bg-blue-50 rounded-md">
          <p className="text-sm text-blue-800">
            <strong>Coming soon:</strong> Full document generation and validation functionality
          </p>
        </div>
      </div>
    </div>
  );
};
