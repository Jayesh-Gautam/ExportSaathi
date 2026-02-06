/**
 * API request and response type definitions for ExportSathi
 * These types define the structure of data sent to and received from the backend API
 */

import type {
  ExportReadinessReport,
  CertificationGuidance,
  GeneratedDocument,
  FinanceAnalysis,
  LogisticsRiskAnalysis,
  ChatResponse,
  ActionPlan,
  UserProfile,
  UserMetrics,
  DocumentType,
  QueryInput,
} from './index';

// ============================================================================
// API ERROR RESPONSES
// ============================================================================

export interface ApiError {
  error: string;
  detail: string;
  code: 'INVALID_INPUT' | 'IMAGE_PROCESSING_FAILED' | 'GENERATION_FAILED' | 'RATE_LIMIT_EXCEEDED' | 'UNAUTHORIZED' | 'NOT_FOUND' | 'SERVER_ERROR';
}

export interface ValidationErrorResponse {
  detail: Array<{
    loc: string[];
    msg: string;
    type: string;
  }>;
}

// ============================================================================
// REPORT API TYPES
// ============================================================================

export interface GenerateReportRequest {
  productName: string;
  productImage?: File;
  ingredients?: string;
  bom?: string;
  destinationCountry: string;
  businessType: string;
  companySize: string;
  monthlyVolume?: number;
  priceRange?: string;
  paymentMode?: string;
}

export interface GenerateReportResponse {
  reportId: string;
  status: 'completed' | 'processing' | 'failed';
  report?: ExportReadinessReport;
  generatedAt: string;
}

export interface GetReportResponse {
  report: ExportReadinessReport;
}

export interface ReportStatusResponse {
  reportId: string;
  status: 'completed' | 'processing' | 'failed';
  progress?: number;
  message?: string;
}

export interface UpdateHSCodeRequest {
  hsCode: string;
  description: string;
}

// ============================================================================
// CERTIFICATION API TYPES
// ============================================================================

export interface GetCertificationGuidanceRequest {
  productType: string;
  destinationCountry: string;
  companySize: string;
}

export interface GetCertificationGuidanceResponse {
  guidance: CertificationGuidance;
}

export interface UpdateCertificationProgressRequest {
  status: 'not_started' | 'in_progress' | 'completed';
  completedDocuments?: string[];
}

export interface UpdateCertificationProgressResponse {
  success: boolean;
  message: string;
}

// ============================================================================
// DOCUMENT API TYPES
// ============================================================================

export interface GenerateDocumentRequest {
  documentType: DocumentType;
  reportId: string;
  customData?: Record<string, unknown>;
}

export interface GenerateDocumentResponse {
  document: GeneratedDocument;
}

export interface ValidateDocumentRequest {
  documentType: DocumentType;
  content: Record<string, unknown>;
}

export interface ValidateDocumentResponse {
  isValid: boolean;
  errors: Array<{
    field: string;
    message: string;
    severity: 'error' | 'warning';
    suggestion: string;
  }>;
  warnings: Array<{
    field: string;
    message: string;
    suggestion: string;
  }>;
}

export interface GetDocumentTypesResponse {
  documentTypes: Array<{
    type: DocumentType;
    name: string;
    description: string;
    requiredFields: string[];
  }>;
}

// ============================================================================
// FINANCE API TYPES
// ============================================================================

export interface GetFinanceAnalysisResponse {
  analysis: FinanceAnalysis;
}

export interface CalculateRoDTEPRequest {
  hsCode: string;
  destinationCountry: string;
  fobValue: number;
}

export interface CalculateRoDTEPResponse {
  hsCode: string;
  ratePercentage: number;
  estimatedAmount: number;
  currency: string;
}

export interface CalculateWorkingCapitalRequest {
  reportId: string;
  productCost: number;
  monthlyVolume?: number;
}

export interface CalculateWorkingCapitalResponse {
  productCost: number;
  certificationCosts: number;
  logisticsCosts: number;
  documentationCosts: number;
  buffer: number;
  total: number;
  currency: string;
}

export interface GetCreditEligibilityRequest {
  companySize: string;
  orderValue: number;
  exportHistory?: boolean;
}

export interface GetCreditEligibilityResponse {
  eligible: boolean;
  estimatedAmount: number;
  interestRate: number;
  tenureDays: number;
  requirements: string[];
}

export interface GetBankReferralsResponse {
  banks: Array<{
    name: string;
    type: string;
    products: string[];
    contactInfo: string;
    website: string;
  }>;
}

// ============================================================================
// LOGISTICS API TYPES
// ============================================================================

export interface AnalyzeLogisticsRiskRequest {
  productType: string;
  hsCode: string;
  volume: number;
  value: number;
  destinationCountry: string;
  productDescription: string;
}

