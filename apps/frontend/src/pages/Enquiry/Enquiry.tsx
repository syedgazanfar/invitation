/**
 * Enquiry Page (public)
 *
 * Lets visitors send an enquiry. The backend stores it and notifies the team
 * (and the visitor) on WhatsApp via the WA-AKG gateway.
 */
import React, { useEffect, useState } from 'react';
import { Link as RouterLink } from 'react-router-dom';
import axios from 'axios';
import {
  Box,
  Container,
  Paper,
  Typography,
  MenuItem,
  Button,
} from '@mui/material';
import { Person, Event, Message, CheckCircle, WhatsApp } from '@mui/icons-material';
import { FormInput, PhoneInput, EmailInput, LoadingButton, Alert } from '../../components/ui';
import { enquiryApi, EnquiryPayload } from '../../services/api';

const DEFAULT_EVENT_TYPES = [
  { value: 'WEDDING', label: 'Wedding' },
  { value: 'ENGAGEMENT', label: 'Engagement' },
  { value: 'BIRTHDAY', label: 'Birthday' },
  { value: 'PARTY', label: 'Party' },
  { value: 'RELIGIOUS', label: 'Religious / Festival' },
  { value: 'OTHER', label: 'Other' },
];

const EMPTY_FORM: EnquiryPayload = {
  name: '',
  phone: '',
  email: '',
  event_type: 'WEDDING',
  event_date: '',
  message: '',
  website: '',
};

type FieldErrors = Partial<Record<keyof EnquiryPayload, string>>;

const today = () => new Date().toISOString().slice(0, 10);

