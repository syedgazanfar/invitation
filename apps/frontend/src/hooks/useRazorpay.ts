/**
 * Razorpay Payment Hook
 */
import { useEffect, useState } from 'react';

interface RazorpayOptions {
  key: string;
  amount: number;
  currency: string;
  name: string;
  description: string;
  order_id: string;
  handler: (response: RazorpayResponse) => void;
  prefill: {
    name: string;
    email: string;
    contact: string;
  };
  theme: {
    color: string;
  };
}

interface RazorpayResponse {
  razorpay_payment_id: string;
  razorpay_order_id: string;
  razorpay_signature: string;
}

export const useRazorpay = () => {
  const [isLoaded, setIsLoaded] = useState(false);

  useEffect(() => {
    // Check if Razorpay is already loaded
    if (window.Razorpay) {
      setIsLoaded(true);
      return;
    }

    // Load Razorpay script
    const script = document.createElement('script');
    script.src = 'https://checkout.razorpay.com/v1/checkout.js';
    script.async = true;
    script.onload = () => setIsLoaded(true);
    script.onerror = () => setIsLoaded(false);
    document.body.appendChild(script);

    return () => {
      document.body.removeChild(script);
    };
  }, []);

  const openRazorpayCheckout = (options: RazorpayOptions): Promise<boolean> => {
    return new Promise((resolve, reject) => {
      if (!window.Razorpay) {
        reject(new Error('Razorpay not loaded'));
        return;
      }

      const razorpay = new window.Razorpay({
        ...options,
        handler: (response: RazorpayResponse) => {
          options.handler(response);
          resolve(true);
        },
        modal: {
          ondismiss: () => {
            resolve(false);
          },
        },
      });

      razorpay.on('payment.failed', (response: any) => {
        reject(new Error(response.error.description));
      });

      razorpay.open();
    });
  };

  return {
    isLoaded,
    openRazorpayCheckout,
  };
};

export default useRazorpay;
