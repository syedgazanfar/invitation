/**
 * Environment Configuration
 *
 * Central configuration file for managing environment variables.
 * All environment variables should be accessed through this file.
 */

export const config = {
  // Environment
  env: process.env.REACT_APP_ENV || 'development',
  isDevelopment: process.env.REACT_APP_ENV === 'development',
  isProduction: process.env.REACT_APP_ENV === 'production',

  // API Configuration
  api: {
    baseUrl: process.env.REACT_APP_API_URL || 'http://localhost:8000/api/v1',
    timeout: parseInt(process.env.REACT_APP_API_TIMEOUT || '30000', 10),
  },

  // App Configuration
  app: {
    publicUrl: process.env.REACT_APP_PUBLIC_URL || 'http://localhost:3000',
    maxUploadSize: parseInt(process.env.REACT_APP_MAX_UPLOAD_SIZE || '10485760', 10), // 10MB
  },

  // Payment Gateway (Razorpay)
  razorpay: {
    keyId: process.env.REACT_APP_RAZORPAY_KEY_ID || '',
  },

  // Analytics (Optional)
  analytics: {
    enabled: process.env.REACT_APP_ENABLE_ANALYTICS === 'true',
    googleAnalyticsId: process.env.REACT_APP_GA_TRACKING_ID || '',
  },

  // Error Reporting (Optional)
  sentry: {
    enabled: process.env.REACT_APP_ENABLE_ERROR_REPORTING === 'true',
    dsn: process.env.REACT_APP_SENTRY_DSN || '',
  },
};

// Validation: Log warnings for missing required variables in production
if (config.isProduction) {
  const requiredVars = {
    'REACT_APP_API_URL': process.env.REACT_APP_API_URL,
    'REACT_APP_PUBLIC_URL': process.env.REACT_APP_PUBLIC_URL,
    'REACT_APP_RAZORPAY_KEY_ID': process.env.REACT_APP_RAZORPAY_KEY_ID,
  };

  Object.entries(requiredVars).forEach(([key, value]) => {
    if (!value) {
      console.warn(`[Config Warning] Missing required environment variable: ${key}`);
    }
  });
}

export default config;
