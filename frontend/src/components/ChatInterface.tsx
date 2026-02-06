/**
 * ChatInterface Component
 * 
 * Interactive Q&A chat interface for follow-up questions about export requirements.
 * Maintains conversation context and displays source citations.
 * 
 * Features:
 * - Display chat messages in conversation format
 * - Show user and assistant messages with distinct styling
 * - Message input field with send button
 * - Loading indicator during response generation
 * - Source citations with links
 * - Auto-scroll to latest message
 * 
 * Requirements: 7.1, 7.3, 7.7
 */

import React, { useState, useRef, useEffect, FormEvent, ChangeEvent } from 'react';
import { Button, LoadingSpinner } from './common';
import type { ChatMessage, QueryContext, Source } from '../types';

interface ChatInterfaceProps {
  sessionId: string;
  initialContext: QueryContext;
  onSendMessage?: (question: string) => void;
}

interface MessageBubbleProps {
  message: ChatMessage;
}

const MessageBubble: React.FC<MessageBubbleProps> = ({ message }) => {
  const isUser = message.role === 'user';
  
  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-4`}>
      <div className={`max-w-3xl ${isUser ? 'ml-12' : 'mr-12'}`}>
        {/* Message Header */}
        <div className={`flex items-center mb-1 ${isUser ? 'justify-end' : 'justify-start'}`}>
          <span className="text-xs text-gray-500">
            {isUser ? 'You' : 'ExportSathi AI'}
          </span>
          <span className="text-xs text-gray-400 ml-2">
            {new Date(message.timestamp).toLocaleTimeString('en-IN', {
              hour: '2-digit',
              minute: '2-digit',
            })}
          </span>
        </div>
        
        {/* Message Content */}
        <div
          className={`rounded-lg px-4 py-3 ${
            isUser
              ? 'bg-blue-600 text-white'
              : 'bg-gray-100 text-gray-900 border border-gray-200'
          }`}
        >
          <p className="whitespace-pre-wrap break-words">{message.content}</p>
        </div>
        
        {/* Source Citations (only for assistant messages) */}
        {!isUser && message.sources && message.sources.length > 0 && (
          <div className="mt-2 space-y-1">
            <p className="text-xs font-medium text-gray-600">Sources:</p>
            {message.sources.map((source, idx) => (
              <div
                key={idx}
                className="text-xs bg-white border border-gray-200 rounded px-3 py-2"
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <p className="font-medium text-gray-900">{source.title}</p>
                    {source.excerpt && (
                      <p className="text-gray-600 mt-1 line-clamp-2">{source.excerpt}</p>
                    )}
                    {source.source && (
                      <p className="text-gray-500 mt-1">Source: {source.source}</p>
                    )}
                  </div>
                  {source.url && (
                    <a
                      href={source.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="ml-2 text-blue-600 hover:text-blue-800 flex-shrink-0"
                    >
                      <svg
                        className="w-4 h-4"
                        fill="none"
                        stroke="currentColor"
                        viewBox="0 0 24 24"
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth={2}
                          d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"
                        />
                      </svg>
                    </a>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export const ChatInterface: React.FC<ChatInterfaceProps> = ({
  sessionId,
  initialContext,
  onSendMessage,
}) => {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputText, setInputText] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  // Auto-scroll to latest message
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Focus input on mount
  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  // Handle input change
  const handleInputChange = (e: ChangeEvent<HTMLTextAreaElement>) => {
    setInputText(e.target.value);
  };

  // Handle form submission
  const handleSubmit = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    
    const question = inputText.trim();
    if (!question || isLoading) {
      return;
    }

    // Clear input and error
    setInputText('');
    setError(null);
    setIsLoading(true);

    // Add user message to chat
    const userMessage: ChatMessage = {
      messageId: `user-${Date.now()}`,
      role: 'user',
      content: question,
      timestamp: new Date().toISOString(),
    };
    setMessages(prev => [...prev, userMessage]);

    // Call parent callback if provided
    if (onSendMessage) {
      onSendMessage(question);
    }

    try {
      // Send message to backend
      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          session_id: sessionId,
          question: question,
          context: initialContext,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to get response');
      }

      const data = await response.json();

      // Add assistant message to chat
      const assistantMessage: ChatMessage = {
        messageId: data.message_id,
        role: 'assistant',
        content: data.answer,
        sources: data.sources,
        timestamp: data.timestamp,
      };
      setMessages(prev => [...prev, assistantMessage]);
    } catch (err) {
      console.error('Chat error:', err);
      setError(err instanceof Error ? err.message : 'Failed to send message');
      
      // Add error message to chat
      const errorMessage: ChatMessage = {
        messageId: `error-${Date.now()}`,
        role: 'assistant',
        content: 'Sorry, I encountered an error processing your question. Please try again.',
        timestamp: new Date().toISOString(),
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
      inputRef.current?.focus();
    }
  };

  // Handle Enter key (submit on Enter, new line on Shift+Enter)
  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e as any);
    }
  };

  return (
    <div className="flex flex-col h-full bg-white rounded-lg shadow-sm border border-gray-200">
      {/* Chat Header */}
      <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200 bg-gray-50">
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 bg-blue-600 rounded-full flex items-center justify-center">
            <svg
              className="w-6 h-6 text-white"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z"
              />
            </svg>
          </div>
          <div>
            <h3 className="text-lg font-semibold text-gray-900">Ask ExportSathi</h3>
            <p className="text-sm text-gray-600">
              Get answers about your export requirements
            </p>
          </div>
        </div>
        
        {/* Session Info */}
        <div className="text-xs text-gray-500">
          Session: {sessionId.substring(0, 8)}...
        </div>
      </div>

      {/* Messages Container */}
      <div className="flex-1 overflow-y-auto px-6 py-4 space-y-4">
        {messages.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-center">
            <svg
              className="w-16 h-16 text-gray-300 mb-4"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"
              />
            </svg>
            <h4 className="text-lg font-medium text-gray-900 mb-2">
              Start a Conversation
            </h4>
            <p className="text-gray-600 max-w-md mb-4">
              Ask questions about certifications, documentation, costs, timelines,
              subsidies, or logistics for your export.
            </p>
            <div className="text-sm text-gray-500 space-y-2">
              <p className="font-medium">Example questions:</p>
              <ul className="text-left space-y-1">
                <li>• What documents do I need for FDA certification?</li>
                <li>• How long will the CE marking process take?</li>
                <li>• What subsidies are available for my company size?</li>
                <li>• How can I reduce RMS inspection probability?</li>
              </ul>
            </div>
          </div>
        ) : (
          <>
            {messages.map((message) => (
              <MessageBubble key={message.messageId} message={message} />
            ))}
            
            {/* Loading Indicator */}
            {isLoading && (
              <div className="flex justify-start mb-4">
                <div className="max-w-3xl mr-12">
                  <div className="flex items-center mb-1">
                    <span className="text-xs text-gray-500">ExportSathi AI</span>
                  </div>
                  <div className="bg-gray-100 border border-gray-200 rounded-lg px-4 py-3">
                    <div className="flex items-center space-x-2">
                      <div className="flex space-x-1">
                        <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
                        <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
                        <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
                      </div>
                      <span className="text-sm text-gray-600">Thinking...</span>
                    </div>
                  </div>
                </div>
              </div>
            )}
            
            {/* Scroll anchor */}
            <div ref={messagesEndRef} />
          </>
        )}
      </div>

      {/* Error Display */}
      {error && (
        <div className="px-6 py-2 bg-red-50 border-t border-red-200">
          <div className="flex items-center text-sm text-red-700">
            <svg
              className="w-4 h-4 mr-2 flex-shrink-0"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
              />
            </svg>
            <span>{error}</span>
          </div>
        </div>
      )}

      {/* Input Form */}
      <form onSubmit={handleSubmit} className="px-6 py-4 border-t border-gray-200 bg-gray-50">
        <div className="flex items-end space-x-3">
          <div className="flex-1">
            <textarea
              ref={inputRef}
              value={inputText}
              onChange={handleInputChange}
              onKeyDown={handleKeyDown}
              placeholder="Ask a question about your export requirements..."
              rows={2}
              maxLength={1000}
              disabled={isLoading}
              className="w-full px-4 py-3 border border-gray-300 rounded-lg shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 resize-none disabled:bg-gray-100 disabled:cursor-not-allowed"
            />
            <div className="flex items-center justify-between mt-2">
              <p className="text-xs text-gray-500">
                Press Enter to send, Shift+Enter for new line
              </p>
              <p className="text-xs text-gray-500">
                {inputText.length}/1000
              </p>
            </div>
          </div>
          
          <Button
            type="submit"
            disabled={!inputText.trim() || isLoading}
            size="lg"
            className="flex-shrink-0"
          >
            {isLoading ? (
              <svg
                className="w-5 h-5 animate-spin"
                fill="none"
                viewBox="0 0 24 24"
              >
                <circle
                  className="opacity-25"
                  cx="12"
                  cy="12"
                  r="10"
                  stroke="currentColor"
                  strokeWidth="4"
                ></circle>
                <path
                  className="opacity-75"
                  fill="currentColor"
                  d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                ></path>
              </svg>
            ) : (
              <svg
                className="w-5 h-5"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8"
                />
              </svg>
            )}
          </Button>
        </div>
      </form>

      {/* Info Footer */}
      <div className="px-6 py-3 bg-blue-50 border-t border-blue-200">
        <div className="flex items-start text-xs text-blue-800">
          <svg
            className="w-4 h-4 mr-2 flex-shrink-0 mt-0.5"
            fill="currentColor"
            viewBox="0 0 20 20"
          >
            <path
              fillRule="evenodd"
              d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z"
              clipRule="evenodd"
            />
          </svg>
          <div>
            <p className="font-medium mb-1">AI-Powered Guidance</p>
            <p>
              All responses are grounded in regulatory documents from DGFT, Customs,
              FDA, and other official sources. Source citations are provided for
              transparency.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ChatInterface;
