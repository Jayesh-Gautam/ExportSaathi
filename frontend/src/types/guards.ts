/**
 * Type guards for runtime validation of ExportSathi data models
 * These functions check if unknown data matches expected TypeScript interfaces
 */

import type {
  BusinessType,
  CompanySize,
  CertificationType,
  RiskSeverity,
  Priority,
  DocumentType,
  TaskCategory,
  ShippingMode,
  FreightMode,
  ReportStatus,
  MessageRole,
  RejectionSource,
  CashFlowEventType,
  ValidationSeverity,
  UserProfile,
  QueryInput,
  HSCodePrediction,
  HSCodeAlternative,
  Certification,
  CertificationGuidance,
  ExportReadinessReport,
  ActionPlan,
  DayPlan,
  Task,
  GeneratedDocument,
  ValidationResult,
  FinanceAnalysis,
  LogisticsRiskAnalysis,
  ChatMessage,
  ChatResponse,
  CostRange,
  Source,
} from './index';

// ============================================================================
// ENUM TYPE GUARDS
// ============================================================================

export function isBusinessType(value: unknown): value is BusinessType {
  return typeof value === 'string' && ['Manufacturing', 'SaaS', 'Merchant'].includes(value);
}

export function isCompanySize(value: unknown): value is CompanySize {
  return typeof value === 'string' && ['Micro', 'Small', 'Medium'].includes(value);
}

export function isCertificationType(value: unknown): value is CertificationType {
  return typeof value === 'string' && ['FDA', 'CE', 'REACH', 'BIS', 'ZED', 'SOFTEX', 'other'].includes(value);
}

export function isRiskSeverity(value: unknown): value is RiskSeverity {
  return typeof value === 'string' && ['high', 'medium', 'low'].includes(value);
}

export function isPriority(value: unknown): value is Priority {
  return typeof value === 'string' && ['high', 'medium', 'low'].includes(value);
}

export function isDocumentType(value: unknown): value is DocumentType {
  return typeof value === 'string' && 
    ['commercial_invoice', 'packing_list', 'shipping_bill', 'gst_lut', 'softex', 'certificate_of_origin'].includes(value);
}

export function isTaskCategory(value: unknown): value is TaskCategory {
  return typeof value === 'string' && ['certification', 'documentation', 'logistics', 'finance'].includes(value);
}

export function isShippingMode(value: unknown): value is ShippingMode {
  return typeof value === 'string' && ['LCL', 'FCL'].includes(value);
}

export function isFreightMode(value: unknown): value is FreightMode {
  return typeof value === 'string' && ['sea', 'air'].includes(value);
}

export function isReportStatus(value: unknown): value is ReportStatus {
  return typeof value === 'string' && ['completed', 'processing', 'failed'].includes(value);
}

export function isMessageRole(value: unknown): value is MessageRole {
  return typeof value === 'string' && ['user', 'assistant'].includes(value);
}

export function isRejectionSource(value: unknown): value is RejectionSource {
  return typeof value === 'string' && ['FDA', 'EU_RASFF', 'other'].includes(value);
}

export function isCashFlowEventType(value: unknown): value is CashFlowEventType {
  return typeof value === 'string' && ['expense', 'income'].includes(value);
}

export function isValidationSeverity(value: unknown): value is ValidationSeverity {
  return typeof value === 'string' && ['error', 'warning'].includes(value);
}

// ============================================================================
// COMMON MODEL TYPE GUARDS
// ============================================================================

export function isCostRange(value: unknown): value is CostRange {
  if (typeof value !== 'object' || value === null) return false;
  const obj = value as Record<string, unknown>;
  return (
    typeof obj.min === 'number' &&
    typeof obj.max === 'number' &&
    typeof obj.currency === 'string' &&
    obj.min >= 0 &&
    obj.max >= 0
  );
}

