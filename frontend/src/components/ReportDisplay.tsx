/**
 * ReportDisplay Component
 * 
 * Main container for displaying the comprehensive export readiness report
 * Includes expandable sections for HS code, certifications, roadmap, risks, costs, and action plan
 */

import React, { useState } from 'react';
import type { ExportReadinessReport } from '../types';
import { LoadingSpinner } from './common';

interface ReportDisplayProps {
  report: ExportReadinessReport | null;
  isLoading?: boolean;
  error?: string;
}

export const ReportDisplay: React.FC<ReportDisplayProps> = ({
  report,
  isLoading = false,
  error,
}) => {
  const [expandedSections, setExpandedSections] = useState<Set<string>>(
    new Set(['hsCode', 'certifications'])
  );

  const toggleSection = (sectionId: string) => {
    setExpandedSections(prev => {
      const newSet = new Set(prev);
      if (newSet.has(sectionId)) {
        newSet.delete(sectionId);
      } else {
        newSet.add(sectionId);
      }
      return newSet;
    });
  };

  // Loading state
  if (isLoading) {
    return (
      <div className="flex flex-col items-center justify-center py-16">
        <LoadingSpinner message="Generating your export readiness report..." />
        <div className="mt-6 text-center max-w-md">
          <p className="text-gray-600 mb-2">This may take up to 30 seconds</p>
          <div className="text-sm text-gray-500 space-y-1">
            <p>• Analyzing product and predicting HS code</p>
            <p>• Identifying required certifications</p>
            <p>• Calculating compliance costs and timeline</p>
            <p>• Generating action plan</p>
          </div>
        </div>
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-6">
        <div className="flex items-start">
          <svg
            className="w-6 h-6 text-red-600 mr-3 flex-shrink-0"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
            />
          </svg>
          <div>
            <h3 className="text-lg font-semibold text-red-900 mb-2">
              Report Generation Failed
            </h3>
            <p className="text-red-700">{error}</p>
            <button
              onClick={() => window.location.reload()}
              className="mt-4 px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 transition-colors"
            >
              Try Again
            </button>
          </div>
        </div>
      </div>
    );
  }

  // No report state
  if (!report) {
    return (
      <div className="text-center py-16">
        <svg
          className="mx-auto h-16 w-16 text-gray-400 mb-4"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
          />
        </svg>
        <h3 className="text-lg font-medium text-gray-900 mb-2">
          No Report Available
        </h3>
        <p className="text-gray-600">
          Submit a product query to generate your export readiness report
        </p>
      </div>
    );
  }

  // Format date
  const formattedDate = new Date(report.generatedAt).toLocaleDateString('en-IN', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });

  return (
    <div className="space-y-6">
      {/* Report Header */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <div className="flex items-start justify-between">
          <div>
            <h2 className="text-2xl font-bold text-gray-900 mb-2">
              Export Readiness Report
            </h2>
            <div className="flex items-center space-x-4 text-sm text-gray-600">
              <span>Report ID: {report.reportId}</span>
              <span>•</span>
              <span>Generated: {formattedDate}</span>
              <span>•</span>
              <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                report.status === 'completed'
                  ? 'bg-green-100 text-green-800'
                  : report.status === 'processing'
                  ? 'bg-yellow-100 text-yellow-800'
                  : 'bg-red-100 text-red-800'
              }`}>
                {report.status.toUpperCase()}
              </span>
            </div>
          </div>
          
          {/* Risk Score Badge */}
          <div className="text-center">
            <div className={`inline-flex items-center justify-center w-20 h-20 rounded-full text-2xl font-bold ${
              report.riskScore >= 70
                ? 'bg-red-100 text-red-700'
                : report.riskScore >= 40
                ? 'bg-yellow-100 text-yellow-700'
                : 'bg-green-100 text-green-700'
            }`}>
              {report.riskScore}
            </div>
            <p className="text-xs text-gray-600 mt-1">Risk Score</p>
          </div>
        </div>
      </div>

      {/* Quick Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <SummaryCard
          title="HS Code"
          value={report.hsCode.code}
          subtitle={`${report.hsCode.confidence}% confidence`}
          icon="🏷️"
        />
        <SummaryCard
          title="Certifications"
          value={report.certifications.length.toString()}
          subtitle={`${report.certifications.filter(c => c.mandatory).length} mandatory`}
          icon="📋"
        />
        <SummaryCard
          title="Timeline"
          value={`${report.timeline.estimatedDays} days`}
          subtitle="Estimated duration"
          icon="⏱️"
        />
        <SummaryCard
          title="Total Cost"
          value={`₹${report.costs.total.toLocaleString('en-IN')}`}
          subtitle={report.costs.currency}
          icon="💰"
        />
      </div>

      {/* Expandable Sections */}
      <div className="space-y-4">
        {/* HS Code Section */}
        <ExpandableSection
          id="hsCode"
          title="HS Code Prediction"
          isExpanded={expandedSections.has('hsCode')}
          onToggle={() => toggleSection('hsCode')}
          badge={`${report.hsCode.confidence}%`}
        >
          <div className="space-y-4">
            <div className="flex items-start space-x-4">
              <div className="flex-1">
                <div className="text-3xl font-bold text-gray-900 mb-2">
                  {report.hsCode.code}
                </div>
                <p className="text-gray-700">{report.hsCode.description}</p>
                
                {/* Confidence Indicator */}
                <div className="mt-4">
                  <div className="flex items-center justify-between text-sm mb-1">
                    <span className="text-gray-600">Confidence Level</span>
                    <span className="font-medium">{report.hsCode.confidence}%</span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div
                      className={`h-2 rounded-full ${
                        report.hsCode.confidence >= 70
                          ? 'bg-green-500'
                          : 'bg-yellow-500'
                      }`}
                      style={{ width: `${report.hsCode.confidence}%` }}
                    />
                  </div>
                </div>

                {/* Alternative Codes */}
                {report.hsCode.alternatives && report.hsCode.alternatives.length > 0 && (
                  <div className="mt-4">
                    <h4 className="text-sm font-medium text-gray-900 mb-2">
                      Alternative HS Codes
                    </h4>
                    <div className="space-y-2">
                      {report.hsCode.alternatives.map((alt, idx) => (
                        <div
                          key={idx}
                          className="flex items-center justify-between p-3 bg-gray-50 rounded-md"
                        >
                          <div>
                            <span className="font-medium text-gray-900">{alt.code}</span>
                            <p className="text-sm text-gray-600">{alt.description}</p>
                          </div>
                          <span className="text-sm text-gray-500">
                            {alt.confidence}%
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        </ExpandableSection>

        {/* Certifications Section */}
        <ExpandableSection
          id="certifications"
          title="Required Certifications"
          isExpanded={expandedSections.has('certifications')}
          onToggle={() => toggleSection('certifications')}
          badge={`${report.certifications.length} total`}
        >
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {report.certifications.map((cert) => (
              <div
                key={cert.id}
                className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow"
              >
                <div className="flex items-start justify-between mb-2">
                  <h4 className="font-semibold text-gray-900">{cert.name}</h4>
                  <span className={`px-2 py-1 rounded text-xs font-medium ${
                    cert.priority === 'high'
                      ? 'bg-red-100 text-red-700'
                      : cert.priority === 'medium'
                      ? 'bg-yellow-100 text-yellow-700'
                      : 'bg-blue-100 text-blue-700'
                  }`}>
                    {cert.priority.toUpperCase()}
                  </span>
                </div>
                
                <div className="space-y-2 text-sm">
                  <div className="flex items-center text-gray-600">
                    <span className={`mr-2 ${cert.mandatory ? 'text-red-600' : 'text-gray-400'}`}>
                      {cert.mandatory ? '● Mandatory' : '○ Optional'}
                    </span>
                  </div>
                  
                  <div className="flex items-center text-gray-600">
                    <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                    ₹{cert.estimatedCost.min.toLocaleString('en-IN')} - ₹{cert.estimatedCost.max.toLocaleString('en-IN')}
                  </div>
                  
                  <div className="flex items-center text-gray-600">
                    <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                    {cert.estimatedTimelineDays} days
                  </div>
                </div>
                
                <button className="mt-3 w-full px-3 py-2 bg-blue-50 text-blue-700 rounded-md hover:bg-blue-100 transition-colors text-sm font-medium">
                  View Details
                </button>
              </div>
            ))}
          </div>
        </ExpandableSection>

        {/* Compliance Roadmap Section */}
        <ExpandableSection
          id="roadmap"
          title="Compliance Roadmap"
          isExpanded={expandedSections.has('roadmap')}
          onToggle={() => toggleSection('roadmap')}
          badge={`${report.complianceRoadmap.length} steps`}
        >
          <div className="space-y-4">
            {report.complianceRoadmap.map((step, idx) => (
              <div key={idx} className="flex">
                <div className="flex flex-col items-center mr-4">
                  <div className="flex items-center justify-center w-8 h-8 rounded-full bg-blue-100 text-blue-700 font-semibold text-sm">
                    {step.step}
                  </div>
                  {idx < report.complianceRoadmap.length - 1 && (
                    <div className="w-0.5 h-full bg-blue-200 mt-2" />
                  )}
                </div>
                <div className="flex-1 pb-8">
                  <h4 className="font-semibold text-gray-900 mb-1">{step.title}</h4>
                  <p className="text-gray-600 text-sm mb-2">{step.description}</p>
                  <div className="flex items-center space-x-4 text-xs text-gray-500">
                    <span>Duration: {step.durationDays} days</span>
                    {step.dependencies.length > 0 && (
                      <>
                        <span>•</span>
                        <span>Depends on: {step.dependencies.join(', ')}</span>
                      </>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </ExpandableSection>

        {/* Risks Section */}
        <ExpandableSection
          id="risks"
          title="Identified Risks"
          isExpanded={expandedSections.has('risks')}
          onToggle={() => toggleSection('risks')}
          badge={`${report.risks.length} risks`}
        >
          <div className="space-y-3">
            {report.risks.map((risk, idx) => (
              <div
                key={idx}
                className={`border-l-4 p-4 rounded-r-lg ${
                  risk.severity === 'high'
                    ? 'border-red-500 bg-red-50'
                    : risk.severity === 'medium'
                    ? 'border-yellow-500 bg-yellow-50'
                    : 'border-blue-500 bg-blue-50'
                }`}
              >
                <div className="flex items-start justify-between mb-2">
                  <h4 className="font-semibold text-gray-900">{risk.title}</h4>
                  <span className={`px-2 py-1 rounded text-xs font-medium ${
                    risk.severity === 'high'
                      ? 'bg-red-100 text-red-700'
                      : risk.severity === 'medium'
                      ? 'bg-yellow-100 text-yellow-700'
                      : 'bg-blue-100 text-blue-700'
                  }`}>
                    {risk.severity.toUpperCase()}
                  </span>
                </div>
                <p className="text-gray-700 text-sm mb-2">{risk.description}</p>
                <div className="bg-white bg-opacity-50 rounded p-3 mt-2">
                  <p className="text-xs font-medium text-gray-700 mb-1">Mitigation:</p>
                  <p className="text-sm text-gray-600">{risk.mitigation}</p>
                </div>
              </div>
            ))}
          </div>
        </ExpandableSection>

        {/* Cost Breakdown Section */}
        <ExpandableSection
          id="costs"
          title="Cost Breakdown"
          isExpanded={expandedSections.has('costs')}
          onToggle={() => toggleSection('costs')}
          badge={`₹${report.costs.total.toLocaleString('en-IN')}`}
        >
          <div className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <CostCard
                title="Certifications"
                amount={report.costs.certifications}
                currency={report.costs.currency}
                icon="📋"
              />
              <CostCard
                title="Documentation"
                amount={report.costs.documentation}
                currency={report.costs.currency}
                icon="📄"
              />
              <CostCard
                title="Logistics"
                amount={report.costs.logistics}
                currency={report.costs.currency}
                icon="🚢"
              />
            </div>
            
            <div className="border-t border-gray-200 pt-4">
              <div className="flex items-center justify-between text-lg font-semibold">
                <span>Total Estimated Cost</span>
                <span className="text-blue-600">
                  ₹{report.costs.total.toLocaleString('en-IN')} {report.costs.currency}
                </span>
              </div>
            </div>

            {/* Subsidies */}
            {report.subsidies && report.subsidies.length > 0 && (
              <div className="bg-green-50 border border-green-200 rounded-lg p-4 mt-4">
                <h4 className="font-semibold text-green-900 mb-3">
                  Available Subsidies & Benefits
                </h4>
                <div className="space-y-2">
                  {report.subsidies.map((subsidy, idx) => (
                    <div key={idx} className="flex items-start justify-between">
                      <div className="flex-1">
                        <p className="font-medium text-green-900">{subsidy.name}</p>
                        <p className="text-sm text-green-700">{subsidy.eligibility}</p>
                      </div>
                      <span className="text-green-700 font-semibold ml-4">
                        {subsidy.percentage}% (₹{subsidy.amount.toLocaleString('en-IN')})
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </ExpandableSection>

        {/* Timeline Section */}
        <ExpandableSection
          id="timeline"
          title="Timeline"
          isExpanded={expandedSections.has('timeline')}
          onToggle={() => toggleSection('timeline')}
          badge={`${report.timeline.estimatedDays} days`}
        >
          <div className="space-y-4">
            <div className="text-center py-4">
              <div className="text-4xl font-bold text-blue-600 mb-2">
                {report.timeline.estimatedDays} Days
              </div>
              <p className="text-gray-600">Estimated time to become export-ready</p>
            </div>
            
            <div className="space-y-3">
              {report.timeline.breakdown.map((phase, idx) => (
                <div key={idx} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                  <span className="font-medium text-gray-900">{phase.phase}</span>
                  <span className="text-gray-600">{phase.durationDays} days</span>
                </div>
              ))}
            </div>
          </div>
        </ExpandableSection>
      </div>

      {/* Action Items Footer */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-blue-900 mb-3">
          Next Steps
        </h3>
        <ul className="space-y-2 text-blue-800">
          <li className="flex items-start">
            <span className="mr-2">1.</span>
            <span>Review the 7-day action plan below</span>
          </li>
          <li className="flex items-start">
            <span className="mr-2">2.</span>
            <span>Click on certifications to view detailed guidance</span>
          </li>
          <li className="flex items-start">
            <span className="mr-2">3.</span>
            <span>Start with high-priority mandatory certifications</span>
          </li>
          <li className="flex items-start">
            <span className="mr-2">4.</span>
            <span>Use the chat interface for specific questions</span>
          </li>
        </ul>
      </div>
    </div>
  );
};

// Helper Components

interface SummaryCardProps {
  title: string;
  value: string;
  subtitle: string;
  icon: string;
}

const SummaryCard: React.FC<SummaryCardProps> = ({ title, value, subtitle, icon }) => (
  <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
    <div className="flex items-center justify-between mb-2">
      <span className="text-2xl">{icon}</span>
    </div>
    <div className="text-2xl font-bold text-gray-900 mb-1">{value}</div>
    <div className="text-sm text-gray-600">{title}</div>
    <div className="text-xs text-gray-500 mt-1">{subtitle}</div>
  </div>
);

interface ExpandableSectionProps {
  id: string;
  title: string;
  isExpanded: boolean;
  onToggle: () => void;
  badge?: string;
  children: React.ReactNode;
}

const ExpandableSection: React.FC<ExpandableSectionProps> = ({
  title,
  isExpanded,
  onToggle,
  badge,
  children,
}) => (
  <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
    <button
      onClick={onToggle}
      className="w-full flex items-center justify-between p-4 hover:bg-gray-50 transition-colors"
    >
      <div className="flex items-center space-x-3">
        <h3 className="text-lg font-semibold text-gray-900">{title}</h3>
        {badge && (
          <span className="px-2 py-1 bg-blue-100 text-blue-700 rounded-full text-xs font-medium">
            {badge}
          </span>
        )}
      </div>
      <svg
        className={`w-5 h-5 text-gray-500 transition-transform ${
          isExpanded ? 'transform rotate-180' : ''
        }`}
        fill="none"
        stroke="currentColor"
        viewBox="0 0 24 24"
      >
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
      </svg>
    </button>
    {isExpanded && (
      <div className="p-6 border-t border-gray-200">
        {children}
      </div>
    )}
  </div>
);

interface CostCardProps {
  title: string;
  amount: number;
  currency: string;
  icon: string;
}

const CostCard: React.FC<CostCardProps> = ({ title, amount, currency, icon }) => (
  <div className="bg-gray-50 rounded-lg p-4">
    <div className="flex items-center justify-between mb-2">
      <span className="text-2xl">{icon}</span>
    </div>
    <div className="text-xl font-bold text-gray-900 mb-1">
      ₹{amount.toLocaleString('en-IN')}
    </div>
    <div className="text-sm text-gray-600">{title}</div>
    <div className="text-xs text-gray-500 mt-1">{currency}</div>
  </div>
);
