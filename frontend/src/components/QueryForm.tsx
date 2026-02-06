/**
 * QueryForm Component
 * 
 * Collects product information for export readiness assessment:
 * - Product name
 * - Product image upload with preview
 * - Ingredients/BOM
 * - Destination country
 * - Monthly volume and price range
 * 
 * Validates inputs and handles image upload to backend
 */

import React, { useState, useRef, ChangeEvent, FormEvent } from 'react';
import { Input, Button, Select } from './common';
import { COUNTRIES, filterCountries, type Country } from '../data/countries';
import type { GenerateReportRequest } from '../types/api';

interface QueryFormProps {
  onSubmit: (data: FormData) => void;
  isLoading?: boolean;
  businessType?: string;
}

interface FormData {
  productName: string;
  productImage: File | null;
  ingredients: string;
  bom: string;
  destinationCountry: string;
  monthlyVolume: string;
  priceRange: string;
  paymentMode: string;
}

interface FormErrors {
  productName?: string;
  destinationCountry?: string;
  monthlyVolume?: string;
  general?: string;
}

const BUSINESS_TYPES = [
  { value: 'Manufacturing', label: 'Manufacturing MSME' },
  { value: 'SaaS', label: 'SaaS/Service Exporter' },
  { value: 'Merchant', label: 'Merchant Exporter' },
];

const COMPANY_SIZES = [
  { value: 'Micro', label: 'Micro (< ₹5 Cr turnover)' },
  { value: 'Small', label: 'Small (₹5-50 Cr turnover)' },
  { value: 'Medium', label: 'Medium (₹50-250 Cr turnover)' },
];

const PRICE_RANGES = [
  { value: '0-1000', label: '₹0 - ₹1,000' },
  { value: '1000-5000', label: '₹1,000 - ₹5,000' },
  { value: '5000-10000', label: '₹5,000 - ₹10,000' },
  { value: '10000-50000', label: '₹10,000 - ₹50,000' },
  { value: '50000+', label: '₹50,000+' },
];

const PAYMENT_MODES = [
  { value: 'LC', label: 'Letter of Credit (LC)' },
  { value: 'TT', label: 'Telegraphic Transfer (TT)' },
  { value: 'DA', label: 'Documents Against Acceptance (DA)' },
  { value: 'DP', label: 'Documents Against Payment (DP)' },
  { value: 'Advance', label: 'Advance Payment' },
];

const MAX_FILE_SIZE = 10 * 1024 * 1024; // 10MB
const ALLOWED_FILE_TYPES = ['image/jpeg', 'image/jpg', 'image/png', 'image/webp'];

