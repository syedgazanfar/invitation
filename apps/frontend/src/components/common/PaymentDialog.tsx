/**
 * Payment Dialog Component for Razorpay
 */
import React, { useState } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Typography,
  Box,
  Alert,
  CircularProgress,
  Stepper,
  Step,
  StepLabel,
  Radio,
  RadioGroup,
  FormControlLabel,
  FormControl,
  TextField,
} from '@mui/material';
import { Payment } from '@mui/icons-material';
import { invitationsApi } from '../../services/api';
import { useRazorpay } from '../../hooks/useRazorpay';

interface PaymentDialogProps {
  open: boolean;
  onClose: () => void;
  orderId: string;
  orderNumber: string;
  amount: number;
  userDetails: {
    name: string;
    email: string;
    phone: string;
  };
  onPaymentSuccess: () => void;
}

const PaymentDialog: React.FC<PaymentDialogProps> = ({
  open,
  onClose,
  orderId,
  orderNumber,
  amount,
  userDetails,
  onPaymentSuccess,
}) => {
  const { isLoaded, openRazorpayCheckout } = useRazorpay();
  const [activeStep, setActiveStep] = useState(0);
  const [paymentMethod, setPaymentMethod] = useState('razorpay');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [upiId, setUpiId] = useState('');
  const [paymentDetails, setPaymentDetails] = useState<{
    upi_id: string;
    account_name: string;
    account_number: string;
    ifsc_code: string;
    bank_name?: string;
  } | null>(null);
  const [loadingPaymentDetails, setLoadingPaymentDetails] = useState(false);

  const steps = ['Select Method', 'Payment', 'Confirmation'];

  // Fetch manual payment details when manual method is selected
  React.useEffect(() => {
    const fetchPaymentDetails = async () => {
      if (paymentMethod === 'manual' && !paymentDetails) {
        try {
          setLoadingPaymentDetails(true);
          setError('');
          const response = await invitationsApi.getManualPaymentDetails();
          if (response.success && response.data) {
            setPaymentDetails(response.data);
          }
        } catch (err: any) {
          console.error('Failed to fetch payment details:', err);
          setError('Failed to load payment details. Please try again.');
        } finally {
          setLoadingPaymentDetails(false);
        }
      }
    };

    fetchPaymentDetails();
  }, [paymentMethod, paymentDetails]);

  const handlePayment = async () => {
    if (paymentMethod === 'razorpay') {
      await handleRazorpayPayment();
    } else {
      // Handle manual payment methods (UPI, Bank Transfer)
      setActiveStep(2);
    }
  };

  const handleRazorpayPayment = async () => {
    try {
      setLoading(true);
      setError('');

      // Create Razorpay order
      const orderResponse = await invitationsApi.createRazorpayOrder(orderId);
      
      if (!orderResponse.success || !orderResponse.data) {
        throw new Error('Failed to create payment order');
      }

      const { order_id, key_id, amount, currency, prefill } = orderResponse.data;

      // Open Razorpay checkout
      const success = await openRazorpayCheckout({
        key: key_id,
        amount: amount * 100,
        currency,
        name: 'InviteMe',
        description: `Payment for ${orderNumber}`,
        order_id,
        handler: async (response) => {
          try {
            // Verify payment
            const verifyResponse = await invitationsApi.verifyRazorpayPayment({
              order_id: orderId,
              razorpay_payment_id: response.razorpay_payment_id,
              razorpay_order_id: response.razorpay_order_id,
              razorpay_signature: response.razorpay_signature,
            });

            if (verifyResponse.success) {
              setActiveStep(2);
              onPaymentSuccess();
            } else {
              setError('Payment verification failed');
            }
          } catch (err: any) {
            setError(err.message || 'Payment verification failed');
          }
        },
        prefill: {
          name: userDetails.name,
          email: userDetails.email,
          contact: userDetails.phone,
        },
        theme: {
          color: '#7B2CBF',
        },
      });

      if (!success) {
        setError('Payment was cancelled');
      }
    } catch (err: any) {
      setError(err.message || 'Payment failed');
    } finally {
      setLoading(false);
    }
  };

  const renderStepContent = () => {
    switch (activeStep) {
      case 0:
        return (
          <FormControl component="fieldset" fullWidth>
            <Typography variant="subtitle1" gutterBottom>
              Select Payment Method
            </Typography>
            <RadioGroup
              value={paymentMethod}
              onChange={(e) => setPaymentMethod(e.target.value)}
            >
              <FormControlLabel
                value="razorpay"
                control={<Radio />}
                label={
                  <Box>
                    <Typography variant="body1">Pay Online (Razorpay)</Typography>
                    <Typography variant="caption" color="text.secondary">
                      Credit/Debit Card, UPI, Net Banking, Wallets
                    </Typography>
                  </Box>
                }
              />
              <FormControlLabel
                value="manual"
                control={<Radio />}
                label={
                  <Box>
                    <Typography variant="body1">Pay Manually</Typography>
                    <Typography variant="caption" color="text.secondary">
                      UPI ID, Bank Transfer (Admin will verify)
                    </Typography>
                  </Box>
                }
              />
            </RadioGroup>
          </FormControl>
        );

      case 1:
        if (paymentMethod === 'manual') {
          if (loadingPaymentDetails) {
            return (
              <Box textAlign="center" py={4}>
                <CircularProgress size={60} />
                <Typography variant="h6" sx={{ mt: 2 }}>
                  Loading payment details...
                </Typography>
              </Box>
            );
          }

          if (!paymentDetails) {
            return (
              <Box>
                <Alert severity="error">
                  Failed to load payment details. Please try again or contact support.
                </Alert>
              </Box>
            );
          }

          return (
            <Box>
              <Typography variant="h6" gutterBottom>
                Manual Payment Instructions
              </Typography>
              <Alert severity="info" sx={{ mb: 3 }}>
                Your order will be pending until admin verifies your payment.
              </Alert>
              <Typography variant="body1" paragraph>
                <strong>Amount:</strong> Rs. {amount}
              </Typography>
              <Typography variant="body1" paragraph>
                <strong>UPI ID:</strong> {paymentDetails.upi_id}
              </Typography>
              <Typography variant="body1" paragraph>
                <strong>Account Name:</strong> {paymentDetails.account_name}
              </Typography>
              <Typography variant="body1" paragraph>
                <strong>Account Number:</strong> {paymentDetails.account_number}
              </Typography>
              <Typography variant="body1" paragraph>
                <strong>IFSC Code:</strong> {paymentDetails.ifsc_code}
              </Typography>
              {paymentDetails.bank_name && (
                <Typography variant="body1" paragraph>
                  <strong>Bank:</strong> {paymentDetails.bank_name}
                </Typography>
              )}
              <TextField
                fullWidth
                label="UPI Transaction ID (Optional)"
                value={upiId}
                onChange={(e) => setUpiId(e.target.value)}
                margin="normal"
                placeholder="Enter transaction reference"
              />
            </Box>
          );
        }
        return (
          <Box textAlign="center" py={4}>
            <CircularProgress size={60} />
            <Typography variant="h6" sx={{ mt: 2 }}>
              Opening payment gateway...
            </Typography>
          </Box>
        );

      case 2:
        return (
          <Box textAlign="center" py={4}>
            <Payment sx={{ fontSize: 80, color: 'success.main', mb: 2 }} />
            <Typography variant="h5" gutterBottom>
              Payment Successful!
            </Typography>
            <Typography variant="body1" color="text.secondary">
              Your order is now pending admin approval.
            </Typography>
          </Box>
        );

      default:
        return null;
    }
  };

  return (
    <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
      <DialogTitle>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <Payment color="primary" />
          <Typography variant="h6">Complete Payment</Typography>
        </Box>
      </DialogTitle>
      <DialogContent>
        <Box sx={{ mb: 3 }}>
          <Typography variant="body2" color="text.secondary">
            Order: {orderNumber}
          </Typography>
          <Typography variant="h5" fontWeight={700} color="primary">
            Rs. {amount}
          </Typography>
        </Box>

        <Stepper activeStep={activeStep} sx={{ mb: 3 }}>
          {steps.map((label) => (
            <Step key={label}>
              <StepLabel>{label}</StepLabel>
            </Step>
          ))}
        </Stepper>

        {error && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {error}
          </Alert>
        )}

        {!isLoaded && paymentMethod === 'razorpay' && (
          <Alert severity="warning" sx={{ mb: 2 }}>
            Loading payment gateway...
          </Alert>
        )}

        {renderStepContent()}
      </DialogContent>
      <DialogActions>
        {activeStep === 0 && <Button onClick={onClose}>Cancel</Button>}
        {activeStep === 1 && paymentMethod === 'manual' && (
          <Button onClick={() => setActiveStep(0)}>Back</Button>
        )}
        {activeStep === 2 && (
          <Button onClick={onClose} variant="contained">
            Done
          </Button>
        )}
        {activeStep < 2 && (
          <Button
            variant="contained"
            onClick={activeStep === 1 ? handlePayment : () => setActiveStep(1)}
            disabled={loading || (paymentMethod === 'razorpay' && !isLoaded)}
          >
            {activeStep === 1 ? 'Pay Now' : 'Continue'}
          </Button>
        )}
      </DialogActions>
    </Dialog>
  );
};

export default PaymentDialog;
