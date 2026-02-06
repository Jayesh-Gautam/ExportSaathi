# ExportSathi Frontend Component Structure

## Application Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                         main.tsx                             │
│  ┌────────────────────────────────────────────────────────┐ │
│  │              QueryClientProvider                       │ │
│  │  ┌──────────────────────────────────────────────────┐ │ │
│  │  │            BrowserRouter                         │ │ │
│  │  │  ┌────────────────────────────────────────────┐ │ │ │
│  │  │  │          ErrorBoundary                     │ │ │ │
│  │  │  │  ┌──────────────────────────────────────┐ │ │ │ │
│  │  │  │  │           App.tsx                    │ │ │ │ │
│  │  │  │  │                                      │ │ │ │ │
│  │  │  │  │  ┌────────────────────────────────┐ │ │ │ │ │
│  │  │  │  │  │         Header                 │ │ │ │ │ │
│  │  │  │  │  │  - Logo & Title                │ │ │ │ │ │
│  │  │  │  │  │  - Navigation Bar              │ │ │ │ │ │
│  │  │  │  │  └────────────────────────────────┘ │ │ │ │ │
│  │  │  │  │                                      │ │ │ │ │
│  │  │  │  │  ┌────────────────────────────────┐ │ │ │ │ │
│  │  │  │  │  │         Routes                 │ │ │ │ │ │
│  │  │  │  │  │  - HomePage                    │ │ │ │ │ │
│  │  │  │  │  │  - ReportsPage                 │ │ │ │ │ │
│  │  │  │  │  │  - CertificationsPage          │ │ │ │ │ │
│  │  │  │  │  │  - DocumentsPage               │ │ │ │ │ │
│  │  │  │  │  │  - FinancePage                 │ │ │ │ │ │
│  │  │  │  │  │  - LogisticsPage               │ │ │ │ │ │
│  │  │  │  │  └────────────────────────────────┘ │ │ │ │ │
│  │  │  │  │                                      │ │ │ │ │
│  │  │  │  │  ┌────────────────────────────────┐ │ │ │ │ │
│  │  │  │  │  │         Footer                 │ │ │ │ │ │
│  │  │  │  │  └────────────────────────────────┘ │ │ │ │ │
│  │  │  │  └──────────────────────────────────────┘ │ │ │ │
│  │  │  └────────────────────────────────────────────┘ │ │ │
│  │  └──────────────────────────────────────────────────┘ │ │
│  └────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

## Component Hierarchy

### Pages

```
HomePage
├── Feature Cards (3)
│   ├── HS Code Prediction
│   ├── Certification Guidance
│   └── Finance Planning
├── CTA Button
└── Benefits List

ReportsPage
└── Report List (to be implemented)

CertificationsPage
└── Certification Grid (6 cards)
    ├── US FDA
    ├── CE Marking
    ├── REACH
    ├── BIS
    ├── ZED
    └── SOFTEX

DocumentsPage
└── Document Type List (6 types)
    ├── Commercial Invoice
    ├── Packing List
    ├── Shipping Bill
    ├── GST LUT
    ├── SOFTEX
    └── Certificate of Origin

FinancePage
└── Finance Features Grid (4 cards)
    ├── Working Capital Planning
    ├── RoDTEP Calculator
    ├── Pre-Shipment Credit
    └── Currency Hedging

LogisticsPage
└── Risk Assessment Features (5 cards)
    ├── LCL vs FCL Analysis
    ├── RMS Probability
    ├── Route Delay Prediction
    ├── Freight Cost Estimation
    └── Insurance Recommendations
```

### Common Components

```
components/common/
├── Button
│   ├── Props: variant, size, isLoading, children
│   └── Variants: primary, secondary, danger, outline
│
├── Input
│   ├── Props: label, error, helperText
│   └── Features: validation, required indicator
│
├── Select
│   ├── Props: label, error, options
│   └── Features: dropdown, validation
│
├── Modal
│   ├── Props: isOpen, onClose, title, size
│   └── Features: backdrop, ESC key, click outside
│
├── LoadingSpinner
│   ├── Props: message, estimatedTime
│   └── Features: animated spinner, status text
│
└── ErrorBoundary
    ├── State: hasError, error
    └── Features: error display, retry button
```

## Data Flow

```
┌─────────────────────────────────────────────────────────────┐
│                      User Interaction                        │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                    React Component                           │
│  ┌────────────────────────────────────────────────────────┐ │
│  │              useState / useApi Hook                    │ │
│  └────────────────────────┬───────────────────────────────┘ │
└───────────────────────────┼─────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                    API Client (Axios)                        │
│  ┌────────────────────────────────────────────────────────┐ │
│  │         Request Interceptor (Add Auth Token)          │ │
│  └────────────────────────┬───────────────────────────────┘ │
└───────────────────────────┼─────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                  Backend API (FastAPI)                       │
│                    http://localhost:8000                     │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                    Response Handling                         │
│  ┌────────────────────────────────────────────────────────┐ │
│  │      Response Interceptor (Handle 401, Errors)        │ │
│  └────────────────────────┬───────────────────────────────┘ │
└───────────────────────────┼─────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                React Query / Component State                 │
│  ┌────────────────────────────────────────────────────────┐ │
│  │         Update UI with Data or Error                  │ │
│  └────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

## State Management Strategy

### Local State (useState)
```
Component-level state for:
- Form inputs
- UI toggles (modals, dropdowns)
- Temporary data
```

### Server State (React Query)
```
API data caching for:
- Reports
- Certifications
- Documents
- Finance analysis
- Logistics data
```

### Persistent State (useLocalStorage)
```
localStorage for:
- User preferences
- Checklist progress
- Draft forms
- Session data
```

## Routing Structure

```
/                           → HomePage
├── /reports                → ReportsPage
│   ├── /reports/new        → (Future) New Report Form
│   └── /reports/:id        → (Future) Report Detail
├── /certifications         → CertificationsPage
│   └── /certifications/:id → (Future) Certification Detail
├── /documents              → DocumentsPage
│   └── /documents/new      → (Future) Document Generator
├── /finance                → FinancePage
│   └── /finance/:reportId  → (Future) Finance Analysis
└── /logistics              → LogisticsPage
    └── /logistics/:reportId → (Future) Logistics Analysis