export interface AnalyzeLogisticsRiskResponse {
  analysis: LogisticsRiskAnalysis;
}

export interface CalculateRMSProbabilityRequest {
  productType: string;
  hsCode: string;
  productDescription: string;
  exportHistory?: boolean;
}

export interface CalculateRMSProbabilityResponse {
  probabilityPercentage: number;
  riskLevel: 'high' | 'medium' | 'low';
  riskFactors: string[];
  redFlagKeywords: string[];
  mitigationTips: string[];
}

export interface EstimateFreightRequest {
  originPort: string;
  destinationPort: string;
  volume: number;
  weight: number;
  mode?: 'sea' | 'air';
}

export interface EstimateFreightResponse {
  seaFreight: number;
  airFreight: number;
  recommendedMode: 'sea' | 'air';
  currency: string;
  transitTimeDays: {
    sea: number;
    air: number;
  };
}

export interface GetRoutesRequest {
  origin: string;
  destination: string;
}

export interface GetRoutesResponse {
  routes: Array<{
    name: string;
    transitTimeDays: number;
    delayRisk: 'high' | 'medium' | 'low';
    geopoliticalFactors: string[];
    costEstimate: number;
  }>;
}

export interface CompareLCLFCLRequest {
  volume: number;
  productType: string;
  destinationCountry: string;
}

export interface CompareLCLFCLResponse {
  recommendation: 'LCL' | 'FCL';
  lcl: {
    cost: number;
    riskLevel: 'high' | 'medium' | 'low';
    pros: string[];
    cons: string[];
  };
  fcl: {
    cost: number;
    riskLevel: 'high' | 'medium' | 'low';
    pros: string[];
    cons: string[];
  };
}

// ============================================================================
// ACTION PLAN API TYPES
// ============================================================================

export interface GetActionPlanResponse {
  actionPlan: ActionPlan;
  estimatedCompletionDate: string;
  notes: string[];
}

export interface UpdateTaskStatusRequest {
  completed: boolean;
}

export interface UpdateTaskStatusResponse {
  success: boolean;
  progressPercentage: number;
}

export interface GetActionPlanProgressResponse {
  progressPercentage: number;
  completedTasks: number;
  totalTasks: number;
  estimatedCompletionDate: string;
}

// ============================================================================
// CHAT API TYPES
// ============================================================================

export interface SendChatMessageRequest {
  sessionId: string;
  question: string;
  context: {
    reportId: string;
    productType: string;
    destinationCountry: string;
  };
}

export interface SendChatMessageResponse {
  response: ChatResponse;
}

export interface GetChatHistoryResponse {
  messages: Array<{
    messageId: string;
    role: 'user' | 'assistant';
    content: string;
    sources?: Array<{
      title: string;
      excerpt?: string;
      url?: string;
    }>;
    timestamp: string;
  }>;
}

export interface ClearChatHistoryResponse {
  success: boolean;
  message: string;
}

// ============================================================================
// USER API TYPES
// ============================================================================

export interface RegisterUserRequest {
  email: string;
  password: string;
  businessType: string;
  companySize: string;
  companyName: string;
  monthlyVolume?: number;
}

export interface RegisterUserResponse {
  userId: string;
  email: string;
  message: string;
}

export interface LoginUserRequest {
  email: string;
  password: string;
}

export interface LoginUserResponse {
  accessToken: string;
  tokenType: string;
  expiresIn: number;
  user: UserProfile;
}

export interface GetUserProfileResponse {
  profile: UserProfile;
}

export interface UpdateUserProfileRequest {
  companyName?: string;
  monthlyVolume?: number;
  businessType?: string;
  companySize?: string;
}

export interface UpdateUserProfileResponse {
  profile: UserProfile;
  message: string;
}

export interface GetUserMetricsResponse {
  metrics: UserMetrics;
}

// ============================================================================
// PAGINATION TYPES
// ============================================================================

export interface PaginationParams {
  page?: number;
  pageSize?: number;
  sortBy?: string;
  sortOrder?: 'asc' | 'desc';
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  pageSize: number;
  totalPages: number;
}

// ============================================================================
// UTILITY TYPES
// ============================================================================

/**
 * Generic API response wrapper
 */
export interface ApiResponse<T> {
  success: boolean;
  data?: T;
  error?: ApiError;
  timestamp: string;
}

/**
 * File upload progress callback
 */
export type UploadProgressCallback = (progress: number) => void;

/**
 * API request options
 */
export interface ApiRequestOptions {
  signal?: AbortSignal;
  onUploadProgress?: UploadProgressCallback;
  timeout?: number;
}
