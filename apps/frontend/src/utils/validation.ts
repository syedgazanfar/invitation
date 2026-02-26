/**
 * Form Validation Utilities
 *
 * Provides common validation functions for forms throughout the application.
 */

/**
 * Validation result interface
 */
export interface ValidationResult {
  isValid: boolean;
  error?: string;
}

/**
 * Email validation
 */
export const validateEmail = (email: string): ValidationResult => {
  if (!email) {
    return { isValid: false, error: 'Email is required' };
  }

  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  if (!emailRegex.test(email)) {
    return { isValid: false, error: 'Please enter a valid email address' };
  }

  return { isValid: true };
};

/**
 * Phone number validation (supports international formats)
 */
export const validatePhone = (phone: string): ValidationResult => {
  if (!phone) {
    return { isValid: false, error: 'Phone number is required' };
  }

  // Remove spaces, dashes, and parentheses
  const cleanPhone = phone.replace(/[\s\-()]/g, '');

  // Check if it starts with + and has at least 10 digits
  if (cleanPhone.startsWith('+')) {
    if (cleanPhone.length < 11 || cleanPhone.length > 15) {
      return { isValid: false, error: 'Phone number must be between 10-15 digits' };
    }
    if (!/^\+\d+$/.test(cleanPhone)) {
      return { isValid: false, error: 'Phone number must contain only digits after +' };
    }
  } else {
    // For non-international numbers, check for 10 digits
    if (cleanPhone.length < 10) {
      return { isValid: false, error: 'Phone number must be at least 10 digits' };
    }
    if (!/^\d+$/.test(cleanPhone)) {
      return { isValid: false, error: 'Phone number must contain only digits' };
    }
  }

  return { isValid: true };
};

/**
 * Password validation
 */
