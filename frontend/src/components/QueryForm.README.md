# QueryForm Component

## Overview

The `QueryForm` component is a comprehensive form for collecting product information needed to generate an export readiness report. It's a critical MVP component that serves as the entry point for users to start their export journey.

## Features

### Required Fields
- **Business Type**: Manufacturing MSME, SaaS/Service Exporter, or Merchant Exporter
- **Company Size**: Micro, Small, or Medium (based on annual turnover)
- **Product Name**: Name of the product to export (max 200 characters)
- **Destination Country**: Target export country with autocomplete search

### Optional Fields
- **Product Image**: Upload with preview (JPEG, PNG, WebP up to 10MB)
- **Ingredients/BOM**: List of ingredients or bill of materials (max 2000 characters)
- **Additional Product Details**: Manufacturing process, materials, specifications (max 1000 characters)
- **Monthly Export Volume**: Estimated units per month
- **Price Range per Unit**: Approximate price range in INR
- **Preferred Payment Mode**: LC, TT, DA, DP, or Advance Payment

## Validation

The component implements comprehensive client-side validation:

1. **Product Name**
   - Required field
   - Maximum 200 characters
   - Trimmed whitespace

2. **Destination Country**
   - Required field
   - Must select from autocomplete dropdown

3. **Business Type & Company Size**
   - Both required
   - Validated before submission

4. **Monthly Volume**
   - Optional
   - Must be a valid number if provided

5. **Image Upload**
   - Optional but recommended
   - File type validation (JPEG, PNG, WebP only)
   - File size validation (max 10MB)
   - Shows preview after upload

## Usage

```tsx
import { QueryForm } from './components/QueryForm';

function MyPage() {
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (formData: FormData) => {
    setIsLoading(true);
    try {
      const response = await api.generateReport(formData);
      // Handle response
    } catch (error) {
      // Handle error
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <QueryForm 
      onSubmit={handleSubmit} 
      isLoading={isLoading}
      businessType="Manufacturing" // Optional: pre-fill business type
    />
  );
}
```

## Props

| Prop | Type | Required | Description |
|------|------|----------|-------------|
| `onSubmit` | `(data: FormData) => void` | Yes | Callback function called when form is submitted with valid data |
| `isLoading` | `boolean` | No | Shows loading state on submit button (default: false) |
| `businessType` | `string` | No | Pre-fill and disable business type field |

## Form Submission

When the form is submitted, the `onSubmit` callback receives a `FormData` object containing:

- `productName` (string, required)
- `destinationCountry` (string, required - country code)
- `businessType` (string, required)
- `companySize` (string, required)
- `productImage` (File, optional)
- `ingredients` (string, optional)
- `bom` (string, optional)
- `monthlyVolume` (string, optional)
- `priceRange` (string, optional)
- `paymentMode` (string, optional)

The FormData format is ready for multipart/form-data API submission.

## Country Autocomplete

The component includes a custom autocomplete for country selection:

- Searches by country name or code
- Displays country name and region
- Filters results as user types
- Shows dropdown on focus
- Closes dropdown on selection

Countries are organized by region:
- North America
- Europe
- Asia Pacific
- Middle East
- Africa
- South America

## Image Upload

The image upload feature includes:

1. **Click-to-upload area** with visual feedback
2. **File validation** for type and size
3. **Image preview** after upload
4. **Remove button** to clear uploaded image
5. **Helper text** explaining the benefit

Supported formats: JPEG, JPG, PNG, WebP
Maximum size: 10MB

## Error Handling

The component displays validation errors in multiple ways:

1. **Field-level errors**: Shown below each input field in red
2. **General errors**: Shown at the top of the form (e.g., missing business type)
3. **Inline validation**: Errors clear as user corrects the input

## Accessibility

- All form fields have proper labels
- Required fields marked with asterisk (*)
- Error messages associated with fields
- Keyboard navigation supported
- Focus management for dropdown

## Styling

The component uses Tailwind CSS for styling and follows the design system:

- Consistent spacing and sizing
- Blue color scheme for primary actions
- Red for errors and validation
- Gray for secondary text and borders
- Responsive design for mobile and desktop

## Testing

The component includes comprehensive unit tests covering:

- Rendering all required fields
- Validation for empty fields
- Validation for field length limits
- Form submission with valid data
- Loading state display
- Image upload handling
- Country search and filtering
- Number validation for monthly volume

Run tests with:
```bash
npm test QueryForm.test.tsx
```

## Integration

The QueryForm is integrated into the `NewReportPage` which:

1. Renders the form
2. Handles form submission
3. Calls the backend API
4. Shows loading state
5. Handles errors
6. Navigates to report page on success

## Future Enhancements

Potential improvements for future iterations:

1. **Auto-save**: Save form data to localStorage
2. **Multi-step form**: Break into smaller steps for better UX
3. **Image cropping**: Allow users to crop uploaded images
4. **Drag-and-drop**: Support drag-and-drop for image upload
5. **Multiple images**: Support uploading multiple product images
6. **BOM file upload**: Allow uploading BOM as CSV/Excel file
7. **Product templates**: Pre-fill common product types
8. **Recent searches**: Show recently searched countries
9. **Validation hints**: Show real-time validation hints as user types
10. **Progress indicator**: Show form completion percentage

## Related Components

- `Input`: Reusable input component
- `Select`: Reusable select component
- `Button`: Reusable button component
- `NewReportPage`: Page that uses QueryForm
- `HomePage`: Landing page with CTA to QueryForm

## API Integration

The form data is sent to the backend endpoint:

```
POST /api/reports/generate
Content-Type: multipart/form-data
```

The backend processes the form data and returns:

```json
{
  "reportId": "string",
  "status": "completed" | "processing" | "failed",
  "report": { ... },
  "generatedAt": "ISO 8601 timestamp"
}
```

## Requirements Mapping

This component satisfies the following requirements:

- **Requirement 1.1**: Product and destination input form
- **Requirement 1.2**: Product image upload and processing
- **Requirement 1.3**: Accept valid query and initiate AI engine
- **Requirement 1.4**: Support worldwide country selection
- **Requirement 1.5**: Validation and feedback for invalid inputs

## MVP Focus

The current implementation focuses on:

✅ **Minimal but functional** form with all required fields
✅ **Proper validation** before submission
✅ **Image upload** with preview and validation
✅ **Country autocomplete** for better UX
✅ **Loading state** during submission
✅ **Error handling** with clear messages
✅ **Responsive design** for mobile and desktop
✅ **Accessibility** with proper labels and ARIA attributes

The component is production-ready for MVP launch.
