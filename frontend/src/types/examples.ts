/**
 * Usage examples for ExportSathi TypeScript types
 * This file demonstrates how to use the type system effectively
 */

import type {
  QueryInput,
  ExportReadinessReport,
  CertificationGuidance,
  FinanceAnalysis,
  LogisticsRiskAnalysis,
  ChatMessage,
  GenerateReportRequest,
  GenerateReportResponse,
} from './index';

import {
  isExportReadinessReport,
  isCertificationGuidance,
  isFinanceAnalysis,
  validateApiResponse,
  parseApiResponse,
} from './guards';

// ============================================================================
// EXAMPLE 1: Creating a Query Input
// ============================================================================

export function createQueryExample(): QueryInput {
  const query: QueryInput = {
    productName: 'Organic Turmeric Powder',
    destinationCountry: 'United States',
    businessType: 'Manufacturing',
    companySize: 'Small',
    ingredients: '100% organic turmeric',
    bom: 'Turmeric rhizomes, packaging material',
    monthlyVolume: 1000,
    priceRange: '500-1000 INR/kg',
    paymentMode: 'LC',
  };

  return query;
}

// ============================================================================
// EXAMPLE 2: Type-Safe API Call with Validation
// ============================================================================

export async function fetchReportWithValidation(
  reportId: string
): Promise<ExportReadinessReport> {
  const response = await fetch(`/api/reports/${reportId}`);
  
  if (!response.ok) {
    throw new Error(`Failed to fetch report: ${response.statusText}`);
  }

  const json = await response.json();
  
  // Validate the response matches our expected type
  return validateApiResponse(
    json,
    isExportReadinessReport,
    'Invalid report format received from API'
  );
}

// ============================================================================
// EXAMPLE 3: Using parseApiResponse Helper
// ============================================================================

export async function fetchCertificationGuidance(
  certId: string,
  productType: string,
  destination: string
): Promise<CertificationGuidance> {
  const response = await fetch(`/api/certifications/${certId}/guidance`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      productType,
      destinationCountry: destination,
      companySize: 'Small',
    }),
  });

  // parseApiResponse handles both response checking and type validation
  return parseApiResponse(response, isCertificationGuidance);
}

// ============================================================================
// EXAMPLE 4: Working with Report Data
// ============================================================================

export function analyzeReport(report: ExportReadinessReport): void {
  // TypeScript knows all the properties and their types
  console.log(`Report ID: ${report.reportId}`);
  console.log(`HS Code: ${report.hsCode.code} (${report.hsCode.confidence}% confidence)`);
  console.log(`Risk Score: ${report.riskScore}/100`);
  
  // Filter high-priority mandatory certifications
  const criticalCerts = report.certifications.filter(
    cert => cert.mandatory && cert.priority === 'high'
  );
  
  console.log(`Critical certifications: ${criticalCerts.length}`);
  
  // Calculate total cost
  const totalCost = report.costs.total;
  console.log(`Total estimated cost: ${totalCost} ${report.costs.currency}`);
  
  // Check action plan progress
  const progress = report.actionPlan.progressPercentage;
  console.log(`Action plan progress: ${progress}%`);
}

// ============================================================================
// EXAMPLE 5: Type Guards for Unknown Data
// ============================================================================

export function processUnknownData(data: unknown): void {
  if (isExportReadinessReport(data)) {
    // TypeScript now knows data is ExportReadinessReport
    console.log(`Processing report ${data.reportId}`);
    analyzeReport(data);
  } else if (isFinanceAnalysis(data)) {
    // TypeScript now knows data is FinanceAnalysis
    console.log(`Processing finance analysis for ${data.reportId}`);
    console.log(`Working capital: ${data.workingCapital.total}`);
  } else {
    console.error('Unknown data type received');
  }
}

// ============================================================================
// EXAMPLE 6: Generating Documents with Type Safety
// ============================================================================

export async function generateInvoice(
  reportId: string,
  customData?: Record<string, unknown>
): Promise<void> {
  const request = {
    documentType: 'commercial_invoice' as const, // Type-safe document type
    reportId,
    customData: customData || {},
  };

  const response = await fetch('/api/documents/generate', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    throw new Error('Failed to generate document');
  }

  const result = await response.json();
  
  // Access validation results
  if (!result.validationResults.isValid) {
    console.error('Document validation failed:');
    result.validationResults.errors.forEach((error: any) => {
      console.error(`- ${error.field}: ${error.message}`);
    });
  }
}

// ============================================================================
// EXAMPLE 7: Working with Chat Messages
// ============================================================================