export const QueryForm: React.FC<QueryFormProps> = ({
  onSubmit,
  isLoading = false,
  businessType: initialBusinessType,
}) => {
  const [formData, setFormData] = useState<FormData>({
    productName: '',
    productImage: null,
    ingredients: '',
    bom: '',
    destinationCountry: '',
    monthlyVolume: '',
    priceRange: '',
    paymentMode: '',
  });

  const [businessType, setBusinessType] = useState(initialBusinessType || '');
  const [companySize, setCompanySize] = useState('');
  const [imagePreview, setImagePreview] = useState<string | null>(null);
  const [errors, setErrors] = useState<FormErrors>({});
  const [countrySearch, setCountrySearch] = useState('');
  const [showCountryDropdown, setShowCountryDropdown] = useState(false);
  const [filteredCountries, setFilteredCountries] = useState<Country[]>(COUNTRIES);
  
  const fileInputRef = useRef<HTMLInputElement>(null);
  const countryInputRef = useRef<HTMLDivElement>(null);

  // Handle input changes
  const handleInputChange = (
    e: ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>
  ) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
    
    // Clear error for this field
    if (errors[name as keyof FormErrors]) {
      setErrors(prev => ({ ...prev, [name]: undefined }));
    }
  };

  // Handle image upload
  const handleImageChange = (e: ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    
    if (!file) return;

    // Validate file type
    if (!ALLOWED_FILE_TYPES.includes(file.type)) {
      setErrors(prev => ({
        ...prev,
        general: 'Please upload a valid image file (JPEG, PNG, or WebP)',
      }));
      return;
    }

    // Validate file size
    if (file.size > MAX_FILE_SIZE) {
      setErrors(prev => ({
        ...prev,
        general: 'Image size must be less than 10MB',
      }));
      return;
    }

    setFormData(prev => ({ ...prev, productImage: file }));
    
    // Create preview
    const reader = new FileReader();
    reader.onloadend = () => {
      setImagePreview(reader.result as string);
    };
    reader.readAsDataURL(file);
    
    // Clear any previous errors
    setErrors(prev => ({ ...prev, general: undefined }));
  };

  // Remove image
  const handleRemoveImage = () => {
    setFormData(prev => ({ ...prev, productImage: null }));
    setImagePreview(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  // Handle country search
  const handleCountrySearch = (e: ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    setCountrySearch(value);
    setShowCountryDropdown(true);
    
    if (value.trim()) {
      setFilteredCountries(filterCountries(value));
    } else {
      setFilteredCountries(COUNTRIES);
    }
    
    // Clear error
    if (errors.destinationCountry) {
      setErrors(prev => ({ ...prev, destinationCountry: undefined }));
    }
  };

  // Select country
  const handleCountrySelect = (country: Country) => {
    setFormData(prev => ({ ...prev, destinationCountry: country.code }));
    setCountrySearch(country.name);
    setShowCountryDropdown(false);
  };

  // Validate form
  const validateForm = (): boolean => {
    const newErrors: FormErrors = {};

    // Product name is required
    if (!formData.productName.trim()) {
      newErrors.productName = 'Product name is required';
    } else if (formData.productName.length > 200) {
      newErrors.productName = 'Product name must be less than 200 characters';
    }

    // Destination country is required
    if (!formData.destinationCountry) {
      newErrors.destinationCountry = 'Destination country is required';
    }

    // Monthly volume validation (if provided)
    if (formData.monthlyVolume && isNaN(Number(formData.monthlyVolume))) {
      newErrors.monthlyVolume = 'Monthly volume must be a number';
    }

    // Business type required
    if (!businessType) {
      newErrors.general = 'Please select your business type';
    }

    // Company size required
    if (!companySize) {
      newErrors.general = 'Please select your company size';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  // Handle form submission
  const handleSubmit = (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();

    if (!validateForm()) {
      return;
    }

    // Create FormData for multipart upload
    const submitData = new FormData();
    submitData.append('productName', formData.productName.trim());
    submitData.append('destinationCountry', formData.destinationCountry);
    submitData.append('businessType', businessType);
    submitData.append('companySize', companySize);

    if (formData.productImage) {
      submitData.append('productImage', formData.productImage);
    }

    if (formData.ingredients.trim()) {
      submitData.append('ingredients', formData.ingredients.trim());
    }

    if (formData.bom.trim()) {
      submitData.append('bom', formData.bom.trim());
    }

    if (formData.monthlyVolume) {
      submitData.append('monthlyVolume', formData.monthlyVolume);
    }

    if (formData.priceRange) {
      submitData.append('priceRange', formData.priceRange);
    }

    if (formData.paymentMode) {
      submitData.append('paymentMode', formData.paymentMode);
    }

    onSubmit(submitData);
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      {/* General Error */}
      {errors.general && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
          {errors.general}
        </div>
      )}

      {/* Business Type */}
      <Select
        label="Business Type"
        name="businessType"
        value={businessType}
        onChange={(e) => setBusinessType(e.target.value)}
        options={BUSINESS_TYPES}
        required
        disabled={!!initialBusinessType}
        helperText="Select your business category"
      />

      {/* Company Size */}
      <Select
        label="Company Size"
        name="companySize"
        value={companySize}
        onChange={(e) => setCompanySize(e.target.value)}
        options={COMPANY_SIZES}
        required
        helperText="Based on annual turnover"
      />

      {/* Product Name */}
      <Input
        label="Product Name"
        name="productName"
        type="text"
        value={formData.productName}
        onChange={handleInputChange}
        placeholder="e.g., Organic Turmeric Powder, LED Bulbs, Cotton T-Shirts"
        required
        maxLength={200}
        error={errors.productName}
        helperText="Enter the name of the product you want to export"
      />

      {/* Product Image Upload */}
      <div className="space-y-2">
        <label className="block text-sm font-medium text-gray-700">
          Product Image
          <span className="text-gray-500 font-normal ml-2">(Optional but recommended)</span>
        </label>
        
        {!imagePreview ? (
          <div className="mt-1">
            <div
              onClick={() => fileInputRef.current?.click()}
              className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center cursor-pointer hover:border-blue-500 transition-colors"
            >
              <svg
                className="mx-auto h-12 w-12 text-gray-400"
                stroke="currentColor"
                fill="none"
                viewBox="0 0 48 48"
              >
                <path
                  d="M28 8H12a4 4 0 00-4 4v20m32-12v8m0 0v8a4 4 0 01-4 4H12a4 4 0 01-4-4v-4m32-4l-3.172-3.172a4 4 0 00-5.656 0L28 28M8 32l9.172-9.172a4 4 0 015.656 0L28 28m0 0l4 4m4-24h8m-4-4v8m-12 4h.02"
                  strokeWidth={2}
                  strokeLinecap="round"
                  strokeLinejoin="round"
                />
              </svg>
              <p className="mt-2 text-sm text-gray-600">
                Click to upload product image
              </p>
              <p className="mt-1 text-xs text-gray-500">
                PNG, JPG, WebP up to 10MB
              </p>
            </div>
            <input
              ref={fileInputRef}
              type="file"
              accept="image/jpeg,image/jpg,image/png,image/webp"
              onChange={handleImageChange}
              className="hidden"
            />
          </div>
        ) : (
          <div className="relative">
            <img
              src={imagePreview}
              alt="Product preview"
              className="w-full h-64 object-cover rounded-lg"
            />
            <button
              type="button"
              onClick={handleRemoveImage}
              className="absolute top-2 right-2 bg-red-600 text-white p-2 rounded-full hover:bg-red-700 transition-colors"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        )}
        <p className="text-xs text-gray-500">
          Uploading a product image helps improve HS code prediction accuracy
        </p>
      </div>

      {/* Ingredients/BOM */}
      <div className="space-y-2">
        <label htmlFor="ingredients" className="block text-sm font-medium text-gray-700">
          Ingredients / Bill of Materials (BOM)
          <span className="text-gray-500 font-normal ml-2">(Optional)</span>
        </label>
        <textarea
          id="ingredients"
          name="ingredients"
          value={formData.ingredients}
          onChange={handleInputChange}
          rows={4}
          maxLength={2000}
          placeholder="List main ingredients or components (e.g., Turmeric 95%, Curcumin 5%)"
          className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
        />
        <p className="text-xs text-gray-500">
          Helps identify restricted substances and compliance requirements
        </p>
      </div>

      {/* Additional BOM Details */}
      <div className="space-y-2">
        <label htmlFor="bom" className="block text-sm font-medium text-gray-700">
          Additional Product Details
          <span className="text-gray-500 font-normal ml-2">(Optional)</span>
        </label>
        <textarea
          id="bom"
          name="bom"
          value={formData.bom}
          onChange={handleInputChange}
          rows={3}
          maxLength={1000}
          placeholder="Any additional details about manufacturing process, materials, or specifications"
          className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
        />
      </div>

      {/* Destination Country Autocomplete */}
      <div className="space-y-2 relative" ref={countryInputRef}>
        <label htmlFor="country-search" className="block text-sm font-medium text-gray-700">
          Destination Country
          <span className="text-red-500 ml-1">*</span>
        </label>
        <input
          id="country-search"
          type="text"
          value={countrySearch}
          onChange={handleCountrySearch}
          onFocus={() => setShowCountryDropdown(true)}
          placeholder="Search for a country..."
          className={`w-full px-3 py-2 border rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 ${
            errors.destinationCountry ? 'border-red-500' : 'border-gray-300'
          }`}
          required
        />
        
        {/* Country Dropdown */}
        {showCountryDropdown && (
          <div className="absolute z-10 w-full mt-1 bg-white border border-gray-300 rounded-md shadow-lg max-h-60 overflow-auto">
            {filteredCountries.length > 0 ? (
              filteredCountries.map((country) => (
                <button
                  key={country.code}
                  type="button"
                  onClick={() => handleCountrySelect(country)}
                  className="w-full text-left px-4 py-2 hover:bg-blue-50 focus:bg-blue-50 focus:outline-none"
                >
                  <div className="font-medium">{country.name}</div>
                  <div className="text-xs text-gray-500">{country.region}</div>
                </button>
              ))
            ) : (
              <div className="px-4 py-2 text-gray-500">No countries found</div>
            )}
          </div>
        )}
        
        {errors.destinationCountry && (
          <p className="text-sm text-red-600">{errors.destinationCountry}</p>
        )}
        <p className="text-xs text-gray-500">
          Select the country you want to export to
        </p>
      </div>

      {/* Monthly Volume */}
      <Input
        label="Monthly Export Volume"
        name="monthlyVolume"
        type="number"
        value={formData.monthlyVolume}
        onChange={handleInputChange}
        placeholder="e.g., 1000"
        min="0"
        error={errors.monthlyVolume}
        helperText="Estimated units per month (optional)"
      />

      {/* Price Range */}
      <Select
        label="Price Range per Unit"
        name="priceRange"
        value={formData.priceRange}
        onChange={handleInputChange}
        options={PRICE_RANGES}
        helperText="Approximate price range (optional)"
      />

      {/* Payment Mode */}
      <Select
        label="Preferred Payment Mode"
        name="paymentMode"
        value={formData.paymentMode}
        onChange={handleInputChange}
        options={PAYMENT_MODES}
        helperText="How you plan to receive payment (optional)"
      />

      {/* Submit Button */}
      <div className="flex justify-end space-x-4">
        <Button
          type="submit"
          size="lg"
          isLoading={isLoading}
          disabled={isLoading}
        >
          {isLoading ? 'Generating Report...' : 'Generate Export Readiness Report'}
        </Button>
      </div>

      {/* Info Box */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <div className="flex">
          <svg className="w-5 h-5 text-blue-600 mr-3 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
          </svg>
          <div className="text-sm text-blue-800">
            <p className="font-medium mb-1">What happens next?</p>
            <ul className="list-disc list-inside space-y-1">
              <li>AI analyzes your product and predicts HS code</li>
              <li>Identifies required certifications for your destination</li>
              <li>Generates comprehensive export readiness report</li>
              <li>Provides 7-day action plan to become export-ready</li>
            </ul>
          </div>
        </div>
      </div>
    </form>
  );
};
