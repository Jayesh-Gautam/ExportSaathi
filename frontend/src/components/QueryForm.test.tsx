/**
 * Unit tests for QueryForm component
 */

import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { QueryForm } from './QueryForm';

describe('QueryForm', () => {
  it('renders all required form fields', () => {
    const mockSubmit = vi.fn();
    render(<QueryForm onSubmit={mockSubmit} />);

    // Check for required fields
    expect(screen.getByLabelText(/business type/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/company size/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/product name/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/destination country/i)).toBeInTheDocument();
  });

  it('shows validation errors for empty required fields', async () => {
    const mockSubmit = vi.fn();
    render(<QueryForm onSubmit={mockSubmit} />);

    // Try to submit without filling required fields
    const submitButton = screen.getByRole('button', { name: /generate export readiness report/i });
    fireEvent.click(submitButton);

    // Should not call onSubmit
    expect(mockSubmit).not.toHaveBeenCalled();

    // Should show validation errors
    await waitFor(() => {
      expect(screen.getByText(/product name is required/i)).toBeInTheDocument();
    });
  });

  it('accepts valid form input and calls onSubmit', async () => {
    const mockSubmit = vi.fn();
    render(<QueryForm onSubmit={mockSubmit} />);

    // Fill in required fields
    const businessTypeSelect = screen.getByLabelText(/business type/i);
    fireEvent.change(businessTypeSelect, { target: { value: 'Manufacturing' } });

    const companySizeSelect = screen.getByLabelText(/company size/i);
    fireEvent.change(companySizeSelect, { target: { value: 'Micro' } });

    const productNameInput = screen.getByLabelText(/product name/i);
    fireEvent.change(productNameInput, { target: { value: 'Organic Turmeric Powder' } });

    const countryInput = screen.getByLabelText(/destination country/i);
    fireEvent.change(countryInput, { target: { value: 'United States' } });
    
    // Select a country from dropdown
    await waitFor(() => {
      const usOption = screen.getByText('United States');
      fireEvent.click(usOption);
    });

    // Submit form
    const submitButton = screen.getByRole('button', { name: /generate export readiness report/i });
    fireEvent.click(submitButton);

    // Should call onSubmit with FormData
    await waitFor(() => {
      expect(mockSubmit).toHaveBeenCalledTimes(1);
      expect(mockSubmit).toHaveBeenCalledWith(expect.any(FormData));
    });
  });

  it('validates product name length', async () => {
    const mockSubmit = vi.fn();
    render(<QueryForm onSubmit={mockSubmit} />);

    const productNameInput = screen.getByLabelText(/product name/i);
    const longName = 'a'.repeat(201); // Exceeds 200 character limit
    fireEvent.change(productNameInput, { target: { value: longName } });

    const submitButton = screen.getByRole('button', { name: /generate export readiness report/i });
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText(/product name must be less than 200 characters/i)).toBeInTheDocument();
    });

    expect(mockSubmit).not.toHaveBeenCalled();
  });

  it('shows loading state when isLoading is true', () => {
    const mockSubmit = vi.fn();
    render(<QueryForm onSubmit={mockSubmit} isLoading={true} />);

    const submitButton = screen.getByRole('button', { name: /generating report/i });
    expect(submitButton).toBeDisabled();
  });

  it('handles image upload', async () => {
    const mockSubmit = vi.fn();
    render(<QueryForm onSubmit={mockSubmit} />);

    // Create a mock file
    const file = new File(['dummy content'], 'product.png', { type: 'image/png' });
    
    // Find the hidden file input
    const fileInput = document.querySelector('input[type="file"]') as HTMLInputElement;
    
    // Simulate file selection
    Object.defineProperty(fileInput, 'files', {
      value: [file],
      writable: false,
    });
    
    fireEvent.change(fileInput);

    // Should show image preview
    await waitFor(() => {
      const preview = screen.getByAltText(/product preview/i);
      expect(preview).toBeInTheDocument();
    });
  });

  it('filters countries based on search input', async () => {
    const mockSubmit = vi.fn();
    render(<QueryForm onSubmit={mockSubmit} />);

    const countryInput = screen.getByLabelText(/destination country/i);
    
    // Type to search
    fireEvent.change(countryInput, { target: { value: 'United' } });
    fireEvent.focus(countryInput);

    // Should show filtered results
    await waitFor(() => {
      expect(screen.getByText('United States')).toBeInTheDocument();
      expect(screen.getByText('United Kingdom')).toBeInTheDocument();
      expect(screen.getByText('United Arab Emirates')).toBeInTheDocument();
    });
  });

  it('validates monthly volume is a number', async () => {
    const mockSubmit = vi.fn();
    render(<QueryForm onSubmit={mockSubmit} />);

    // Fill required fields first
    const businessTypeSelect = screen.getByLabelText(/business type/i);
    fireEvent.change(businessTypeSelect, { target: { value: 'Manufacturing' } });

    const companySizeSelect = screen.getByLabelText(/company size/i);
    fireEvent.change(companySizeSelect, { target: { value: 'Micro' } });

    const productNameInput = screen.getByLabelText(/product name/i);
    fireEvent.change(productNameInput, { target: { value: 'Test Product' } });

    const countryInput = screen.getByLabelText(/destination country/i);
    fireEvent.change(countryInput, { target: { value: 'United States' } });
    
    await waitFor(() => {
      const usOption = screen.getByText('United States');
      fireEvent.click(usOption);
    });

    // Enter invalid monthly volume
    const volumeInput = screen.getByLabelText(/monthly export volume/i);
    fireEvent.change(volumeInput, { target: { value: 'not-a-number' } });

    const submitButton = screen.getByRole('button', { name: /generate export readiness report/i });
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText(/monthly volume must be a number/i)).toBeInTheDocument();
    });

    expect(mockSubmit).not.toHaveBeenCalled();
  });
});