const Enquiry: React.FC = () => {
  const [form, setForm] = useState<EnquiryPayload>(EMPTY_FORM);
  const [eventTypes, setEventTypes] = useState(DEFAULT_EVENT_TYPES);
  const [fieldErrors, setFieldErrors] = useState<FieldErrors>({});
  const [error, setError] = useState('');
  const [successMessage, setSuccessMessage] = useState('');
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    enquiryApi
      .getOptions()
      .then(res => {
        if (res.success && res.data?.event_types?.length) setEventTypes(res.data.event_types);
      })
      .catch(() => {
        /* fall back to defaults */
      });
  }, []);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target;
    setForm(prev => ({ ...prev, [name]: value }));
    if (fieldErrors[name as keyof EnquiryPayload]) {
      setFieldErrors(prev => ({ ...prev, [name]: undefined }));
    }
  };

  const validate = (): boolean => {
    const errs: FieldErrors = {};
    if (form.name.trim().length < 2) errs.name = 'Please enter your name.';
    const digits = form.phone.replace(/\D/g, '');
    if (digits.length < 10) errs.phone = 'Enter a valid WhatsApp number.';
    if (form.email && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(form.email)) errs.email = 'Enter a valid email.';
    setFieldErrors(errs);
    return Object.keys(errs).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    if (!validate()) return;

    setSubmitting(true);
    try {
      const payload: EnquiryPayload = {
        ...form,
        email: form.email || '',
        event_date: form.event_date || null,
      };
      const res = await enquiryApi.submit(payload);
      setSuccessMessage(res.message || "Thanks! We'll contact you on WhatsApp shortly.");
      setForm(EMPTY_FORM);
    } catch (err) {
      if (axios.isAxiosError(err)) {
        if (err.response?.status === 429) {
          setError('Too many enquiries from this device. Please try again later.');
        } else if (err.response?.data?.errors) {
          const apiErrors = err.response.data.errors as Record<string, string[]>;
          const mapped: FieldErrors = {};
          Object.entries(apiErrors).forEach(([k, v]) => {
            mapped[k as keyof EnquiryPayload] = Array.isArray(v) ? v[0] : String(v);
          });
          setFieldErrors(mapped);
          setError(err.response.data.message || 'Please correct the errors below.');
        } else {
          setError('Could not send your enquiry. Please check your connection and try again.');
        }
      } else {
        setError('Something went wrong. Please try again.');
      }
    } finally {
      setSubmitting(false);
    }
  };

  if (successMessage) {
    return (
      <Container maxWidth="sm" sx={{ py: { xs: 6, md: 10 } }}>
        <Paper elevation={0} sx={{ p: { xs: 3, md: 5 }, textAlign: 'center', borderRadius: 3, border: 1, borderColor: 'divider' }}>
          <CheckCircle color="success" sx={{ fontSize: 64, mb: 2 }} />
          <Typography variant="h5" fontWeight={700} gutterBottom>
            Enquiry sent
          </Typography>
          <Typography color="text.secondary" sx={{ mb: 4 }}>
            {successMessage}
          </Typography>
          <Box sx={{ display: 'flex', gap: 2, justifyContent: 'center', flexWrap: 'wrap' }}>
            <Button variant="outlined" onClick={() => setSuccessMessage('')}>
              Send another
            </Button>
            <Button variant="contained" component={RouterLink} to="/plans">
              View plans
            </Button>
          </Box>
        </Paper>
      </Container>
    );
  }

  return (
    <Container maxWidth="sm" sx={{ py: { xs: 4, md: 8 } }}>
      <Box sx={{ textAlign: 'center', mb: 4 }}>
        <Typography variant="h4" component="h1" fontWeight={700} gutterBottom>
          Send us an enquiry
        </Typography>
        <Typography color="text.secondary">
          Tell us about your event and we'll reply on{' '}
          <Box component="span" sx={{ display: 'inline-flex', alignItems: 'center', color: '#25D366', fontWeight: 600 }}>
            <WhatsApp fontSize="small" sx={{ mr: 0.5 }} />
            WhatsApp
          </Box>
          .
        </Typography>
      </Box>

      <Paper
        component="form"
        noValidate
        onSubmit={handleSubmit}
        elevation={0}
        sx={{ p: { xs: 3, md: 4 }, borderRadius: 3, border: 1, borderColor: 'divider' }}
      >
        {error && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {error}
          </Alert>
        )}

        <FormInput
          label="Your name"
          name="name"
          value={form.name}
          onChange={handleChange}
          startIcon={<Person color="action" />}
          error={!!fieldErrors.name}
          helperText={fieldErrors.name}
          autoComplete="name"
          required
        />

        <PhoneInput
          label="WhatsApp number"
          name="phone"
          value={form.phone}
          onChange={handleChange}
          error={!!fieldErrors.phone}
          helperText={fieldErrors.phone || "We'll reply on this number"}
          autoComplete="tel"
          required
        />

        <EmailInput
          label="Email (optional)"
          name="email"
          value={form.email}
          onChange={handleChange}
          error={!!fieldErrors.email}
          helperText={fieldErrors.email}
        />

        <FormInput
          select
          label="Event type"
          name="event_type"
          value={form.event_type}
          onChange={handleChange}
          error={!!fieldErrors.event_type}
          helperText={fieldErrors.event_type}
        >
          {eventTypes.map(opt => (
            <MenuItem key={opt.value} value={opt.value}>
              {opt.label}
            </MenuItem>
          ))}
        </FormInput>

        <FormInput
          type="date"
          label="Event date (optional)"
          name="event_date"
          value={form.event_date || ''}
          onChange={handleChange}
          startIcon={<Event color="action" />}
          InputLabelProps={{ shrink: true }}
          inputProps={{ min: today() }}
          error={!!fieldErrors.event_date}
          helperText={fieldErrors.event_date}
        />

        <FormInput
          label="Message"
          name="message"
          value={form.message}
          onChange={handleChange}
          startIcon={<Message color="action" />}
          multiline
          minRows={4}
          inputProps={{ maxLength: 2000 }}
          placeholder="Language, design style, number of guests, anything else…"
          error={!!fieldErrors.message}
          helperText={fieldErrors.message}
        />

        {/* Honeypot: hidden from people, bots fill it */}
        <Box sx={{ position: 'absolute', left: '-10000px', width: 1, height: 1, overflow: 'hidden' }} aria-hidden="true">
          <input type="text" name="website" tabIndex={-1} autoComplete="off" value={form.website} onChange={handleChange} />
        </Box>

        <LoadingButton
          type="submit"
          variant="contained"
          size="large"
          fullWidth
          loading={submitting}
          sx={{ mt: 3, py: 1.5 }}
        >
          Send enquiry
        </LoadingButton>
      </Paper>
    </Container>
  );
};

export default Enquiry;
