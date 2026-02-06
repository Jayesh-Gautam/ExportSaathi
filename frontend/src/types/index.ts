/**
 * TypeScript type definitions for ExportSathi
 * These interfaces match the backend Pydantic models exactly
 */

// ============================================================================
// ENUMS
// ============================================================================

export type BusinessType = 'Manufacturing' | 'SaaS' | 'Merchant';
export type CompanySize = 'Micro' | 'Small' | 'Medium';
export type CertificationType = 'FDA' | 'CE' | 'REACH' | 'BIS' | 'ZED' | 'SOFTEX' | 'other';
export type RiskSeverity = 'high' | 'medium' | 'low';
export type Priority = 'high' | 'medium' | 'low';
export type DocumentType = 'commercial_invoice' | 'packing_list' | 'shipping_bill' | 'gst_lut' | 'softex' | 'certificate_of_origin';
export type TaskCategory = 'certification' | 'documentation' | 'logistics' | 'finance';
export type ShippingMode = 'LCL' | 'FCL';
export type FreightMode = 'sea' | 'air';
export type ReportStatus = 'completed' | 'processing' | 'failed';
export type CertificationStatus = 'not_started' | 'in_progress' | 'completed';
export type MessageRole = 'user' | 'assistant';
export type RejectionSource = 'FDA' | 'EU_RASFF' | 'other';
export type CashFlowEventType = 'expense' | 'income';
export type ValidationSeverity = 'error' | 'warning';

// ============================================================================
// COMMON MODELS
// ============================================================================

export interface CostRange {
  min: number;
  max: number;
  currency: string;
}

export interface Source {
  title: string;
  source?: string;
  excerpt?: string;
  url?: string;
  relevanceScore?: number;
}

export interface GuidanceStep {
  stepNumber: number;
  title?: string;
  description: string;
  estimatedDuration: string;
}

// ============================================================================
// USER AND PROFILE MODELS
// ============================================================================

export interface UserProfile {
  userId: string;
  email: string;
  businessType: BusinessType;
  companySize: CompanySize;
  companyName: string;
  monthlyVolume?: number;
  createdAt: string;
}

export interface UserMetrics {
  userId: string;
  reportsGenerated: number;
  certificationsCompleted: number;
  exportsCompleted: number;
  costSavings: number;
  timelineSavings: number;
  successRate: number;
}

// ============================================================================
// QUERY AND HS CODE MODELS
// ============================================================================

export interface QueryInput {
  productName: string;
  productImage?: File;
  ingredients?: string;
  bom?: string;
  destinationCountry: string;
  businessType: BusinessType;
  companySize: CompanySize;
  monthlyVolume?: number;
  priceRange?: string;
  paymentMode?: string;
}

export interface HSCodeAlternative {
  code: string;
  confidence: number;
  description: string;
}

export interface HSCodePrediction {
  code: string;
  confidence: number;
  description: string;
  alternatives: HSCodeAlternative[];
}

export interface ImageFeatures {
  extractedText: string;
  visualFeatures: Record<string, unknown>;
  confidence: number;
}

// ============================================================================
// CERTIFICATION MODELS
// ============================================================================

export interface Certification {
  id: string;
  name: string;
  type: CertificationType;
  mandatory: boolean;
  estimatedCost: CostRange;
  estimatedTimelineDays: number;
  priority: Priority;
}

export interface DocumentChecklistItem {
  id: string;
  name: string;
  description: string;
  mandatory: boolean;
  autoFillAvailable: boolean;
}

export interface TestLab {
  name: string;
  location: string;
  contact: string;
  website: string;
  accreditation: string;
}

export interface Consultant {
  name: string;
  specialization: string;
  rating: number;
  costRange: CostRange;
  contact: string;
}

export interface Subsidy {
  name: string;
  amount: number;
  percentage: number;
  eligibility: string;
  applicationProcess: string;
}

export interface MockAuditQuestion {
  question: string;
  category: string;
  tips: string;
}

export interface CertificationGuidance {
  certificationId: string;
  name: string;
  whyRequired: string;
  steps: GuidanceStep[];
  documentChecklist: DocumentChecklistItem[];
  testLabs: TestLab[];
  consultants: Consultant[];
  subsidies: Subsidy[];
  commonRejectionReasons: string[];
  mockAuditQuestions: MockAuditQuestion[];
  estimatedCost: CostRange;
  estimatedTimeline: string;
  sources: Source[];
}

// ============================================================================
// REPORT MODELS
// ============================================================================

export interface RestrictedSubstance {
  name: string;
  reason: string;
  regulation: string;
}

export interface PastRejection {
  productType: string;
  reason: string;
  source: RejectionSource;
  date: string;
}

export interface RoadmapStep {
  step: number;
  title: string;
  description: string;
  durationDays: number;
  dependencies: string[];
}

export interface Risk {
  title: string;
  description: string;
  severity: RiskSeverity;
  mitigation: string;
}

export interface TimelinePhase {
  phase: string;
  durationDays: number;
}

export interface Timeline {
  estimatedDays: number;
  breakdown: TimelinePhase[];
}

export interface CostBreakdown {
  certifications: number;
  documentation: number;
  logistics: number;
  total: number;
  currency: string;
}

export interface ExportReadinessReport {
  reportId: string;
  status: ReportStatus;
  hsCode: HSCodePrediction;
  certifications: Certification[];
  restrictedSubstances: RestrictedSubstance[];
  pastRejections: PastRejection[];
  complianceRoadmap: RoadmapStep[];
  risks: Risk[];
  riskScore: number;
  timeline: Timeline;
  costs: CostBreakdown;
  subsidies: Subsidy[];
  actionPlan: ActionPlan;
  retrievedSources: Source[];
  generatedAt: string;
}