export function isSource(value: unknown): value is Source {
  if (typeof value !== 'object' || value === null) return false;
  const obj = value as Record<string, unknown>;
  return (
    typeof obj.title === 'string' &&
    (obj.source === undefined || typeof obj.source === 'string') &&
    (obj.excerpt === undefined || typeof obj.excerpt === 'string') &&
    (obj.url === undefined || typeof obj.url === 'string') &&
    (obj.relevanceScore === undefined || typeof obj.relevanceScore === 'number')
  );
}

// ============================================================================
// USER MODEL TYPE GUARDS
// ============================================================================

export function isUserProfile(value: unknown): value is UserProfile {
  if (typeof value !== 'object' || value === null) return false;
  const obj = value as Record<string, unknown>;
  return (
    typeof obj.userId === 'string' &&
    typeof obj.email === 'string' &&
    isBusinessType(obj.businessType) &&
    isCompanySize(obj.companySize) &&
    typeof obj.companyName === 'string' &&
    (obj.monthlyVolume === undefined || typeof obj.monthlyVolume === 'number') &&
    typeof obj.createdAt === 'string'
  );
}

// ============================================================================
// QUERY MODEL TYPE GUARDS
// ============================================================================

export function isQueryInput(value: unknown): value is QueryInput {
  if (typeof value !== 'object' || value === null) return false;
  const obj = value as Record<string, unknown>;
  return (
    typeof obj.productName === 'string' &&
    (obj.productImage === undefined || obj.productImage instanceof File) &&
    (obj.ingredients === undefined || typeof obj.ingredients === 'string') &&
    (obj.bom === undefined || typeof obj.bom === 'string') &&
    typeof obj.destinationCountry === 'string' &&
    isBusinessType(obj.businessType) &&
    isCompanySize(obj.companySize) &&
    (obj.monthlyVolume === undefined || typeof obj.monthlyVolume === 'number') &&
    (obj.priceRange === undefined || typeof obj.priceRange === 'string') &&
    (obj.paymentMode === undefined || typeof obj.paymentMode === 'string')
  );
}

export function isHSCodeAlternative(value: unknown): value is HSCodeAlternative {
  if (typeof value !== 'object' || value === null) return false;
  const obj = value as Record<string, unknown>;
  return (
    typeof obj.code === 'string' &&
    typeof obj.confidence === 'number' &&
    typeof obj.description === 'string' &&
    obj.confidence >= 0 &&
    obj.confidence <= 100
  );
}

export function isHSCodePrediction(value: unknown): value is HSCodePrediction {
  if (typeof value !== 'object' || value === null) return false;
  const obj = value as Record<string, unknown>;
  return (
    typeof obj.code === 'string' &&
    typeof obj.confidence === 'number' &&
    typeof obj.description === 'string' &&
    Array.isArray(obj.alternatives) &&
    obj.alternatives.every(isHSCodeAlternative) &&
    obj.confidence >= 0 &&
    obj.confidence <= 100
  );
}

// ============================================================================
// CERTIFICATION MODEL TYPE GUARDS
// ============================================================================

export function isCertification(value: unknown): value is Certification {
  if (typeof value !== 'object' || value === null) return false;
  const obj = value as Record<string, unknown>;
  return (
    typeof obj.id === 'string' &&
    typeof obj.name === 'string' &&
    isCertificationType(obj.type) &&
    typeof obj.mandatory === 'boolean' &&
    isCostRange(obj.estimatedCost) &&
    typeof obj.estimatedTimelineDays === 'number' &&
    isPriority(obj.priority) &&
    obj.estimatedTimelineDays > 0
  );
}

export function isCertificationGuidance(value: unknown): value is CertificationGuidance {
  if (typeof value !== 'object' || value === null) return false;
  const obj = value as Record<string, unknown>;
  return (
    typeof obj.certificationId === 'string' &&
    typeof obj.name === 'string' &&
    typeof obj.whyRequired === 'string' &&
    Array.isArray(obj.steps) &&
    Array.isArray(obj.documentChecklist) &&
    Array.isArray(obj.testLabs) &&
    Array.isArray(obj.consultants) &&
    Array.isArray(obj.subsidies) &&
    Array.isArray(obj.commonRejectionReasons) &&
    Array.isArray(obj.mockAuditQuestions) &&
    isCostRange(obj.estimatedCost) &&
    typeof obj.estimatedTimeline === 'string' &&
    Array.isArray(obj.sources)
  );
}

