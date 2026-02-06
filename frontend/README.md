# ExportSathi Frontend

React-based frontend for the ExportSathi AI-Powered Export Compliance & Certification Co-Pilot.

## Tech Stack

- **React 18+** - UI library with functional components and hooks
- **TypeScript** - Type safety and better developer experience
- **Vite** - Fast build tool and dev server
- **React Router** - Client-side routing
- **Tailwind CSS** - Utility-first CSS framework
- **Axios** - HTTP client for API calls
- **React Query (@tanstack/react-query)** - Server state management
- **React Hook Form** - Form management
- **Chart.js** - Data visualization for finance timelines
- **Lucide React** - Icon library

## Project Structure

```
frontend/
├── src/
│   ├── components/          # Reusable UI components
│   │   ├── common/          # Common components (Button, Input, Modal, etc.)
│   │   ├── forms/           # Form components (QueryForm, etc.)
│   │   ├── reports/         # Report-related components
│   │   ├── certifications/  # Certification components
│   │   ├── documents/       # Document components
│   │   ├── finance/         # Finance components
│   │   └── logistics/       # Logistics components
│   ├── pages/               # Page components
│   │   ├── HomePage.tsx
│   │   ├── ReportsPage.tsx
│   │   ├── CertificationsPage.tsx
│   │   ├── DocumentsPage.tsx
│   │   ├── FinancePage.tsx
│   │   └── LogisticsPage.tsx
│   ├── hooks/               # Custom React hooks
│   │   ├── useLocalStorage.ts
│   │   └── useApi.ts
│   ├── services/            # API services
│   │   └── api.ts
│   ├── types/               # TypeScript type definitions
│   │   ├── index.ts
│   │   ├── api.ts
│   │   └── guards.ts
│   ├── App.tsx              # Main app component
│   ├── main.tsx             # App entry point
│   └── index.css            # Global styles
├── public/                  # Static assets
├── package.json
├── vite.config.ts
├── tailwind.config.js
└── tsconfig.json
```

## Getting Started

### Prerequisites

- Node.js 18+ and npm
- Backend API running on http://localhost:8000

### Installation

1. Install dependencies:
```bash
npm install
```

2. Create environment file:
```bash
cp .env.example .env
```

3. Update `.env` with your configuration:
```
VITE_API_BASE_URL=http://localhost:8000
```

### Development

Start the development server:
```bash
npm run dev
```

The app will be available at http://localhost:3000

### Build

Build for production:
```bash
npm run build
```

Preview production build:
```bash
npm run preview
```

### Testing

Run tests:
```bash
npm test
```

Run tests with UI:
```bash
npm run test:ui
```

## Key Features

### 1. Component Library

Common reusable components in `src/components/common/`:
- **Button** - Styled button with variants (primary, secondary, danger, outline)
- **Input** - Form input with label, error, and helper text
- **Select** - Dropdown select with options
- **Modal** - Modal dialog with backdrop
- **LoadingSpinner** - Loading indicator with optional message
- **ErrorBoundary** - Error boundary for graceful error handling

### 2. Pages

- **HomePage** - Landing page with feature overview
- **ReportsPage** - Export readiness reports list and details
- **CertificationsPage** - Certification guidance and navigation
- **DocumentsPage** - Document generation and validation
- **FinancePage** - Finance readiness analysis
- **LogisticsPage** - Logistics risk assessment

### 3. Custom Hooks

- **useLocalStorage** - Persist state to localStorage
- **useApi** - API calls with loading and error states

### 4. API Client

Centralized API client in `src/services/api.ts` with:
- Axios instance with base URL configuration
- Request interceptor for authentication tokens
- Response interceptor for error handling
- Type-safe API methods for all endpoints

### 5. Routing

React Router setup with:
- Navigation bar with active link highlighting
- Route definitions for all pages
- Error boundary wrapping

### 6. Styling

Tailwind CSS configured with:
- Custom color palette
- Responsive design utilities
- Component-specific styles
- Dark mode support (optional)

## API Integration

The frontend communicates with the backend API through the `api` service:

```typescript
import { api } from './services/api';

// Generate report
const response = await api.generateReport(formData);

// Get report
const report = await api.getReport(reportId);

// Submit chat question
const answer = await api.submitQuestion({ question, sessionId });
```

## State Management

- **Local State** - React useState for component-level state
- **Server State** - React Query for API data caching and synchronization
- **Persistent State** - useLocalStorage hook for localStorage persistence
- **Form State** - React Hook Form for form management

## Type Safety

TypeScript interfaces and types defined in `src/types/`:
- API request/response types
- Domain model types
- Type guards for runtime validation

## Best Practices

1. **Component Organization** - Separate concerns (presentation, logic, data)
2. **Type Safety** - Use TypeScript for all components and functions
3. **Error Handling** - Use ErrorBoundary and try-catch blocks
4. **Loading States** - Show loading indicators during async operations
5. **Accessibility** - Use semantic HTML and ARIA attributes
6. **Responsive Design** - Mobile-first approach with Tailwind
7. **Code Splitting** - Lazy load routes and components when needed

## Environment Variables

- `VITE_API_BASE_URL` - Backend API base URL (default: http://localhost:8000)

## Deployment

### AWS Amplify

1. Connect GitHub repository to AWS Amplify
2. Configure build settings:
   - Build command: `npm run build`
   - Output directory: `dist`
3. Set environment variables in Amplify console
4. Deploy

### AWS S3 + CloudFront

1. Build the app: `npm run build`
2. Upload `dist/` contents to S3 bucket
3. Configure S3 for static website hosting
4. Create CloudFront distribution pointing to S3
5. Update DNS records

## Contributing

1. Create feature branch from `main`
2. Make changes with proper TypeScript types
3. Test thoroughly
4. Submit pull request

## License

Proprietary - ExportSathi