// ============================================================================
// ACTION PLAN MODELS
// ============================================================================

export interface Task {
  id: string;
  title: string;
  description: string;
  category: TaskCategory;
  completed: boolean;
  estimatedDuration?: string;
  dependencies: string[];
}

export interface DayPlan {
  day: number;
  title: string;
  tasks: Task[];
}

export interface ActionPlan {
  days: DayPlan[];
  progressPercentage: number;
}

// ============================================================================
// DOCUMENT MODELS
// ============================================================================

export interface ValidationError {
  field: string;
  message: string;
  severity: ValidationSeverity;
  suggestion: string;
}

export interface ValidationWarning {
  field: string;
  message: string;
  suggestion: string;
}

export interface ValidationResult {
  isValid: boolean;
  errors: ValidationError[];
  warnings: ValidationWarning[];
}

export interface GeneratedDocument {
  documentId: string;
  documentType: DocumentType;
  content: Record<string, unknown>;
  validationResults: ValidationResult;
  pdfUrl: string;
  editableUrl: string;
  generatedAt: string;
}

export interface DocumentGenerationRequest {
  documentType: DocumentType;
  reportId: string;
  customData: Record<string, unknown>;
}

// ============================================================================
// FINANCE MODELS
// ============================================================================

export interface WorkingCapitalAnalysis {
  productCost: number;
  certificationCosts: number;
  logisticsCosts: number;
  documentationCosts: number;
  buffer: number;
  total: number;
  currency: string;
}

export interface PreShipmentCredit {
  eligible: boolean;
  estimatedAmount: number;
  interestRate: number;
  tenureDays: number;
  requirements: string[];
}

export interface RoDTEPBenefit {
  hsCode: string;
  ratePercentage: number;
  estimatedAmount: number;
  currency: string;
}

export interface GSTRefund {
  estimatedAmount: number;
  timelineDays: number;
  requirements: string[];
}

export interface CashFlowEvent {
  date: string;
  type: CashFlowEventType;
  category: string;
  amount: number;
  description: string;
}

export interface LiquidityGap {
  startDate: string;
  endDate: string;
  amount: number;
}

export interface CashFlowTimeline {
  events: CashFlowEvent[];
  liquidityGap: LiquidityGap;
}

export interface CurrencyHedging {
  recommended: boolean;
  strategies: string[];
  estimatedSavings: number;
}

export interface FinancingOption {
  type: string;
  provider: string;
  amount: number;
  interestRate: number;
  tenure: string;
  eligibility: string;
}

export interface FinanceAnalysis {
  reportId: string;
  workingCapital: WorkingCapitalAnalysis;
  preShipmentCredit: PreShipmentCredit;
  rodtepBenefit: RoDTEPBenefit;
  gstRefund: GSTRefund;
  cashFlowTimeline: CashFlowTimeline;
  currencyHedging: CurrencyHedging;
  financingOptions: FinancingOption[];
}

// ============================================================================
// LOGISTICS MODELS
// ============================================================================

export interface ShippingOption {
  cost: number;
  riskLevel: RiskSeverity;
  pros: string[];
  cons: string[];
}

export interface LCLFCLComparison {
  recommendation: ShippingMode;
  lcl: ShippingOption;
  fcl: ShippingOption;
}

export interface RMSProbability {
  probabilityPercentage: number;
  riskLevel: RiskSeverity;
  riskFactors: string[];
  redFlagKeywords: string[];
  mitigationTips: string[];
}

export interface Route {
  name: string;
  transitTimeDays: number;
  delayRisk: RiskSeverity;
  geopoliticalFactors: string[];
  costEstimate: number;
}

export interface RouteAnalysis {
  recommendedRoute: string;
  routes: Route[];
}

export interface FreightEstimate {
  seaFreight: number;
  airFreight: number;
  recommendedMode: FreightMode;
  currency: string;
}

export interface InsuranceRecommendation {
  recommendedCoverage: number;
  premiumEstimate: number;
  coverageType: string;
}

export interface LogisticsRiskAnalysis {
  lclFclComparison: LCLFCLComparison;
  rmsProbability: RMSProbability;
  routeAnalysis: RouteAnalysis;
  freightEstimate: FreightEstimate;
  insuranceRecommendation: InsuranceRecommendation;
}

export interface LogisticsRiskRequest {
  productType: string;
  hsCode: string;
  volume: number;
  value: number;
  destinationCountry: string;
  productDescription: string;
}

// ============================================================================
// CHAT MODELS
// ============================================================================

export interface QueryContext {
  reportId: string;
  productType: string;
  destinationCountry: string;
}

export interface ChatMessage {
  messageId: string;
  role: MessageRole;
  content: string;
  sources?: Source[];
  timestamp: string;
}

export interface ChatRequest {
  sessionId: string;
  question: string;
  context: QueryContext;
}

export interface ChatResponse {
  messageId: string;
  answer: string;
  sources: Source[];
  timestamp: string;
}

export interface ChatSession {
  sessionId: string;
  messages: ChatMessage[];
  context: QueryContext;
  createdAt: string;
  lastActivity: string;
}

// ============================================================================
// RE-EXPORTS
// ============================================================================

// Export type guards for runtime validation
export * from './guards';

// Export API types
export * from './api';