// ============================================================================
// ACTION PLAN MODEL TYPE GUARDS
// ============================================================================

export function isTask(value: unknown): value is Task {
  if (typeof value !== 'object' || value === null) return false;
  const obj = value as Record<string, unknown>;
  return (
    typeof obj.id === 'string' &&
    typeof obj.title === 'string' &&
    typeof obj.description === 'string' &&
    isTaskCategory(obj.category) &&
    typeof obj.completed === 'boolean' &&
    (obj.estimatedDuration === undefined || typeof obj.estimatedDuration === 'string') &&
    Array.isArray(obj.dependencies) &&
    obj.dependencies.every((dep) => typeof dep === 'string')
  );
}

export function isDayPlan(value: unknown): value is DayPlan {
  if (typeof value !== 'object' || value === null) return false;
  const obj = value as Record<string, unknown>;
  return (
    typeof obj.day === 'number' &&
    typeof obj.title === 'string' &&
    Array.isArray(obj.tasks) &&
    obj.tasks.every(isTask) &&
    obj.day >= 1 &&
    obj.day <= 7 &&
    obj.tasks.length > 0
  );
}

export function isActionPlan(value: unknown): value is ActionPlan {
  if (typeof value !== 'object' || value === null) return false;
  const obj = value as Record<string, unknown>;
  return (
    Array.isArray(obj.days) &&
    obj.days.every(isDayPlan) &&
    typeof obj.progressPercentage === 'number' &&
    obj.days.length === 7 &&
    obj.progressPercentage >= 0 &&
    obj.progressPercentage <= 100
  );
}

// ============================================================================
// REPORT MODEL TYPE GUARDS
// ============================================================================

export function isExportReadinessReport(value: unknown): value is ExportReadinessReport {
  if (typeof value !== 'object' || value === null) return false;
  const obj = value as Record<string, unknown>;
  return (
    typeof obj.reportId === 'string' &&
    isReportStatus(obj.status) &&
    isHSCodePrediction(obj.hsCode) &&
    Array.isArray(obj.certifications) &&
    obj.certifications.every(isCertification) &&
    Array.isArray(obj.restrictedSubstances) &&
    Array.isArray(obj.pastRejections) &&
    Array.isArray(obj.complianceRoadmap) &&
    Array.isArray(obj.risks) &&
    typeof obj.riskScore === 'number' &&
    typeof obj.timeline === 'object' &&
    obj.timeline !== null &&
    typeof obj.costs === 'object' &&
    obj.costs !== null &&
    Array.isArray(obj.subsidies) &&
    isActionPlan(obj.actionPlan) &&
    Array.isArray(obj.retrievedSources) &&
    typeof obj.generatedAt === 'string' &&
    obj.riskScore >= 0 &&
    obj.riskScore <= 100
  );
}

// ============================================================================
// DOCUMENT MODEL TYPE GUARDS
// ============================================================================

export function isValidationResult(value: unknown): value is ValidationResult {
  if (typeof value !== 'object' || value === null) return false;
  const obj = value as Record<string, unknown>;
  return (
    typeof obj.isValid === 'boolean' &&
    Array.isArray(obj.errors) &&
    Array.isArray(obj.warnings)
  );
}

export function isGeneratedDocument(value: unknown): value is GeneratedDocument {
  if (typeof value !== 'object' || value === null) return false;
  const obj = value as Record<string, unknown>;
  return (
    typeof obj.documentId === 'string' &&
    isDocumentType(obj.documentType) &&
    typeof obj.content === 'object' &&
    obj.content !== null &&
    isValidationResult(obj.validationResults) &&
    typeof obj.pdfUrl === 'string' &&
    typeof obj.editableUrl === 'string' &&
    typeof obj.generatedAt === 'string'
  );
}

