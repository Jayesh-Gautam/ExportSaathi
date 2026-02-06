/**
 * ChatInterface Component Tests
 * 
 * Tests for the chat interface component including:
 * - Message display and formatting
 * - User input and submission
 * - Loading states
 * - Source citations
 * - Error handling
 * 
 * Requirements: 7.1, 7.3, 7.7
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { ChatInterface } from './ChatInterface';
import type { QueryContext } from '../types';

// Mock fetch globally
global.fetch = vi.fn();

const mockContext: QueryContext = {
  reportId: 'report-123',
  productType: 'LED Bulbs',
  destinationCountry: 'US',
};

const mockSessionId = 'sess-abc123';

describe('ChatInterface', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    (global.fetch as any).mockClear();
  });

  describe('Initial Render', () => {
    it('should render chat interface with header', () => {
      render(
        <ChatInterface
          sessionId={mockSessionId}
          initialContext={mockContext}
        />
      );

      expect(screen.getByText('Ask ExportSathi')).toBeInTheDocument();
      expect(screen.getByText('Get answers about your export requirements')).toBeInTheDocument();
    });

    it('should display empty state with example questions', () => {
      render(
        <ChatInterface
          sessionId={mockSessionId}
          initialContext={mockContext}
        />
      );

      expect(screen.getByText('Start a Conversation')).toBeInTheDocument();
      expect(screen.getByText(/What documents do I need for FDA certification/)).toBeInTheDocument();
    });

    it('should display session ID in header', () => {
      render(
        <ChatInterface
          sessionId={mockSessionId}
          initialContext={mockContext}
        />
      );

      expect(screen.getByText(/Session: sess-abc/)).toBeInTheDocument();
    });

    it('should render input field and send button', () => {
      render(
        <ChatInterface
          sessionId={mockSessionId}
          initialContext={mockContext}
        />
      );

      const input = screen.getByPlaceholderText('Ask a question about your export requirements...');
      expect(input).toBeInTheDocument();
      expect(input).toHaveAttribute('maxLength', '1000');
      
      const sendButton = screen.getByRole('button');
      expect(sendButton).toBeInTheDocument();
    });

    it('should display info footer about AI-powered guidance', () => {
      render(
        <ChatInterface
          sessionId={mockSessionId}
          initialContext={mockContext}
        />
      );

      expect(screen.getByText('AI-Powered Guidance')).toBeInTheDocument();
      expect(screen.getByText(/All responses are grounded in regulatory documents/)).toBeInTheDocument();
    });
  });

  describe('User Input', () => {
    it('should update input value when user types', () => {
      render(
        <ChatInterface
          sessionId={mockSessionId}
          initialContext={mockContext}
        />
      );

      const input = screen.getByPlaceholderText('Ask a question about your export requirements...') as HTMLTextAreaElement;
      fireEvent.change(input, { target: { value: 'What is FDA certification?' } });

      expect(input.value).toBe('What is FDA certification?');
    });

    it('should display character count', () => {
      render(
        <ChatInterface
          sessionId={mockSessionId}
          initialContext={mockContext}
        />
      );

      const input = screen.getByPlaceholderText('Ask a question about your export requirements...');
      fireEvent.change(input, { target: { value: 'Test question' } });

      expect(screen.getByText('13/1000')).toBeInTheDocument();
    });

    it('should disable send button when input is empty', () => {
      render(
        <ChatInterface
          sessionId={mockSessionId}
          initialContext={mockContext}
        />
      );

      const sendButton = screen.getByRole('button');
      expect(sendButton).toBeDisabled();
    });

    it('should enable send button when input has text', () => {
      render(
        <ChatInterface
          sessionId={mockSessionId}
          initialContext={mockContext}
        />
      );

      const input = screen.getByPlaceholderText('Ask a question about your export requirements...');
      const sendButton = screen.getByRole('button');

      fireEvent.change(input, { target: { value: 'Test question' } });
      expect(sendButton).not.toBeDisabled();
    });

    it('should clear input after successful submission', async () => {
      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          message_id: 'msg-123',
          answer: 'Test response',
          sources: [],
          timestamp: new Date().toISOString(),
        }),
      });

      render(
        <ChatInterface
          sessionId={mockSessionId}
          initialContext={mockContext}
        />
      );

      const input = screen.getByPlaceholderText('Ask a question about your export requirements...') as HTMLTextAreaElement;
      fireEvent.change(input, { target: { value: 'Test question' } });
      
      const sendButton = screen.getByRole('button');
      fireEvent.click(sendButton);

      await waitFor(() => {
        expect(input.value).toBe('');
      });
    });
  });

  describe('Message Submission', () => {
    it('should send message to API when form is submitted', async () => {
      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          message_id: 'msg-123',
          answer: 'Test response',
          sources: [],
          timestamp: new Date().toISOString(),
        }),
      });

      render(
        <ChatInterface
          sessionId={mockSessionId}
          initialContext={mockContext}
        />
      );

      const input = screen.getByPlaceholderText('Ask a question about your export requirements...');
      fireEvent.change(input, { target: { value: 'What is FDA certification?' } });
      
      const sendButton = screen.getByRole('button');
      fireEvent.click(sendButton);

      await waitFor(() => {
        expect(global.fetch).toHaveBeenCalledWith('/api/chat', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            session_id: mockSessionId,
            question: 'What is FDA certification?',
            context: mockContext,
          }),
        });
      });
    });

    it('should call onSendMessage callback when provided', async () => {
      const onSendMessage = vi.fn();
      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          message_id: 'msg-123',
          answer: 'Test response',
          sources: [],
          timestamp: new Date().toISOString(),
        }),
      });

      render(
        <ChatInterface
          sessionId={mockSessionId}
          initialContext={mockContext}
          onSendMessage={onSendMessage}
        />
      );

      const input = screen.getByPlaceholderText('Ask a question about your export requirements...');
      fireEvent.change(input, { target: { value: 'Test question' } });
      
      const sendButton = screen.getByRole('button');
      fireEvent.click(sendButton);

      expect(onSendMessage).toHaveBeenCalledWith('Test question');
    });
  });

  describe('Message Display', () => {
    it('should display user message after submission', async () => {
      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          message_id: 'msg-123',
          answer: 'Test response',
          sources: [],
          timestamp: new Date().toISOString(),
        }),
      });

      render(
        <ChatInterface
          sessionId={mockSessionId}
          initialContext={mockContext}
        />
      );

      const input = screen.getByPlaceholderText('Ask a question about your export requirements...');
      fireEvent.change(input, { target: { value: 'What is FDA certification?' } });
      
      const sendButton = screen.getByRole('button');
      fireEvent.click(sendButton);

      await waitFor(() => {
        expect(screen.getByText('What is FDA certification?')).toBeInTheDocument();
        expect(screen.getByText('You')).toBeInTheDocument();
      });
    });

    it('should display assistant response after API call', async () => {
      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          message_id: 'msg-123',
          answer: 'FDA certification is required for food and medical products.',
          sources: [],
          timestamp: new Date().toISOString(),
        }),
      });

      render(
        <ChatInterface
          sessionId={mockSessionId}
          initialContext={mockContext}
        />
      );

      const input = screen.getByPlaceholderText('Ask a question about your export requirements...');
      fireEvent.change(input, { target: { value: 'What is FDA certification?' } });
      
      const sendButton = screen.getByRole('button');
      fireEvent.click(sendButton);

      await waitFor(() => {
        expect(screen.getByText('FDA certification is required for food and medical products.')).toBeInTheDocument();
        expect(screen.getByText('ExportSathi AI')).toBeInTheDocument();
      });
    });

    it('should display user and assistant messages with distinct styling', async () => {
      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          message_id: 'msg-123',
          answer: 'Test response',
          sources: [],
          timestamp: new Date().toISOString(),
        }),
      });

      render(
        <ChatInterface
          sessionId={mockSessionId}
          initialContext={mockContext}
        />
      );

      const input = screen.getByPlaceholderText('Ask a question about your export requirements...');
      fireEvent.change(input, { target: { value: 'Test question' } });
      
      const sendButton = screen.getByRole('button');
      fireEvent.click(sendButton);

      await waitFor(() => {
        const userMessage = screen.getByText('Test question').closest('div');
        const assistantMessage = screen.getByText('Test response').closest('div');
        
        expect(userMessage).toHaveClass('bg-blue-600');
        expect(assistantMessage).toHaveClass('bg-gray-100');
      });
    });
  });

  describe('Source Citations', () => {
    it('should display source citations for assistant messages', async () => {
      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          message_id: 'msg-123',
          answer: 'FDA certification is required.',
          sources: [
            {
              title: 'FDA Regulations',
              excerpt: 'All food products must be FDA certified.',
              source: 'FDA.gov',
              url: 'https://fda.gov/regulations',
            },
          ],
          timestamp: new Date().toISOString(),
        }),
      });

      render(
        <ChatInterface
          sessionId={mockSessionId}
          initialContext={mockContext}
        />
      );

      const input = screen.getByPlaceholderText('Ask a question about your export requirements...');
      fireEvent.change(input, { target: { value: 'What is FDA certification?' } });
      
      const sendButton = screen.getByRole('button');
      fireEvent.click(sendButton);

      await waitFor(() => {
        expect(screen.getByText('Sources:')).toBeInTheDocument();
        expect(screen.getByText('FDA Regulations')).toBeInTheDocument();
        expect(screen.getByText('All food products must be FDA certified.')).toBeInTheDocument();
        expect(screen.getByText('Source: FDA.gov')).toBeInTheDocument();
      });
    });

    it('should display clickable links for sources with URLs', async () => {
      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          message_id: 'msg-123',
          answer: 'Test response',
          sources: [
            {
              title: 'Test Source',
              url: 'https://example.com',
            },
          ],
          timestamp: new Date().toISOString(),
        }),
      });

      render(
        <ChatInterface
          sessionId={mockSessionId}
          initialContext={mockContext}
        />
      );

      const input = screen.getByPlaceholderText('Ask a question about your export requirements...');
      fireEvent.change(input, { target: { value: 'Test question' } });
      
      const sendButton = screen.getByRole('button');
      fireEvent.click(sendButton);

      await waitFor(() => {
        const link = screen.getByRole('link');
        expect(link).toHaveAttribute('href', 'https://example.com');
        expect(link).toHaveAttribute('target', '_blank');
        expect(link).toHaveAttribute('rel', 'noopener noreferrer');
      });
    });
  });

  describe('Loading State', () => {
    it('should display loading indicator while waiting for response', async () => {
      (global.fetch as any).mockImplementationOnce(
        () => new Promise(resolve => setTimeout(() => resolve({
          ok: true,
          json: async () => ({
            message_id: 'msg-123',
            answer: 'Test response',
            sources: [],
            timestamp: new Date().toISOString(),
          }),
        }), 100))
      );

      render(
        <ChatInterface
          sessionId={mockSessionId}
          initialContext={mockContext}
        />
      );

      const input = screen.getByPlaceholderText('Ask a question about your export requirements...');
      fireEvent.change(input, { target: { value: 'Test question' } });
      
      const sendButton = screen.getByRole('button');
      fireEvent.click(sendButton);

      expect(screen.getByText('Thinking...')).toBeInTheDocument();

      await waitFor(() => {
        expect(screen.queryByText('Thinking...')).not.toBeInTheDocument();
      }, { timeout: 2000 });
    });

    it('should disable input and button during loading', async () => {
      (global.fetch as any).mockImplementationOnce(
        () => new Promise(resolve => setTimeout(() => resolve({
          ok: true,
          json: async () => ({
            message_id: 'msg-123',
            answer: 'Test response',
            sources: [],
            timestamp: new Date().toISOString(),
          }),
        }), 100))
      );

      render(
        <ChatInterface
          sessionId={mockSessionId}
          initialContext={mockContext}
        />
      );

      const input = screen.getByPlaceholderText('Ask a question about your export requirements...');
      fireEvent.change(input, { target: { value: 'Test question' } });
      
      const sendButton = screen.getByRole('button');
      fireEvent.click(sendButton);

      expect(input).toBeDisabled();
      expect(sendButton).toBeDisabled();

      await waitFor(() => {
        expect(input).not.toBeDisabled();
      }, { timeout: 2000 });
    });
  });

  describe('Error Handling', () => {
    it('should display error message when API call fails', async () => {
      (global.fetch as any).mockRejectedValueOnce(new Error('Network error'));

      render(
        <ChatInterface
          sessionId={mockSessionId}
          initialContext={mockContext}
        />
      );

      const input = screen.getByPlaceholderText('Ask a question about your export requirements...');
      fireEvent.change(input, { target: { value: 'Test question' } });
      
      const sendButton = screen.getByRole('button');
      fireEvent.click(sendButton);

      await waitFor(() => {
        expect(screen.getByText('Network error')).toBeInTheDocument();
      });
    });

    it('should display error message in chat when API returns error', async () => {
      (global.fetch as any).mockResolvedValueOnce({
        ok: false,
        json: async () => ({
          detail: 'Invalid session ID',
        }),
      });

      render(
        <ChatInterface
          sessionId={mockSessionId}
          initialContext={mockContext}
        />
      );

      const input = screen.getByPlaceholderText('Ask a question about your export requirements...');
      fireEvent.change(input, { target: { value: 'Test question' } });
      
      const sendButton = screen.getByRole('button');
      fireEvent.click(sendButton);

      await waitFor(() => {
        expect(screen.getByText('Sorry, I encountered an error processing your question. Please try again.')).toBeInTheDocument();
      });
    });

    it('should clear error when new message is sent', async () => {
      (global.fetch as any)
        .mockRejectedValueOnce(new Error('Network error'))
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({
            message_id: 'msg-123',
            answer: 'Test response',
            sources: [],
            timestamp: new Date().toISOString(),
          }),
        });

      render(
        <ChatInterface
          sessionId={mockSessionId}
          initialContext={mockContext}
        />
      );

      const input = screen.getByPlaceholderText('Ask a question about your export requirements...');
      fireEvent.change(input, { target: { value: 'Test question' } });
      
      const sendButton = screen.getByRole('button');
      fireEvent.click(sendButton);

      await waitFor(() => {
        expect(screen.getByText('Network error')).toBeInTheDocument();
      });

      fireEvent.change(input, { target: { value: 'Another question' } });
      fireEvent.click(sendButton);

      await waitFor(() => {
        expect(screen.queryByText('Network error')).not.toBeInTheDocument();
      });
    });
  });
});
