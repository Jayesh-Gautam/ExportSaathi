import React from 'react';

export const FinancePage: React.FC = () => {
  return (
    <div className="px-4 py-6">
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-2xl font-bold text-gray-900 mb-4">
          Finance Readiness Module
        </h2>
        <p className="text-gray-600 mb-6">
          Plan your working capital, understand RoDTEP benefits, and assess credit eligibility.
        </p>

        <div className="grid md:grid-cols-2 gap-6 mb-6">
          <div className="bg-gradient-to-br from-blue-50 to-blue-100 rounded-lg p-6">
            <div className="flex items-center mb-3">
              <svg className="w-8 h-8 text-blue-600 mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <h3 className="text-lg font-semibold text-gray-900">
                Working Capital Planning
              </h3>
            </div>
            <p className="text-sm text-gray-700">
              Calculate total working capital requirements including product costs, certification fees, logistics, and documentation expenses.
            </p>
          </div>

          <div className="bg-gradient-to-br from-green-50 to-green-100 rounded-lg p-6">
            <div className="flex items-center mb-3">
              <svg className="w-8 h-8 text-green-600 mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 7h6m0 10v-3m-3 3h.01M9 17h.01M9 14h.01M12 14h.01M15 11h.01M12 11h.01M9 11h.01M7 21h10a2 2 0 002-2V5a2 2 0 00-2-2H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
              </svg>
              <h3 className="text-lg font-semibold text-gray-900">
                RoDTEP Calculator
              </h3>
            </div>
            <p className="text-sm text-gray-700">
              Calculate Remission of Duties and Taxes on Exported Products benefits based on your HS code and destination country.
            </p>
          </div>

          <div className="bg-gradient-to-br from-purple-50 to-purple-100 rounded-lg p-6">
            <div className="flex items-center mb-3">
              <svg className="w-8 h-8 text-purple-600 mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 10h18M7 15h1m4 0h1m-7 4h12a3 3 0 003-3V8a3 3 0 00-3-3H6a3 3 0 00-3 3v8a3 3 0 003 3z" />
              </svg>
              <h3 className="text-lg font-semibold text-gray-900">
                Pre-Shipment Credit
              </h3>
            </div>
            <p className="text-sm text-gray-700">
              Assess your eligibility for pre-shipment credit based on company size, order value, and banking relationships.
            </p>
          </div>

          <div className="bg-gradient-to-br from-yellow-50 to-yellow-100 rounded-lg p-6">
            <div className="flex items-center mb-3">
              <svg className="w-8 h-8 text-yellow-600 mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
              </svg>
              <h3 className="text-lg font-semibold text-gray-900">
                Currency Hedging
              </h3>
            </div>
            <p className="text-sm text-gray-700">
              Get recommendations for currency hedging strategies to manage foreign exchange risk.
            </p>
          </div>
        </div>

        <div className="bg-gray-50 rounded-lg p-6 mb-6">
          <h3 className="font-semibold text-gray-900 mb-3">Cash Flow Timeline</h3>
          <p className="text-sm text-gray-600 mb-4">
            Visualize when expenses occur and when refunds/payments are expected to identify liquidity gaps.
          </p>
          <div className="bg-white rounded border border-gray-200 p-4">
            <p className="text-sm text-gray-500 text-center">
              Interactive cash flow timeline will be displayed here
            </p>
          </div>
        </div>

        <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
          <h3 className="font-semibold text-red-900 mb-2">
            ⚠️ Avoid the Liquidity-Compliance Trap
          </h3>
          <p className="text-sm text-red-800">
            Many MSMEs fail due to cash flow issues while waiting for GST refunds and certifications. Our finance module helps you plan ahead and secure necessary financing.
          </p>
        </div>

        <div className="mt-6 p-4 bg-blue-50 rounded-md">
          <p className="text-sm text-blue-800">
            <strong>Coming soon:</strong> Full finance analysis with interactive cash flow timeline and bank referral programs
          </p>
        </div>
      </div>
    </div>
  );
};
