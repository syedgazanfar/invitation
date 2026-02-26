/**
 * Error Fallback UI Component
 *
 * Displayed when an error is caught by the Error Boundary.
 */
import React, { ErrorInfo } from 'react';
import {
  Box,
  Container,
  Typography,
  Button,
  Paper,
  Accordion,
  AccordionSummary,
  AccordionDetails,
} from '@mui/material';
import {
  ErrorOutline,
  Refresh,
  Home,
  ExpandMore,
  BugReport,
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';

interface ErrorFallbackProps {
  error: Error | null;
  errorInfo: ErrorInfo | null;
  onReset?: () => void;
}

const ErrorFallback: React.FC<ErrorFallbackProps> = ({
  error,
  errorInfo,
  onReset,
}) => {
  const navigate = useNavigate();

  const handleReload = () => {
    if (onReset) {
      onReset();
    }
    window.location.reload();
  };

  const handleGoHome = () => {
    if (onReset) {
      onReset();
    }
    navigate('/');
  };

  const handleReportError = () => {
    // In production, this could open a support ticket or send error details
    const errorDetails = `
Error: ${error?.message || 'Unknown error'}

Stack Trace:
${error?.stack || 'No stack trace available'}

Component Stack:
${errorInfo?.componentStack || 'No component stack available'}
    `.trim();

    console.log('Error Report:', errorDetails);
    alert('Error details logged to console. In production, this would send an error report.');
  };

  return (
    <Container maxWidth="md" sx={{ py: 8 }}>
      <Box textAlign="center">
        {/* Error Icon */}
        <Box
          sx={{
            width: 120,
            height: 120,
            borderRadius: '50%',
            bgcolor: 'error.main',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            mx: 'auto',
            mb: 3,
          }}
        >
          <ErrorOutline sx={{ fontSize: 64, color: 'white' }} />
        </Box>

        {/* Error Message */}
        <Typography variant="h3" gutterBottom fontWeight={700}>
          Oops! Something Went Wrong
        </Typography>
        <Typography variant="h6" color="text.secondary" sx={{ mb: 4 }}>
          We're sorry for the inconvenience. An unexpected error occurred.
        </Typography>

        {/* Action Buttons */}
        <Box sx={{ display: 'flex', gap: 2, justifyContent: 'center', mb: 4, flexWrap: 'wrap' }}>
          <Button
            variant="contained"
            size="large"
            startIcon={<Refresh />}
            onClick={handleReload}
          >
            Reload Page
          </Button>
          <Button
            variant="outlined"
            size="large"
            startIcon={<Home />}
            onClick={handleGoHome}
          >
            Go to Home
          </Button>
          <Button
            variant="outlined"
            size="large"
            color="error"
            startIcon={<BugReport />}
            onClick={handleReportError}
          >
            Report Error
          </Button>
        </Box>

        {/* Error Details (Development Mode) */}
        {(process.env.NODE_ENV === 'development' || process.env.REACT_APP_SHOW_ERROR_DETAILS === 'true') && (
          <Paper sx={{ p: 3, textAlign: 'left', bgcolor: 'grey.100' }}>
            <Typography variant="h6" gutterBottom fontWeight={600} color="error">
              Error Details (Development Mode)
            </Typography>

            {error && (
              <Accordion>
                <AccordionSummary expandIcon={<ExpandMore />}>
                  <Typography variant="subtitle2" fontWeight={600}>
                    Error Message
                  </Typography>
                </AccordionSummary>
                <AccordionDetails>
                  <Typography
                    variant="body2"
                    component="pre"
                    sx={{
                      bgcolor: 'grey.900',
                      color: 'grey.100',
                      p: 2,
                      borderRadius: 1,
                      overflow: 'auto',
                      fontSize: '0.8rem',
                    }}
                  >
                    {error.toString()}
                  </Typography>
                </AccordionDetails>
              </Accordion>
            )}

            {error?.stack && (
              <Accordion>
                <AccordionSummary expandIcon={<ExpandMore />}>
                  <Typography variant="subtitle2" fontWeight={600}>
                    Stack Trace
                  </Typography>
                </AccordionSummary>
                <AccordionDetails>
                  <Typography
                    variant="body2"
                    component="pre"
                    sx={{
                      bgcolor: 'grey.900',
                      color: 'grey.100',
                      p: 2,
                      borderRadius: 1,
                      overflow: 'auto',
                      fontSize: '0.75rem',
                      whiteSpace: 'pre-wrap',
                    }}
                  >
                    {error.stack}
                  </Typography>
                </AccordionDetails>
              </Accordion>
            )}

            {errorInfo?.componentStack && (
              <Accordion>
                <AccordionSummary expandIcon={<ExpandMore />}>
                  <Typography variant="subtitle2" fontWeight={600}>
                    Component Stack
                  </Typography>
                </AccordionSummary>
                <AccordionDetails>
                  <Typography
                    variant="body2"
                    component="pre"
                    sx={{
                      bgcolor: 'grey.900',
                      color: 'grey.100',
                      p: 2,
                      borderRadius: 1,
                      overflow: 'auto',
                      fontSize: '0.75rem',
                      whiteSpace: 'pre-wrap',
                    }}
                  >
                    {errorInfo.componentStack}
                  </Typography>
                </AccordionDetails>
              </Accordion>
            )}
          </Paper>
        )}

        {/* User-Friendly Suggestions */}
        <Box sx={{ mt: 4, textAlign: 'left' }}>
          <Typography variant="subtitle2" gutterBottom fontWeight={600}>
            What can you do?
          </Typography>
          <ul style={{ marginTop: 8 }}>
            <li>
              <Typography variant="body2">Try reloading the page</Typography>
            </li>
            <li>
              <Typography variant="body2">Clear your browser cache and cookies</Typography>
            </li>
            <li>
              <Typography variant="body2">Check your internet connection</Typography>
            </li>
            <li>
              <Typography variant="body2">
                If the problem persists, please report it using the "Report Error" button
              </Typography>
            </li>
          </ul>
        </Box>
      </Box>
    </Container>
  );
};

export default ErrorFallback;
