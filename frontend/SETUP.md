# Frontend Setup Guide

This guide will help you set up the ExportSathi frontend application.

## Prerequisites

Before you begin, ensure you have the following installed:

- **Node.js** (version 18 or higher)
- **npm** (comes with Node.js)
- **Git** (for version control)

### Check Prerequisites

```bash
# Check Node.js version
node --version  # Should be v18.x.x or higher

# Check npm version
npm --version   # Should be 9.x.x or higher
```

## Installation Steps

### 1. Navigate to Frontend Directory

```bash
cd frontend
```

### 2. Install Dependencies

```bash
npm install
```

This will install all required packages including:
- React and React DOM
- React Router for navigation
- Axios for API calls
- React Query for server state management
- Tailwind CSS for styling
- TypeScript and related tools
- Vite for development and building

### 3. Create Environment File

```bash
# Copy the example environment file
cp .env.example .env
```

Edit `.env` and configure:

```env
# Backend API URL
VITE_API_BASE_URL=http://localhost:8000
```

### 4. Verify Installation

```bash
# Check if all dependencies are installed
npm list --depth=0
```

## Development

### Start Development Server

```bash
npm run dev
```

The application will start at: **http://localhost:3000**

You should see:
```
  VITE v5.0.12  ready in 500 ms

  ➜  Local:   http://localhost:3000/
  ➜  Network: use --host to expose
  ➜  press h to show help
```

### Development Features

- **Hot Module Replacement (HMR)** - Changes reflect instantly
- **Fast Refresh** - React components update without losing state
- **TypeScript Checking** - Real-time type checking
- **Proxy to Backend** - API calls to `/api/*` are proxied to backend

## Building for Production

### Build the Application

```bash
npm run build
```

This will:
1. Run TypeScript compiler to check types
2. Build optimized production bundle
3. Output to `dist/` directory

### Preview Production Build

```bash
npm run preview
```

This starts a local server to preview the production build.

## Project Structure Overview

```
frontend/
├── src/
│   ├── components/
│   │   └── common/          # Reusable UI components
│   │       ├── Button.tsx
│   │       ├── Input.tsx
│   │       ├── Select.tsx
│   │       ├── Modal.tsx
│   │       ├── LoadingSpinner.tsx
│   │       └── ErrorBoundary.tsx
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
│   ├── types/               # TypeScript types
│   ├── App.tsx              # Main app component
│   ├── main.tsx             # Entry point
│   └── index.css            # Global styles
├── public/                  # Static assets
├── package.json
├── vite.config.ts           # Vite configuration
├── tailwind.config.js       # Tailwind CSS configuration
└── tsconfig.json            # TypeScript configuration
```

## Key Technologies

### React 18
- Functional components with hooks
- Concurrent rendering features
- Automatic batching

### TypeScript
- Type safety for all components
- Better IDE support
- Catch errors at compile time

### Vite
- Lightning-fast dev server
- Optimized production builds
- Native ES modules support

### Tailwind CSS
- Utility-first CSS framework
- Responsive design utilities
- Custom color palette

### React Router
- Client-side routing
- Navigation between pages
- URL parameter handling

### Axios
- HTTP client for API calls
- Request/response interceptors
- Automatic JSON transformation

### React Query
- Server state management
- Automatic caching
- Background refetching
- Optimistic updates

## Configuration Files

### vite.config.ts
```typescript
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
})
```

### tailwind.config.js
```javascript
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {},
  },
  plugins: [],
}
```

## Common Tasks

### Add a New Page

1. Create page component in `src/pages/`:
```typescript
// src/pages/NewPage.tsx
import React from 'react';

export const NewPage: React.FC = () => {
  return (
    <div className="px-4 py-6">
      <h2 className="text-2xl font-bold">New Page</h2>
    </div>
  );
};
```

2. Export from `src/pages/index.ts`:
```typescript
export { NewPage } from './NewPage';
```

3. Add route in `src/App.tsx`:
```typescript
import { NewPage } from './pages';

// In Routes:
<Route path="/new" element={<NewPage />} />
```

### Add a New Component

1. Create component in `src/components/`:
```typescript
// src/components/MyComponent.tsx
import React from 'react';

interface MyComponentProps {
  title: string;
}

export const MyComponent: React.FC<MyComponentProps> = ({ title }) => {
  return <div>{title}</div>;
};
```

2. Use in pages or other components:
```typescript
import { MyComponent } from '../components/MyComponent';

<MyComponent title="Hello" />
```

### Add API Endpoint

1. Add method to `src/services/api.ts`:
```typescript
export const api = {
  // ... existing methods
  
  myNewEndpoint: (data: any) => 
    apiClient.post('/api/my-endpoint', data),
};
```

2. Use in components:
```typescript
import { api } from '../services/api';

const response = await api.myNewEndpoint({ foo: 'bar' });
```

## Troubleshooting

### Port Already in Use

If port 3000 is already in use:

```bash
# Kill process on port 3000 (Windows)
netstat -ano | findstr :3000
taskkill /PID <PID> /F

# Or use a different port
npm run dev -- --port 3001
```

### Module Not Found

```bash
# Clear node_modules and reinstall
rm -rf node_modules package-lock.json
npm install
```

### TypeScript Errors

```bash
# Check TypeScript configuration
npx tsc --noEmit

# Update TypeScript
npm install -D typescript@latest
```

### Build Errors

```bash
# Clear Vite cache
rm -rf node_modules/.vite

# Rebuild
npm run build
```

## Testing

### Run Tests

```bash
npm test
```

### Run Tests with UI

```bash
npm run test:ui
```

### Run Tests in Watch Mode

```bash
npm test -- --watch
```

## Next Steps

After setup is complete:

1. **Start Backend** - Ensure backend API is running on port 8000
2. **Test Navigation** - Click through all pages to verify routing
3. **Test API Integration** - Try making API calls from the frontend
4. **Customize Styling** - Modify Tailwind configuration as needed
5. **Add Features** - Start implementing components for each page

## Resources

- [React Documentation](https://react.dev/)
- [TypeScript Documentation](https://www.typescriptlang.org/docs/)
- [Vite Documentation](https://vitejs.dev/)
- [Tailwind CSS Documentation](https://tailwindcss.com/docs)
- [React Router Documentation](https://reactrouter.com/)
- [React Query Documentation](https://tanstack.com/query/latest)

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Review the main README.md
3. Check backend API documentation
4. Contact the development team