export function formatChatMessage(message: ChatMessage): string {
  const timestamp = new Date(message.timestamp).toLocaleTimeString();
  const role = message.role === 'user' ? 'You' : 'ExportSathi';
  
  let formatted = `[${timestamp}] ${role}: ${message.content}`;
  
  if (message.sources && message.sources.length > 0) {
    formatted += '\n\nSources:';
    message.sources.forEach(source => {
      formatted += `\n- ${source.title}`;
      if (source.url) {
        formatted += ` (${source.url})`;
      }
    });
  }
  
  return formatted;
}

// ============================================================================
// EXAMPLE 8: Form Data with File Upload
// ============================================================================

export async function submitQueryWithImage(
  query: QueryInput,
  imageFile?: File
): Promise<GenerateReportResponse> {
  const formData = new FormData();
  
  // Add all query fields
  formData.append('product_name', query.productName);
  formData.append('destination_country', query.destinationCountry);
  formData.append('business_type', query.businessType);
  formData.append('company_size', query.companySize);
  
  if (query.ingredients) {
    formData.append('ingredients', query.ingredients);
  }
  
  if (query.bom) {
    formData.append('bom', query.bom);
  }
  
  if (imageFile) {
    formData.append('product_image', imageFile);
  }
  
  if (query.monthlyVolume) {
    formData.append('monthly_volume', query.monthlyVolume.toString());
  }

  const response = await fetch('/api/reports/generate', {
    method: 'POST',
    body: formData,
  });

  if (!response.ok) {
    throw new Error('Failed to generate report');
  }

  return response.json();
}

// ============================================================================
// EXAMPLE 9: Filtering and Mapping with Type Safety
// ============================================================================

export function getHighRiskCertifications(report: ExportReadinessReport) {
  return report.certifications
    .filter(cert => cert.mandatory && cert.estimatedTimelineDays > 30)
    .map(cert => ({
      name: cert.name,
      type: cert.type,
      cost: cert.estimatedCost,
      timeline: cert.estimatedTimelineDays,
    }));
}

export function calculateTotalCertificationCost(report: ExportReadinessReport): number {
  return report.certifications.reduce((total, cert) => {
    // Use average of min and max cost
    const avgCost = (cert.estimatedCost.min + cert.estimatedCost.max) / 2;
    return total + avgCost;
  }, 0);
}

// ============================================================================
// EXAMPLE 10: Error Handling with Type Guards
// ============================================================================

export async function safelyFetchReport(
  reportId: string
): Promise<ExportReadinessReport | null> {
  try {
    const response = await fetch(`/api/reports/${reportId}`);
    
    if (!response.ok) {
      console.error(`API error: ${response.status}`);
      return null;
    }

    const json = await response.json();
    
    if (isExportReadinessReport(json)) {
      return json;
    } else {
      console.error('Invalid report format received');
      return null;
    }
  } catch (error) {
    console.error('Failed to fetch report:', error);
    return null;
  }
}

// ============================================================================
// EXAMPLE 11: Discriminated Union Pattern
// ============================================================================

export function handleReportStatus(report: ExportReadinessReport): string {
  // TypeScript ensures all cases are handled
  switch (report.status) {
    case 'completed':
      return `Report completed at ${report.generatedAt}`;
    case 'processing':
      return 'Report is being generated...';
    case 'failed':
      return 'Report generation failed';
    default:
      // TypeScript will error if we miss a case
      const _exhaustive: never = report.status;
      return _exhaustive;
  }
}

// ============================================================================
// EXAMPLE 12: Partial Updates with Type Safety
// ============================================================================

export async function updateTaskStatus(
  reportId: string,
  taskId: string,
  completed: boolean
): Promise<void> {
  const response = await fetch(
    `/api/action-plan/${reportId}/tasks/${taskId}`,
    {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ completed }),
    }
  );

  if (!response.ok) {
    throw new Error('Failed to update task status');
  }
}

// ============================================================================
// EXAMPLE 13: Type-Safe Configuration Objects
// ============================================================================

export interface ReportDisplayConfig {
  showSources: boolean;
  showRisks: boolean;
  showCosts: boolean;
  highlightMandatoryCerts: boolean;
}

export function renderReport(
  report: ExportReadinessReport,
  config: ReportDisplayConfig
): void {
  console.log(`=== ${report.reportId} ===`);
  
  if (config.showRisks) {
    console.log('\nRisks:');
    report.risks.forEach(risk => {
      console.log(`- [${risk.severity.toUpperCase()}] ${risk.title}`);
    });
  }
  
  if (config.showCosts) {
    console.log(`\nTotal Cost: ${report.costs.total} ${report.costs.currency}`);
  }
  
  if (config.highlightMandatoryCerts) {
    const mandatory = report.certifications.filter(c => c.mandatory);
    console.log(`\nMandatory Certifications: ${mandatory.length}`);
  }
  
  if (config.showSources) {
    console.log(`\nSources: ${report.retrievedSources.length}`);
  }
}
