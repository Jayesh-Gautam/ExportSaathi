# ExportSathi TypeScript Type Definitions

This directory contains comprehensive TypeScript type definitions for the ExportSathi platform. All types are designed to match the backend Pydantic models exactly, ensuring type safety across the full stack.

## File Structure

### `index.ts`
Main type definitions file containing all data models organized by domain:

- **Enums**: Type unions for all enumerated values (BusinessType, CompanySize, etc.)
- **Common Models**: Shared types used across multiple domains (CostRange, Source, etc.)
- **User Models**: User profile and metrics types
- **Query Models**: Product query and HS code prediction types
- **Certification Models**: Certification requirements and guidance types
- **Report Models**: Export readiness report and related types
- **Action Plan Models**: 7-day action plan and task types
- **Document Models**: Document generation and validation types
- **Finance Models**: Financial analysis and calculation types
- **Logistics Models**: Logistics risk analysis types
- **Chat Models**: Chat conversation and messaging types

### `guards.ts`
Runtime type guards for validating API responses and unknown data:

- **Enum Guards**: Type guards for all enum types (e.g., `isBusinessType()`)
- **Model Guards**: Type guards for complex data structures (e.g., `isExportReadinessReport()`)
- **Utility Functions**: Helper functions for API response validation

### `api.ts`
API request and response type definitions:

- **Request Types**: Types for data sent to backend endpoints
- **Response Types**: Types for data received from backend endpoints
- **Error Types**: API error response structures
- **Pagination Types**: Types for paginated API responses

## Usage Examples

### Basic Type Usage

```typescript
import type { QueryInput, ExportReadinessReport } from '@/types';

const query: QueryInput = {
  productName: 'Organic Turmeric Powder',
  destinationCountry: 'United States',
  businessType: 'Manufacturing',
  companySize: 'Small',
};

function displayReport(report: ExportReadinessReport) {
  console.log(`HS Code: ${report.hsCode.code}`);
  console.log(`Risk Score: ${report.riskScore}`);
}
```

### Runtime Type Validation

```typescript
import { isExportReadinessReport, validateApiResponse } from '@/types';

// Validate unknown API response
async function fetchReport(reportId: string) {
  const response = await fetch(`/api/reports/${reportId}`);
  const json = await response.json();
  
  // Throws error if validation fails
  const report = validateApiResponse(json, isExportReadinessReport);
  return report;
}

// Safe type checking
function processData(data: unknown) {
  if (isExportReadinessReport(data)) {
    // TypeScript knows data is ExportReadinessReport here
    console.log(data.reportId);
  }
}
```

### API Request/Response Types

```typescript
import type { 
  GenerateReportRequest, 
  GenerateReportResponse,
  ApiError 
} from '@/types';

async function generateReport(
  request: GenerateReportRequest
): Promise<GenerateReportResponse> {
  const response = await fetch('/api/reports/generate', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(request),
  });
  
  if (!response.ok) {
    const error: ApiError = await response.json();
    throw new Error(error.detail);
  }
  
  return response.json();
}
```

### Type Guards with API Calls

```typescript
import { parseApiResponse, isExportReadinessReport } from '@/types';

async function getReport(reportId: string) {
  const response = await fetch(`/api/reports/${reportId}`);
  
  // Automatically validates and parses response
  const report = await parseApiResponse(response, isExportReadinessReport);
  return report;
}
```

## Type Safety Best Practices

### 1. Always Use Type Guards for API Responses

```typescript
// ❌ Bad - No validation
const data = await response.json();
const report = data as ExportReadinessReport; // Unsafe cast

// ✅ Good - Runtime validation
const data = await response.json();
const report = validateApiResponse(data, isExportReadinessReport);
```

### 2. Use Strict Type Checking

```typescript
// ❌ Bad - Loose typing
function processReport(report: any) {
  console.log(report.reportId);
}

// ✅ Good - Strict typing
function processReport(report: ExportReadinessReport) {
  console.log(report.reportId);
}
```

### 3. Leverage Type Inference

```typescript
// ✅ Good - Let TypeScript infer types
const certifications = report.certifications.filter(
  cert => cert.mandatory && cert.priority === 'high'
);
// TypeScript knows certifications is Certification[]
```

### 4. Use Discriminated Unions

```typescript
// Report status is a discriminated union
function handleReport(report: ExportReadinessReport) {
  switch (report.status) {
    case 'completed':
      // Handle completed report
      break;
    case 'processing':
      // Show loading state
      break;
    case 'failed':
      // Show error
      break;
  }
}
```

## Naming Conventions

### Backend to Frontend Mapping

The TypeScript interfaces use camelCase naming to follow JavaScript conventions, while backend Pydantic models use snake_case. The mapping is consistent:

| Backend (Python)        | Frontend (TypeScript)   |
|------------------------|-------------------------|
| `user_id`              | `userId`                |
| `estimated_cost`       | `estimatedCost`         |
| `hs_code`              | `hsCode`                |
| `business_type`        | `businessType`          |
| `cash_flow_timeline`   | `cashFlowTimeline`      |

### Type Naming Patterns

- **Interfaces**: PascalCase (e.g., `ExportReadinessReport`)
- **Type Unions**: PascalCase (e.g., `BusinessType`)
- **Type Guards**: camelCase with `is` prefix (e.g., `isExportReadinessReport`)
- **API Types**: PascalCase with suffix (e.g., `GenerateReportRequest`, `GetReportResponse`)

## Adding New Types

When adding new types to match backend models:

1. **Add the interface** to `index.ts` in the appropriate section
2. **Create type guards** in `guards.ts` for runtime validation
3. **Add API types** in `api.ts` if the type is used in API requests/responses
4. **Update this README** with usage examples if needed

Example:

```typescript
// 1. Add interface in index.ts
export interface NewFeature {
  id: string;
  name: string;
  enabled: boolean;
}

// 2. Add type guard in guards.ts
export function isNewFeature(value: unknown): value is NewFeature {
  if (typeof value !== 'object' || value === null) return false;
  const obj = value as Record<string, unknown>;
  return (
    typeof obj.id === 'string' &&
    typeof obj.name === 'string' &&
    typeof obj.enabled === 'boolean'
  );
}

// 3. Add API types in api.ts (if needed)
export interface GetNewFeatureResponse {
  feature: NewFeature;
}
```

## Type Validation Performance

Type guards perform runtime validation which has a small performance cost. For optimal performance:

- **Validate at boundaries**: Only validate data when it enters your application (API responses, user input)
- **Trust internal data**: Once validated, trust the types within your application
- **Cache validation results**: Don't re-validate the same data multiple times

```typescript
// ✅ Good - Validate once at the boundary
const report = await parseApiResponse(response, isExportReadinessReport);
processReport(report); // No need to validate again

// ❌ Bad - Unnecessary re-validation
function processReport(report: unknown) {
  if (isExportReadinessReport(report)) {
    // Validating every time is wasteful
  }
}
```

## Testing with Types

Use type guards in tests to ensure API contracts are maintained:

```typescript
import { isExportReadinessReport } from '@/types';

describe('Report API', () => {
  it('should return valid report structure', async () => {
    const response = await fetch('/api/reports/test-id');
    const data = await response.json();
    
    expect(isExportReadinessReport(data)).toBe(true);
  });
});
```

## Related Documentation

- Backend Pydantic models: `/backend/models/`
- API documentation: `/backend/routers/`
- Design document: `/.kiro/specs/export-readiness-platform/design.md`
