/**
 * QueryForm Stories
 * Visual examples and documentation for the QueryForm component
 */

import type { Meta, StoryObj } from '@storybook/react';
import { QueryForm } from './QueryForm';
import { action } from '@storybook/addon-actions';

const meta: Meta<typeof QueryForm> = {
  title: 'Components/QueryForm',
  component: QueryForm,
  parameters: {
    layout: 'padded',
  },
  tags: ['autodocs'],
};

export default meta;
type Story = StoryObj<typeof QueryForm>;

/**
 * Default state of the QueryForm
 */
export const Default: Story = {
  args: {
    onSubmit: action('onSubmit'),
    isLoading: false,
  },
};

/**
 * Form in loading state during submission
 */
export const Loading: Story = {
  args: {
    onSubmit: action('onSubmit'),
    isLoading: true,
  },
};

/**
 * Form with pre-filled business type (e.g., from onboarding)
 */
export const WithBusinessType: Story = {
  args: {
    onSubmit: action('onSubmit'),
    isLoading: false,
    businessType: 'Manufacturing',
  },
};

/**
 * Example: Manufacturing MSME use case
 */
export const ManufacturingExample: Story = {
  args: {
    onSubmit: action('onSubmit'),
    isLoading: false,
    businessType: 'Manufacturing',
  },
  parameters: {
    docs: {
      description: {
        story: 'Example for a manufacturing MSME exporting LED bulbs to the United States',
      },
    },
  },
};

/**
 * Example: SaaS Exporter use case
 */
export const SaaSExample: Story = {
  args: {
    onSubmit: action('onSubmit'),
    isLoading: false,
    businessType: 'SaaS',
  },
  parameters: {
    docs: {
      description: {
        story: 'Example for a SaaS company exporting software services',
      },
    },
  },
};

/**
 * Example: Merchant Exporter use case
 */
export const MerchantExample: Story = {
  args: {
    onSubmit: action('onSubmit'),
    isLoading: false,
    businessType: 'Merchant',
  },
  parameters: {
    docs: {
      description: {
        story: 'Example for a merchant exporter dealing with multiple products',
      },
    },
  },
};
