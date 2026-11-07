'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import axios from 'axios';
import { authAPI, apiErrorMessage } from '@/lib/api';
import { normalizePhone } from '@/lib/forms';
import type { ApiEnvelope, AuthPayload, RegisterInput } from '@/lib/types';
import { useAuthStore } from '@/store/authStore';

type FormState = {
  phone: string;
  username: string;
  full_name: string;
  email: string;
  password: string;
  password_confirm: string;
};

type FieldErrors = Partial<Record<keyof FormState, string>>;

const FIELDS: Array<{
  name: keyof FormState;
  label: string;
  type: string;
  required: boolean;
  autoComplete: string;
  placeholder?: string;
  hint?: string;
}> = [
  { name: 'phone', label: 'Phone number', type: 'tel', required: true, autoComplete: 'tel', placeholder: '+91 98765 43210' },
  { name: 'username', label: 'Username', type: 'text', required: true, autoComplete: 'username' },
  { name: 'full_name', label: 'Full name (optional)', type: 'text', required: false, autoComplete: 'name' },
  { name: 'email', label: 'Email (optional)', type: 'email', required: false, autoComplete: 'email' },
  { name: 'password', label: 'Password', type: 'password', required: true, autoComplete: 'new-password', hint: 'Minimum 8 characters' },
  { name: 'password_confirm', label: 'Confirm password', type: 'password', required: true, autoComplete: 'new-password' },
];

export default function SignupPage() {
  const router = useRouter();
  const setAuth = useAuthStore((state) => state.setAuth);

  const [formData, setFormData] = useState<FormState>({
    phone: '',
    username: '',
    full_name: '',
    email: '',
    password: '',
    password_confirm: '',
  });
  const [fieldErrors, setFieldErrors] = useState<FieldErrors>({});
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const update = (name: keyof FormState) => (e: React.ChangeEvent<HTMLInputElement>) => {
    setFormData((prev) => ({ ...prev, [name]: e.target.value }));
    if (fieldErrors[name]) setFieldErrors((prev) => ({ ...prev, [name]: undefined }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setFieldErrors({});

    if (formData.password !== formData.password_confirm) {
      setFieldErrors({ password_confirm: 'Passwords do not match' });
      return;
    }
    if (formData.password.length < 8) {
      setFieldErrors({ password: 'Password must be at least 8 characters' });
      return;
    }

    const payload: RegisterInput = {
      phone: normalizePhone(formData.phone),
      username: formData.username.trim(),
      password: formData.password,
      password_confirm: formData.password_confirm,
    };
    if (formData.full_name.trim()) payload.full_name = formData.full_name.trim();
    if (formData.email.trim()) payload.email = formData.email.trim();

    setLoading(true);
    try {
      const response = await authAPI.register(payload);
      const { user, access, refresh } = (response.data as ApiEnvelope<AuthPayload>).data;
      setAuth(user, access, refresh);
      router.push('/dashboard?welcome=1');
    } catch (err) {
      // DRF validation errors come back as { field: [message] } (or wrapped in `errors`).
      const body = axios.isAxiosError(err) ? err.response?.data : undefined;
      const source = (body && typeof body === 'object' && 'errors' in body ? body.errors : body) as
        | Record<string, unknown>
        | undefined;
      const mapped: FieldErrors = {};
      if (source && typeof source === 'object') {
        for (const field of FIELDS) {
          const v = source[field.name];
          if (Array.isArray(v) && v.length) mapped[field.name] = String(v[0]);
        }
      }
      setFieldErrors(mapped);
      setError(Object.keys(mapped).length ? 'Please correct the errors below.' : apiErrorMessage(err, 'Signup failed. Please try again.'));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-pink-50 via-purple-50 to-blue-50 flex items-center justify-center px-4 py-12">
      <div className="max-w-md w-full">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Create Account</h1>
          <p className="text-gray-600">Start creating beautiful wedding invitations</p>
        </div>

        <div className="card">
          <form onSubmit={handleSubmit} noValidate className="space-y-5">
            {error && (
              <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg" role="alert">
                {error}
              </div>
            )}

            {FIELDS.map((field) => (
              <div key={field.name}>
                <label htmlFor={field.name} className="block text-sm font-medium text-gray-700 mb-2">
                  {field.label}
                </label>
                <input
                  id={field.name}
                  type={field.type}
                  required={field.required}
                  autoComplete={field.autoComplete}
                  placeholder={field.placeholder}
                  className={`input-field ${fieldErrors[field.name] ? 'border-red-400' : ''}`}
                  value={formData[field.name]}
                  onChange={update(field.name)}
                />
                {fieldErrors[field.name] ? (
                  <p className="error-message">{fieldErrors[field.name]}</p>
                ) : (
                  field.hint && <p className="text-xs text-gray-500 mt-1">{field.hint}</p>
                )}
              </div>
            ))}

            <button
              type="submit"
              disabled={loading}
              className="w-full btn-primary disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? 'Creating account...' : 'Sign Up'}
            </button>
          </form>

          <div className="mt-6 text-center">
            <p className="text-gray-600">
              Already have an account?{' '}
              <Link href="/login" className="text-primary-600 hover:text-primary-700 font-semibold">
                Login
              </Link>
            </p>
          </div>

          <div className="mt-4 text-center">
            <Link href="/" className="text-gray-500 hover:text-gray-700 text-sm">
              Back to home
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