export const validatePassword = (password: string, options?: {
  minLength?: number;
  requireUppercase?: boolean;
  requireLowercase?: boolean;
  requireNumber?: boolean;
  requireSpecialChar?: boolean;
}): ValidationResult => {
  const {
    minLength = 8,
    requireUppercase = true,
    requireLowercase = true,
    requireNumber = true,
    requireSpecialChar = false,
  } = options || {};

  if (!password) {
    return { isValid: false, error: 'Password is required' };
  }

  if (password.length < minLength) {
    return { isValid: false, error: `Password must be at least ${minLength} characters` };
  }

  if (requireUppercase && !/[A-Z]/.test(password)) {
    return { isValid: false, error: 'Password must contain at least one uppercase letter' };
  }

  if (requireLowercase && !/[a-z]/.test(password)) {
    return { isValid: false, error: 'Password must contain at least one lowercase letter' };
  }

  if (requireNumber && !/\d/.test(password)) {
    return { isValid: false, error: 'Password must contain at least one number' };
  }

  if (requireSpecialChar && !/[!@#$%^&*(),.?":{}|<>]/.test(password)) {
    return { isValid: false, error: 'Password must contain at least one special character' };
  }

  return { isValid: true };
};

/**
 * Password confirmation validation
 */
export const validatePasswordConfirm = (password: string, confirmPassword: string): ValidationResult => {
  if (!confirmPassword) {
    return { isValid: false, error: 'Please confirm your password' };
  }

  if (password !== confirmPassword) {
    return { isValid: false, error: 'Passwords do not match' };
  }

  return { isValid: true };
};

/**
 * Required field validation
 */
export const validateRequired = (value: string, fieldName: string = 'This field'): ValidationResult => {
  if (!value || value.trim() === '') {
    return { isValid: false, error: `${fieldName} is required` };
  }

  return { isValid: true };
};

/**
 * Minimum length validation
 */
export const validateMinLength = (
  value: string,
  minLength: number,
  fieldName: string = 'This field'
): ValidationResult => {
  if (value.length < minLength) {
    return { isValid: false, error: `${fieldName} must be at least ${minLength} characters` };
  }

  return { isValid: true };
};

/**
 * Maximum length validation
 */
export const validateMaxLength = (
  value: string,
  maxLength: number,
  fieldName: string = 'This field'
): ValidationResult => {
  if (value.length > maxLength) {
    return { isValid: false, error: `${fieldName} must not exceed ${maxLength} characters` };
  }

  return { isValid: true };
};

/**
 * URL validation
 */
export const validateURL = (url: string): ValidationResult => {
  if (!url) {
    return { isValid: false, error: 'URL is required' };
  }

  try {
    new URL(url);
    return { isValid: true };
  } catch {
    return { isValid: false, error: 'Please enter a valid URL' };
  }
};

/**
 * Date validation (must be future date)
 */
export const validateFutureDate = (date: string | Date): ValidationResult => {
  if (!date) {
    return { isValid: false, error: 'Date is required' };
  }

  const selectedDate = new Date(date);
  const today = new Date();
  today.setHours(0, 0, 0, 0);

  if (selectedDate < today) {
    return { isValid: false, error: 'Please select a future date' };
  }

  return { isValid: true };
};

/**
 * Date validation (must be past date)
 */
export const validatePastDate = (date: string | Date): ValidationResult => {
  if (!date) {
    return { isValid: false, error: 'Date is required' };
  }

  const selectedDate = new Date(date);
  const today = new Date();
  today.setHours(0, 0, 0, 0);

  if (selectedDate > today) {
    return { isValid: false, error: 'Please select a past date' };
  }

  return { isValid: true };
};

/**
 * File size validation (in bytes)
 */
export const validateFileSize = (file: File, maxSizeInMB: number): ValidationResult => {
  const maxSizeInBytes = maxSizeInMB * 1024 * 1024;

  if (file.size > maxSizeInBytes) {
    return { isValid: false, error: `File size must not exceed ${maxSizeInMB}MB` };
  }

  return { isValid: true };
};

/**
 * File type validation
 */
export const validateFileType = (file: File, allowedTypes: string[]): ValidationResult => {
  if (!allowedTypes.includes(file.type)) {
    return { isValid: false, error: `File type must be one of: ${allowedTypes.join(', ')}` };
  }

  return { isValid: true };
};

/**
 * OTP validation (6 digits)
 */
export const validateOTP = (otp: string): ValidationResult => {
  if (!otp) {
    return { isValid: false, error: 'OTP is required' };
  }

  if (!/^\d{6}$/.test(otp)) {
    return { isValid: false, error: 'OTP must be 6 digits' };
  }

  return { isValid: true };
};

/**
 * Username validation
 */
export const validateUsername = (username: string): ValidationResult => {
  if (!username) {
    return { isValid: false, error: 'Username is required' };
  }

  if (username.length < 3) {
    return { isValid: false, error: 'Username must be at least 3 characters' };
  }

  if (username.length > 30) {
    return { isValid: false, error: 'Username must not exceed 30 characters' };
  }

  if (!/^[a-zA-Z0-9_]+$/.test(username)) {
    return { isValid: false, error: 'Username can only contain letters, numbers, and underscores' };
  }

  return { isValid: true };
};

/**
 * Numeric validation
 */
export const validateNumeric = (value: string, fieldName: string = 'This field'): ValidationResult => {
  if (!value) {
    return { isValid: false, error: `${fieldName} is required` };
  }

  if (!/^\d+$/.test(value)) {
    return { isValid: false, error: `${fieldName} must be a number` };
  }

  return { isValid: true };
};

/**
 * Range validation
 */
export const validateRange = (
  value: number,
  min: number,
  max: number,
  fieldName: string = 'Value'
): ValidationResult => {
  if (value < min || value > max) {
    return { isValid: false, error: `${fieldName} must be between ${min} and ${max}` };
  }

  return { isValid: true };
};

/**
 * Validate multiple fields
 */
export const validateForm = (validations: { [key: string]: ValidationResult }): {
  isValid: boolean;
  errors: { [key: string]: string };
} => {
  const errors: { [key: string]: string } = {};
  let isValid = true;

  Object.keys(validations).forEach((key) => {
    const result = validations[key];
    if (!result.isValid && result.error) {
      errors[key] = result.error;
      isValid = false;
    }
  });

  return { isValid, errors };
};