```

## API Integration Points

```
Pages → API Client → Backend Endpoints

HomePage
└── (No API calls yet)

ReportsPage
├── GET /api/reports
└── GET /api/reports/:id

CertificationsPage
├── GET /api/certifications
└── POST /api/certifications/:id/guidance

DocumentsPage
├── POST /api/documents/generate
└── POST /api/documents/validate

FinancePage
├── GET /api/finance/analysis/:reportId
└── POST /api/finance/rodtep-calculator

LogisticsPage
└── POST /api/logistics/risk-analysis
```

## Custom Hooks Usage

### useLocalStorage
```typescript
// Store checklist progress
const [progress, setProgress] = useLocalStorage('checklist-progress', {});

// Store user preferences
const [theme, setTheme] = useLocalStorage('theme', 'light');
```

### useApi
```typescript
// Generate report
const { data, loading, error, execute } = useApi(api.generateReport);

// Get report
const { data, loading, error, execute } = useApi(api.getReport);
```

## Component Communication

```
Parent Component
├── Props Down ↓
│   ├── Data
│   ├── Callbacks
│   └── Configuration
│
└── Events Up ↑
    ├── onClick
    ├── onChange
    └── onSubmit
```

## Error Handling Flow

```
Error Occurs
├── Component Level
│   ├── Try-Catch Block
│   └── Display Error Message
│
├── API Level
│   ├── Response Interceptor
│   └── Error State in useApi
│
└── Application Level
    ├── ErrorBoundary
    └── Fallback UI
```

## Styling Approach

```
Tailwind CSS Utility Classes
├── Layout
│   ├── Flexbox (flex, items-center, justify-between)
│   ├── Grid (grid, grid-cols-2, gap-4)
│   └── Spacing (p-4, m-2, space-y-4)
│
├── Typography
│   ├── Font Size (text-sm, text-lg, text-2xl)
│   ├── Font Weight (font-medium, font-bold)
│   └── Color (text-gray-600, text-blue-600)
│
├── Colors
│   ├── Background (bg-white, bg-blue-50)
│   ├── Border (border-gray-200, border-blue-500)
│   └── Text (text-gray-900, text-red-600)
│
└── Responsive
    ├── Mobile First (default)
    ├── Tablet (md:)
    └── Desktop (lg:)
```

## Future Component Structure

```
components/
├── common/              ✅ DONE
│   ├── Button
│   ├── Input
│   ├── Select
│   ├── Modal
│   ├── LoadingSpinner
│   └── ErrorBoundary
│
├── forms/               🔜 NEXT
│   ├── QueryForm
│   ├── ProductImageUpload
│   └── CountrySelect
│
├── reports/             🔜 FUTURE
│   ├── ReportCard
│   ├── HSCodeSection
│   ├── CertificationList
│   └── RiskScore
│
├── certifications/      🔜 FUTURE
│   ├── CertificationCard
│   ├── DocumentChecklist
│   └── TestLabList
│
├── documents/           🔜 FUTURE
│   ├── DocumentGenerator
│   ├── DocumentPreview
│   └── ValidationResults
│
├── finance/             🔜 FUTURE
│   ├── CashFlowTimeline
│   ├── RoDTEPCalculator
│   └── WorkingCapitalBreakdown
│
└── logistics/           🔜 FUTURE
    ├── RMSProbability
    ├── LCLvsFCLComparison
    └── FreightEstimator
```

## Performance Considerations

### Code Splitting
```typescript
// Future implementation
const ReportsPage = lazy(() => import('./pages/ReportsPage'));
const CertificationsPage = lazy(() => import('./pages/CertificationsPage'));
```

### Memoization
```typescript
// Use React.memo for expensive components
export const ExpensiveComponent = React.memo(({ data }) => {
  // Component logic
});
```

### React Query Caching
```typescript
// Automatic caching and background refetching
const { data } = useQuery('reports', api.getReports, {
  staleTime: 5 * 60 * 1000, // 5 minutes
  cacheTime: 10 * 60 * 1000, // 10 minutes
});
```

## Accessibility Features

- ✅ Semantic HTML elements
- ✅ ARIA labels and roles
- ✅ Keyboard navigation
- ✅ Focus management
- ✅ Screen reader support
- ✅ Color contrast compliance

## Responsive Breakpoints

```
Mobile:  < 640px   (default)
Tablet:  640px+    (sm:)
Desktop: 768px+    (md:)
Large:   1024px+   (lg:)
XLarge:  1280px+   (xl:)
```

---

This structure provides a solid foundation for building the complete ExportSathi frontend application.