// ============================================================================
// FINANCE MODEL TYPE GUARDS
// ============================================================================

export function isFinanceAnalysis(value: unknown): value is FinanceAnalysis {
  if (typeof value !== 'object' || value === null) return false;
  const obj = value as Record<string, unknown>;
  return (
    typeof obj.reportId === 'string' &&
    typeof obj.workingCapital === 'object' &&
    obj.workingCapital !== null &&
    typeof obj.preShipmentCredit === 'object' &&
    obj.preShipmentCredit !== null &&
    typeof obj.rodtepBenefit === 'object' &&
    obj.rodtepBenefit !== null &&
    typeof obj.gstRefund === 'object' &&
    obj.gstRefund !== null &&
    typeof obj.cashFlowTimeline === 'object' &&
    obj.cashFlowTimeline !== null &&
    typeof obj.currencyHedging === 'object' &&
    obj.currencyHedging !== null &&
    Array.isArray(obj.financingOptions)
  );
}

// ============================================================================
// LOGISTICS MODEL TYPE GUARDS
// ============================================================================

export function isLogisticsRiskAnalysis(value: unknown): value is LogisticsRiskAnalysis {
  if (typeof value !== 'object' || value === null) return false;
  const obj = value as Record<string, unknown>;
  return (
    typeof obj.lclFclComparison === 'object' &&
    obj.lclFclComparison !== null &&
    typeof obj.rmsProbability === 'object' &&
    obj.rmsProbability !== null &&
    typeof obj.routeAnalysis === 'object' &&
    obj.routeAnalysis !== null &&
    typeof obj.freightEstimate === 'object' &&
    obj.freightEstimate !== null &&
    typeof obj.insuranceRecommendation === 'object' &&
    obj.insuranceRecommendation !== null
  );
}

// ============================================================================
// CHAT MODEL TYPE GUARDS
// ============================================================================

export function isChatMessage(value: unknown): value is ChatMessage {
  if (typeof value !== 'object' || value === null) return false;
  const obj = value as Record<string, unknown>;
  return (
    typeof obj.messageId === 'string' &&
    isMessageRole(obj.role) &&
    typeof obj.content === 'string' &&
    (obj.sources === undefined || (Array.isArray(obj.sources) && obj.sources.every(isSource))) &&
    typeof obj.timestamp === 'string'
  );
}

export function isChatResponse(value: unknown): value is ChatResponse {
  if (typeof value !== 'object' || value === null) return false;
  const obj = value as Record<string, unknown>;
  return (
    typeof obj.messageId === 'string' &&
    typeof obj.answer === 'string' &&
    Array.isArray(obj.sources) &&
    obj.sources.every(isSource) &&
    typeof obj.timestamp === 'string'
  );
}

// ============================================================================
// UTILITY FUNCTIONS
// ============================================================================

/**
 * Validates and parses JSON response from API
 * @param json - Unknown JSON data
 * @param guard - Type guard function
 * @returns Typed data if valid, throws error otherwise
 */
export function validateApiResponse<T>(
  json: unknown,
  guard: (value: unknown) => value is T,
  errorMessage: string = 'Invalid API response format'
): T {
  if (guard(json)) {
    return json;
  }
  throw new Error(errorMessage);
}

/**
 * Safely parses API response with type checking
 * @param response - Fetch response
 * @param guard - Type guard function
 * @returns Typed data if valid
 */
export async function parseApiResponse<T>(
  response: Response,
  guard: (value: unknown) => value is T
): Promise<T> {
  if (!response.ok) {
    throw new Error(`API error: ${response.status} ${response.statusText}`);
  }
  
  const json = await response.json();
  return validateApiResponse(json, guard, `Invalid response format for ${response.url}`);
}
