/**
 * Form Validation Hook
 *
 * A custom React hook for form validation with real-time feedback.
 */
import { useState, useCallback } from 'react';
import { ValidationResult, validateForm } from '../utils/validation';

interface FormErrors {
  [key: string]: string;
}

interface FieldValidation {
  [key: string]: (value: any) => ValidationResult;
}

interface UseFormValidationReturn {
  errors: FormErrors;
  validate: (field: string, value: any) => boolean;
  validateAll: (formData: { [key: string]: any }) => boolean;
  clearError: (field: string) => void;
  clearAllErrors: () => void;
  setError: (field: string, error: string) => void;
}

/**
 * Custom hook for form validation
 *
 * @param validations - Object mapping field names to validation functions
 * @returns Validation utilities and error state
 *
 * @example
 * const { errors, validate, validateAll } = useFormValidation({
 *   email: (value) => validateEmail(value),
 *   password: (value) => validatePassword(value),
 * });
 *
 * // Validate single field
 * const handleEmailChange = (e) => {
 *   setEmail(e.target.value);
 *   validate('email', e.target.value);
 * };
 *
 * // Validate all fields
 * const handleSubmit = () => {
 *   if (validateAll({ email, password })) {
 *     // Submit form
 *   }
 * };
 */
export const useFormValidation = (
  validations: FieldValidation
): UseFormValidationReturn => {
  const [errors, setErrors] = useState<FormErrors>({});

  /**
   * Validate a single field
   */
  const validate = useCallback(
    (field: string, value: any): boolean => {
      if (!validations[field]) {
        console.warn(`No validation defined for field: ${field}`);
        return true;
      }

      const result = validations[field](value);

      if (!result.isValid && result.error) {
        setErrors((prev) => ({ ...prev, [field]: result.error! }));
        return false;
      } else {
        setErrors((prev) => {
          const newErrors = { ...prev };
          delete newErrors[field];
          return newErrors;
        });
        return true;
      }
    },
    [validations]
  );

  /**
   * Validate all fields in the form
   */
  const validateAll = useCallback(
    (formData: { [key: string]: any }): boolean => {
      const validationResults: { [key: string]: ValidationResult } = {};

      Object.keys(validations).forEach((field) => {
        validationResults[field] = validations[field](formData[field]);
      });

      const { isValid, errors: validationErrors } = validateForm(validationResults);

      setErrors(validationErrors);

      return isValid;
    },
    [validations]
  );

  /**
   * Clear error for a specific field
   */
  const clearError = useCallback((field: string) => {
    setErrors((prev) => {
      const newErrors = { ...prev };
      delete newErrors[field];
      return newErrors;
    });
  }, []);

  /**
   * Clear all errors
   */
  const clearAllErrors = useCallback(() => {
    setErrors({});
  }, []);

  /**
   * Manually set an error for a field
   */
  const setError = useCallback((field: string, error: string) => {
    setErrors((prev) => ({ ...prev, [field]: error }));
  }, []);

  return {
    errors,
    validate,
    validateAll,
    clearError,
    clearAllErrors,
    setError,
  };
};

export default useFormValidation;
