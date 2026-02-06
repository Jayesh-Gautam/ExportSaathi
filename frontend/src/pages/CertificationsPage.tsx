import React from 'react';

export const CertificationsPage: React.FC = () => {
  return (
    <div className="px-4 py-6">
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-2xl font-bold text-gray-900 mb-4">
          Certification Navigator
        </h2>
        <p className="text-gray-600 mb-6">
          Get step-by-step guidance for obtaining required certifications for your export products.
        </p>

        <div className="grid md:grid-cols-2 gap-4 mb-6">
          <div className="border border-gray-200 rounded-lg p-4">
            <h3 className="font-semibold text-gray-900 mb-2">US FDA</h3>
            <p className="text-sm text-gray-600">
              Food and Drug Administration certification for food, medical devices, and cosmetics
            </p>
          </div>
          <div className="border border-gray-200 rounded-lg p-4">
            <h3 className="font-semibold text-gray-900 mb-2">CE Marking</h3>
            <p className="text-sm text-gray-600">
              European conformity marking for products sold in the European Economic Area
            </p>
          </div>
          <div className="border border-gray-200 rounded-lg p-4">
            <h3 className="font-semibold text-gray-900 mb-2">REACH</h3>
            <p className="text-sm text-gray-600">
              EU regulation for chemical substances in products
            </p>
          </div>
          <div className="border border-gray-200 rounded-lg p-4">
            <h3 className="font-semibold text-gray-900 mb-2">BIS</h3>
            <p className="text-sm text-gray-600">
              Bureau of Indian Standards certification for quality assurance
            </p>
          </div>
          <div className="border border-gray-200 rounded-lg p-4">
            <h3 className="font-semibold text-gray-900 mb-2">ZED</h3>
            <p className="text-sm text-gray-600">
              Zero Defect Zero Effect certification with 80% subsidy for micro enterprises
            </p>
          </div>
          <div className="border border-gray-200 rounded-lg p-4">
            <h3 className="font-semibold text-gray-900 mb-2">SOFTEX</h3>
            <p className="text-sm text-gray-600">
              Software export declaration for SaaS and service exporters
            </p>
          </div>
        </div>

        <div className="mt-6 p-4 bg-blue-50 rounded-md">
          <p className="text-sm text-blue-800">
            <strong>Coming soon:</strong> Detailed certification guidance with document checklists, test labs, consultants, and subsidies
          </p>
        </div>
      </div>
    </div>
  );
};
