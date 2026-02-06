# ChatInterface Component

## Overview

The `ChatInterface` component provides an interactive Q&A chat interface for users to ask follow-up questions about their export requirements. It maintains conversation context and displays AI-generated responses with source citations from regulatory documents.

## Features

- **Conversation Display**: Shows user and assistant messages in a clean, scrollable interface
- **Distinct Message Styling**: User messages appear in blue on the right, assistant messages in gray on the left
- **Message Input**: Multi-line textarea with character counter (max 1000 characters)
- **Loading Indicators**: Animated "Thinking..." indicator while waiting for responses
- **Source Citations**: Displays regulatory document sources with clickable links
- **Auto-scroll**: Automatically scrolls to the latest message
- **Error Handling**: Displays user-friendly error messages for API failures
- **Keyboard Shortcuts**: Enter to send, Shift+Enter for new line
- **Session Management**: Maintains conversation context across multiple questions

## Requirements

Implements the following requirements:
- **7.1**: Chat interface for follow-up questions
- **7.3**: Display responses while maintaining conversation history
- **7.7**: Provide source citations from regulatory documents

## Props

```typescript
interface ChatInterfaceProps {
  sessionId: string;           // Unique session identifier (e.g., "sess-abc123")
  initialContext: QueryContext; // Context from the export readiness report
  onSendMessage?: (question: string) => void; // Optional callback when message is sent
}

interface QueryContext {
  reportId: string;           // ID of the export readiness report
  productType: string;        // Product being exported
  destinationCountry: string; // Target export country
}
```

## Usage

### Basic Usage

```tsx
import { ChatInterface } from './components';

function ReportPage() {
  const sessionId = 'sess-' + generateUniqueId();
  const context = {
    reportId: 'report-123',
    productType: 'LED Bulbs',
    destinationCountry: 'US',
  };

  return (
    <div className="h-screen">
      <ChatInterface
        sessionId={sessionId}
        initialContext={context}
      />
    </div>
  );
}
```

### With Callback

```tsx
import { ChatInterface } from './components';

function ReportPage() {
  const handleSendMessage = (question: string) => {
    console.log('User asked:', question);
    // Track analytics, etc.
  };

  return (
    <ChatInterface
      sessionId={sessionId}
      initialContext={context}
      onSendMessage={handleSendMessage}
    />
  );
}
```

## API Integration

The component sends POST requests to `/api/chat` with the following payload:

```json
{
  "session_id": "sess-abc123",
  "question": "What documents do I need for FDA certification?",
  "context": {
    "report_id": "report-123",
    "product_type": "LED Bulbs",
    "destination_country": "US"
  }
}
```

Expected response format:

```json
{
  "message_id": "msg-456",
  "answer": "For FDA certification, you need...",
  "sources": [
    {
      "title": "FDA Regulations",
      "excerpt": "All food products must be FDA certified.",
      "source": "FDA.gov",
      "url": "https://fda.gov/regulations"
    }
  ],
  "timestamp": "2024-01-15T10:30:00Z"
}
```

## Component Structure

```
ChatInterface
├── Header
│   ├── Icon and Title
│   └── Session ID
├── Messages Container
│   ├── Empty State (when no messages)
│   ├── Message Bubbles
│   │   ├── User Messages (right-aligned, blue)
│   │   └── Assistant Messages (left-aligned, gray)
│   │       └── Source Citations
│   └── Loading Indicator
├── Error Display (when errors occur)
├── Input Form
│   ├── Textarea
│   ├── Character Counter
│   └── Send Button
└── Info Footer
```

## Styling

The component uses Tailwind CSS classes for styling:

- **User Messages**: `bg-blue-600 text-white` - Blue background with white text
- **Assistant Messages**: `bg-gray-100 text-gray-900` - Light gray background
- **Source Citations**: White background with border, clickable links
- **Loading State**: Animated bouncing dots
- **Error Messages**: Red background with error icon

## Keyboard Shortcuts

- **Enter**: Submit message
- **Shift + Enter**: Add new line in textarea

## State Management

The component manages the following state:

- `messages`: Array of chat messages (user and assistant)
- `inputText`: Current text in the input field
- `isLoading`: Whether a response is being generated
- `error`: Error message to display (if any)

## Auto-scroll Behavior

The component automatically scrolls to the bottom when:
- A new message is added (user or assistant)
- The component first renders
- The messages array changes

This is implemented using a ref to the bottom of the messages container and `scrollIntoView({ behavior: 'smooth' })`.

## Error Handling

The component handles the following error scenarios:

1. **Network Errors**: Displays error message in error banner
2. **API Errors**: Shows error response from backend
3. **Empty Input**: Disables send button
4. **Loading State**: Disables input and button during API call

When an error occurs, an error message is displayed both in the error banner and as an assistant message in the chat.

## Testing

The component includes comprehensive unit tests covering:

- Initial render and empty state
- User input and character counting
- Message submission and API calls
- Message display with distinct styling
- Source citation display
- Loading states
- Error handling
- Auto-scroll behavior

Run tests with:

```bash
npm test -- ChatInterface.test.tsx
```

## Accessibility

- Semantic HTML with proper roles
- Keyboard navigation support
- Focus management (input auto-focuses on mount)
- ARIA labels for interactive elements
- External links open in new tab with `rel="noopener noreferrer"`

## Performance Considerations

- Messages are rendered efficiently with React keys
- Auto-scroll uses `scrollIntoView` with smooth behavior
- Input is debounced through React's controlled component pattern
- API calls are made only on explicit user action (button click or Enter key)

## Future Enhancements

Potential improvements for future versions:

1. **Message History Persistence**: Load previous messages from backend
2. **Typing Indicators**: Show when assistant is typing
3. **Message Reactions**: Allow users to rate responses
4. **Export Chat**: Download conversation as PDF or text
5. **Voice Input**: Speech-to-text for questions
6. **Suggested Questions**: Show common follow-up questions
7. **Rich Text Formatting**: Support markdown in responses
8. **File Attachments**: Allow users to upload documents for context

## Related Components

- `ReportDisplay`: Main report component that can include ChatInterface
- `LoadingSpinner`: Used for loading states
- `Button`: Used for send button

## Dependencies

- React 18+
- TypeScript
- Tailwind CSS
- Common components (Button, LoadingSpinner)

## Browser Support

- Chrome/Edge (latest)
- Firefox (latest)
- Safari (latest)
- Mobile browsers (iOS Safari, Chrome Mobile)

## Notes

- The component requires a valid session ID to function
- Session IDs should be unique per report/user session
- The backend must implement the `/api/chat` endpoint
- Source citations are optional but recommended for transparency
- The component maintains conversation context automatically
