/**
 * API Client Service for ExportSathi
 * 
 * Provides methods for all backend API endpoints with error handling,
 * retry logic, and request/response interceptors.
 * 
 * Requirements: 8.1
 */

import axios, { AxiosInstance, AxiosError, AxiosRequestConfig } from 'axios';

// API base URL from environment variable
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

// Create axios instance with default config
const apiClient: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  timeout: 60000, // 60 seconds for report generation
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor for adding auth tokens
apiClient.interceptors.request.use(
  (config) => {
    // Add auth token if available
    const token = localStorage.getItem('auth_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor for error handling
apiClient.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config as AxiosRequestConfig & { _retry?: boolean };

    // Handle 401 Unauthorized
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      // Clear auth token and redirect to login
      localStorage.removeItem('auth_token');
      window.location.href = '/login';
      return Promise.reject(error);
    }

    // Handle 429 Too Many Requests with retry
    if (error.response?.status === 429 && !originalRequest._retry) {
      originalRequest._retry = true;
      // Wait 2 seconds and retry
      await new Promise(resolve => setTimeout(resolve, 2000));
      return apiClient(originalRequest);
    }

    return Promise.reject(error);
  }
);

// Types
export interface QueryInput {
  product_name: string;
  product_image?: File;
  ingredients?: string;
  bom?: string;
  destination_country: string;
  business_type: string;
  company_size: string;
  monthly_volume?: number;
  price_range?: string;
  payment_mode?: string;
}

export interface ExportReadinessReport {
  report_id: string;
  status: string;
  hs_code: {
    code: string;
    confidence: number;
    description: string;
    alternatives?: Array<{ code: string; confidence: number }>;
  };
  certifications: Array<{
    id: string;
    name: string;
    type: string;
    mandatory: boolean;
    estimated_cost: { min: number; max: number; currency: string };
    estimated_timeline_days: number;
    priority: string;
  }>;
  restricted_substances: Array<{
    name: string;
    reason: string;
    regulation: string;
  }>;
  past_rejections: Array<any>;
  compliance_roadmap: Array<{
    step: number;
    title: string;
    description: string;
    duration_days: number;
    dependencies: string[];
  }>;
  risks: Array<{
    title: string;
    description: string;
    severity: string;
    mitigation: string;
  }>;
  risk_score: number;
  timeline: {
    estimated_days: number;
    breakdown: Array<{ phase: string; duration_days: number }>;
  };
  costs: {
    certifications: number;
    documentation: number;
    logistics: number;
    total: number;
    currency: string;
  };
  subsidies: Array<{
    name: string;
    amount: number;
    percentage: number;
    eligibility: string;
    application_process: string;
  }>;
  action_plan: {
    days: Array<{
      day: number;
      title: string;
      tasks: Array<{
        id: string;
        title: string;
        description: string;
        category: string;
        completed: boolean;
        estimated_duration: string;
      }>;
    }>;
    progress_percentage: number;
  };
  retrieved_sources: Array<{
    title: string;
    source: string;
    excerpt: string;
    url?: string;
    relevance_score: number;
  }>;
  generated_at: string;
}

export interface CertificationGuidance {
  certification_id: string;
  why_required: string;
  roadmap: Array<{
    step: number;
    title: string;
    description: string;
    duration_days: number;
    dependencies: string[];
  }>;
  document_checklist: Array<{
    id: string;
    name: string;
    description: string;
    mandatory: boolean;
    auto_fill_available: boolean;
  }>;
  test_labs: Array<{
    id: string;
    name: string;
    accreditation: string;
    location: string;
    contact: {
      email: string;
      phone: string;
      website: string;
    };
    specialization: string[];
  }>;
  consultants: Array<{
    id: string;
    name: string;
    specialization: string[];
    rating: number;
    cost_range: { min: number; max: number; currency: string };
    contact: {
      email: string;
      phone: string;
      website: string;
    };
    experience_years: number;
  }>;
  subsidies: Array<{
    name: string;
    amount: number;
    percentage: number;
    eligibility: string;
    application_process: string;
  }>;
  common_rejection_reasons: string[];
  mock_audit_questions: Array<{
    question: string;
    category: string;
    importance: string;
  }>;
  estimated_cost: { min: number; max: number; currency: string };
  estimated_timeline_days: number;
}

// API Methods
class ApiService {
  /**
   * Generate export readiness report
   */
  async generateReport(query: QueryInput): Promise<ExportReadinessReport> {
    const formData = new FormData();
    
    // Add text fields
    formData.append('product_name', query.product_name);
    formData.append('destination_country', query.destination_country);
    formData.append('business_type', query.business_type);
    formData.append('company_size', query.company_size);
    
    if (query.ingredients) formData.append('ingredients', query.ingredients);
    if (query.bom) formData.append('bom', query.bom);
    if (query.monthly_volume) formData.append('monthly_volume', query.monthly_volume.toString());
    if (query.price_range) formData.append('price_range', query.price_range);
    if (query.payment_mode) formData.append('payment_mode', query.payment_mode);
    
    // Add image file if provided
    if (query.product_image) {
      formData.append('product_image', query.product_image);
    }

    const response = await apiClient.post<ExportReadinessReport>(
      '/api/reports/generate',
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      }
    );

    return response.data;
  }

  /**
   * Get existing report by ID
   */
  async getReport(reportId: string): Promise<ExportReadinessReport> {
    const response = await apiClient.get<ExportReadinessReport>(`/api/reports/${reportId}`);
    return response.data;
  }

  /**
   * Get report generation status
   */
  async getReportStatus(reportId: string): Promise<{ status: string; progress?: number }> {
    const response = await apiClient.get(`/api/reports/${reportId}/status`);
    return response.data;
  }

  /**
   * List all supported certifications
   */
  async listCertifications(): Promise<Array<any>> {
    const response = await apiClient.get('/api/certifications/');
    return response.data;
  }

  /**
   * Get certification details
   */
  async getCertification(certId: string): Promise<any> {
    const response = await apiClient.get(`/api/certifications/${certId}`);
    return response.data;
  }

  /**
   * Get detailed certification guidance
   */
  async getCertificationGuidance(
    certId: string,
    productType: string,
    destinationCountry: string,
    companySize: string = 'Small'
  ): Promise<CertificationGuidance> {
    const response = await apiClient.post<CertificationGuidance>(
      `/api/certifications/${certId}/guidance`,
      null,
      {
        params: {
          product_type: productType,
          destination_country: destinationCountry,
          company_size: companySize,
        },
      }
    );
    return response.data;
  }

  /**
   * Get test labs for certification
   */
  async getTestLabs(certId: string, location: string = 'India'): Promise<Array<any>> {
    const response = await apiClient.get(`/api/certifications/${certId}/test-labs`, {
      params: { location },
    });
    return response.data;
  }

  /**
   * Get consultants for certification
   */
  async getConsultants(certId: string): Promise<Array<any>> {
    const response = await apiClient.get(`/api/certifications/${certId}/consultants`);
    return response.data;
  }

  /**
   * Get subsidies for certification
   */
  async getSubsidies(certId: string, companySize: string): Promise<Array<any>> {
    const response = await apiClient.get(`/api/certifications/${certId}/subsidies`, {
      params: { company_size: companySize },
    });
    return response.data;
  }

  /**
   * Update certification progress
   */
  async updateCertificationProgress(
    certId: string,
    status: string,
    reportId: string
  ): Promise<any> {
    const response = await apiClient.put(`/api/certifications/${certId}/progress`, null, {
      params: { status, report_id: reportId },
    });
    return response.data;
  }
}

// Export singleton instance
export const api = new ApiService();
export default api;
