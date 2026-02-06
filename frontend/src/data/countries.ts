/**
 * List of countries for destination selection
 * Organized by region for better UX
 */

export interface Country {
  code: string;
  name: string;
  region: string;
}

export const COUNTRIES: Country[] = [
  // North America
  { code: 'US', name: 'United States', region: 'North America' },
  { code: 'CA', name: 'Canada', region: 'North America' },
  { code: 'MX', name: 'Mexico', region: 'North America' },
  
  // Europe
  { code: 'GB', name: 'United Kingdom', region: 'Europe' },
  { code: 'DE', name: 'Germany', region: 'Europe' },
  { code: 'FR', name: 'France', region: 'Europe' },
  { code: 'IT', name: 'Italy', region: 'Europe' },
  { code: 'ES', name: 'Spain', region: 'Europe' },
  { code: 'NL', name: 'Netherlands', region: 'Europe' },
  { code: 'BE', name: 'Belgium', region: 'Europe' },
  { code: 'SE', name: 'Sweden', region: 'Europe' },
  { code: 'NO', name: 'Norway', region: 'Europe' },
  { code: 'DK', name: 'Denmark', region: 'Europe' },
  { code: 'FI', name: 'Finland', region: 'Europe' },
  { code: 'PL', name: 'Poland', region: 'Europe' },
  { code: 'CH', name: 'Switzerland', region: 'Europe' },
  { code: 'AT', name: 'Austria', region: 'Europe' },
  { code: 'IE', name: 'Ireland', region: 'Europe' },
  
  // Asia Pacific
  { code: 'CN', name: 'China', region: 'Asia Pacific' },
  { code: 'JP', name: 'Japan', region: 'Asia Pacific' },
  { code: 'KR', name: 'South Korea', region: 'Asia Pacific' },
  { code: 'SG', name: 'Singapore', region: 'Asia Pacific' },
  { code: 'AU', name: 'Australia', region: 'Asia Pacific' },
  { code: 'NZ', name: 'New Zealand', region: 'Asia Pacific' },
  { code: 'MY', name: 'Malaysia', region: 'Asia Pacific' },
  { code: 'TH', name: 'Thailand', region: 'Asia Pacific' },
  { code: 'VN', name: 'Vietnam', region: 'Asia Pacific' },
  { code: 'ID', name: 'Indonesia', region: 'Asia Pacific' },
  { code: 'PH', name: 'Philippines', region: 'Asia Pacific' },
  { code: 'HK', name: 'Hong Kong', region: 'Asia Pacific' },
  { code: 'TW', name: 'Taiwan', region: 'Asia Pacific' },
  
  // Middle East
  { code: 'AE', name: 'United Arab Emirates', region: 'Middle East' },
  { code: 'SA', name: 'Saudi Arabia', region: 'Middle East' },
  { code: 'QA', name: 'Qatar', region: 'Middle East' },
  { code: 'KW', name: 'Kuwait', region: 'Middle East' },
  { code: 'OM', name: 'Oman', region: 'Middle East' },
  { code: 'BH', name: 'Bahrain', region: 'Middle East' },
  { code: 'IL', name: 'Israel', region: 'Middle East' },
  { code: 'TR', name: 'Turkey', region: 'Middle East' },
  
  // Africa
  { code: 'ZA', name: 'South Africa', region: 'Africa' },
  { code: 'EG', name: 'Egypt', region: 'Africa' },
  { code: 'NG', name: 'Nigeria', region: 'Africa' },
  { code: 'KE', name: 'Kenya', region: 'Africa' },
  { code: 'MA', name: 'Morocco', region: 'Africa' },
  { code: 'GH', name: 'Ghana', region: 'Africa' },
  
  // South America
  { code: 'BR', name: 'Brazil', region: 'South America' },
  { code: 'AR', name: 'Argentina', region: 'South America' },
  { code: 'CL', name: 'Chile', region: 'South America' },
  { code: 'CO', name: 'Colombia', region: 'South America' },
  { code: 'PE', name: 'Peru', region: 'South America' },
];

/**
 * Get country name by code
 */
export const getCountryName = (code: string): string => {
  const country = COUNTRIES.find(c => c.code === code);
  return country?.name || code;
};

/**
 * Filter countries by search term
 */
export const filterCountries = (searchTerm: string): Country[] => {
  const term = searchTerm.toLowerCase();
  return COUNTRIES.filter(
    country =>
      country.name.toLowerCase().includes(term) ||
      country.code.toLowerCase().includes(term)
  );
};
