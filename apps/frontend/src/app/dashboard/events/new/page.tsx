'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { eventsAPI, plansAPI, templatesAPI } from '@/lib/api';
import { Plan, Template, PlanCode } from '@/types';
import { useAuthStore } from '@/store/authStore';

type Step = 'details' | 'plan' | 'template' | 'payment';

export default function NewEventPage() {
  const router = useRouter();
  const user = useAuthStore((state) => state.user);

  const [currentStep, setCurrentStep] = useState<Step>('details');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  // Data
  const [plans, setPlans] = useState<Plan[]>([]);
  const [templates, setTemplates] = useState<Template[]>([]);
  const [pricing, setPricing] = useState<any>(null);

  // Form data
  const [eventData, setEventData] = useState({
    brideName: '',
    groomName: '',
    weddingDate: '',
    startTime: '',
    timezone: 'UTC',
    venueName: '',
    address: '',
    city: '',
    country: user?.preferredCountry || 'US',
    lat: null as number | null,
    lng: null as number | null,
    message: '',
  });

  const [selectedPlan, setSelectedPlan] = useState<PlanCode | null>(null);
  const [selectedTemplate, setSelectedTemplate] = useState<string | null>(null);

  useEffect(() => {
    loadPlans();
  }, []);

  const loadPlans = async () => {
    try {
      const response = await plansAPI.getAll();
      setPlans(response.data.data);
    } catch (err) {
      console.error('Failed to load plans:', err);
    }
  };

  const loadTemplates = async (planCode: PlanCode) => {
    try {
      const response = await templatesAPI.getByPlan(planCode);
      setTemplates(response.data.data);
    } catch (err) {
      console.error('Failed to load templates:', err);
    }
  };

  const loadPricing = async () => {
    if (!selectedPlan) return;

    try {
      const response = await plansAPI.getPricing(user?.preferredCountry || 'US');
      const planPricing = response.data.data.plans.find(
        (p: any) => p.planCode === selectedPlan
      );
      setPricing(planPricing);
    } catch (err) {
      console.error('Failed to load pricing:', err);
    }
  };

  const handleDetailsNext = () => {
    if (!eventData.brideName || !eventData.groomName || !eventData.weddingDate ||
        !eventData.startTime || !eventData.venueName || !eventData.address ||
        !eventData.city || !eventData.country) {
      setError('Please fill in all required fields');
      return;
    }
    setError('');
    setCurrentStep('plan');
  };

  const handlePlanSelect = async (planCode: PlanCode) => {
    setSelectedPlan(planCode);
    await loadTemplates(planCode);
    setCurrentStep('template');
  };

  const handleTemplateSelect = async (templateId: string) => {
    setSelectedTemplate(templateId);
    await loadPricing();
    setCurrentStep('payment');
  };

  const handleCreateEvent = async () => {
    if (!selectedPlan || !selectedTemplate) return;

    setLoading(true);
    setError('');

    try {
      // Step 1: Create event
      const eventResponse = await eventsAPI.create({
        ...eventData,
        planCode: selectedPlan,
        templateId: selectedTemplate,
      });

      const eventId = eventResponse.data.data.id;

      // Step 2: Process payment (stubbed)
      const paymentResponse = await eventsAPI.processPayment(eventId, {
        countryCode: user?.preferredCountry || 'US',
        simulateFailure: false,
      });

      if (!paymentResponse.data.success) {
        throw new Error('Payment failed');
      }

      // Step 3: Activate event
      await eventsAPI.activate(eventId);

      router.push(`/dashboard/events/${eventId}`);
    } catch (err: any) {
      setError(err.response?.data?.message || 'Failed to create event');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto">
      <h1 className="text-3xl font-bold text-gray-900 mb-8">Create Wedding Event</h1>

      {/* Progress Steps */}
      <div className="mb-8">
        <div className="flex items-center justify-between">
          {(['details', 'plan', 'template', 'payment'] as Step[]).map((step, index) => (
            <div key={step} className="flex items-center flex-1">
              <div className={`flex items-center justify-center w-10 h-10 rounded-full ${
                currentStep === step ? 'bg-primary-600 text-white' :
                ['details', 'plan', 'template', 'payment'].indexOf(currentStep) > index ?
                'bg-green-600 text-white' : 'bg-gray-300 text-gray-600'
              }`}>
                {index + 1}
              </div>
              {index < 3 && (
                <div className={`flex-1 h-1 mx-2 ${
                  ['details', 'plan', 'template', 'payment'].indexOf(currentStep) > index ?
                  'bg-green-600' : 'bg-gray-300'
                }`} />
              )}
            </div>
          ))}
        </div>
        <div className="flex justify-between mt-2 text-sm">
          <span>Details</span>
          <span>Plan</span>
          <span>Template</span>
          <span>Payment</span>
        </div>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg mb-6">
          {error}
        </div>
      )}

      {/* Step: Details */}
      {currentStep === 'details' && (
        <div className="card">
          <h2 className="text-2xl font-semibold mb-6">Wedding Details</h2>

          <div className="grid md:grid-cols-2 gap-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Bride Name *
              </label>
              <input
                type="text"
                required
                className="input-field"
                value={eventData.brideName}
                onChange={(e) => setEventData({ ...eventData, brideName: e.target.value })}
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Groom Name *
              </label>
              <input
                type="text"
                required
                className="input-field"
                value={eventData.groomName}
                onChange={(e) => setEventData({ ...eventData, groomName: e.target.value })}
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Wedding Date *
              </label>
              <input
                type="date"
                required
                className="input-field"
                value={eventData.weddingDate}
                onChange={(e) => setEventData({ ...eventData, weddingDate: e.target.value })}
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Start Time *
              </label>
              <input
                type="time"
                required
                className="input-field"
                value={eventData.startTime}
                onChange={(e) => setEventData({ ...eventData, startTime: e.target.value })}
              />
            </div>

            <div className="md:col-span-2">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Venue Name *
              </label>
              <input
                type="text"
                required
                className="input-field"
                value={eventData.venueName}
                onChange={(e) => setEventData({ ...eventData, venueName: e.target.value })}
              />
            </div>

            <div className="md:col-span-2">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Address *
              </label>
              <input
                type="text"
                required
                className="input-field"
                value={eventData.address}
                onChange={(e) => setEventData({ ...eventData, address: e.target.value })}
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                City *
              </label>
              <input
                type="text"
                required
                className="input-field"
                value={eventData.city}
                onChange={(e) => setEventData({ ...eventData, city: e.target.value })}
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Country *
              </label>
              <input
                type="text"
                required
                className="input-field"
                value={eventData.country}
                onChange={(e) => setEventData({ ...eventData, country: e.target.value })}
              />
            </div>

            <div className="md:col-span-2">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Message (Optional)
              </label>
              <textarea
                rows={4}
                className="input-field"
                value={eventData.message}
                onChange={(e) => setEventData({ ...eventData, message: e.target.value })}
              />
            </div>
          </div>

          <div className="mt-6 flex justify-end">
            <button onClick={handleDetailsNext} className="btn-primary">
              Next: Select Plan
            </button>
          </div>
        </div>
      )}

      {/* Step: Plan Selection */}
      {currentStep === 'plan' && (
        <div className="card">
          <h2 className="text-2xl font-semibold mb-6">Choose Your Plan</h2>

          <div className="grid md:grid-cols-3 gap-6">
            {plans.map((plan) => (
              <div
                key={plan.code}
                onClick={() => handlePlanSelect(plan.code)}
                className={`border-2 rounded-xl p-6 cursor-pointer transition-all ${
                  selectedPlan === plan.code ? 'border-primary-500 bg-primary-50' : 'border-gray-200 hover:border-primary-300'
                }`}
              >
                <h3 className="text-xl font-bold mb-2">{plan.name}</h3>
                <p className="text-3xl font-bold text-primary-600 mb-4">
                  ${plan.basePriceUsd}
                </p>
                <ul className="space-y-2 text-sm">
                  <li>{plan.maxRegularGuests} regular guests</li>
                  <li>{plan.maxTestGuests} test opens</li>
                  <li>5-day validity</li>
                  <li>Guest analytics</li>
                </ul>
              </div>
            ))}
          </div>

          <div className="mt-6 flex justify-between">
            <button onClick={() => setCurrentStep('details')} className="btn-secondary">
              Back
            </button>
          </div>
        </div>
      )}

      {/* Step: Template Selection */}
      {currentStep === 'template' && (
        <div className="card">
          <h2 className="text-2xl font-semibold mb-6">Choose Template</h2>

          <div className="grid md:grid-cols-3 gap-6">
            {templates.map((template) => (
              <div
                key={template.id}
                onClick={() => handleTemplateSelect(template.id)}
                className={`border-2 rounded-xl p-4 cursor-pointer transition-all ${
                  selectedTemplate === template.id ? 'border-primary-500 bg-primary-50' : 'border-gray-200 hover:border-primary-300'
                }`}
              >
                <div className="aspect-video bg-gray-200 rounded-lg mb-3 overflow-hidden">
                  <img src={template.previewUrl} alt={template.name} className="w-full h-full object-cover" />
                </div>
                <h3 className="font-semibold">{template.name}</h3>
                <p className="text-sm text-gray-600">{template.description}</p>
              </div>
            ))}
          </div>

          <div className="mt-6 flex justify-between">
            <button onClick={() => setCurrentStep('plan')} className="btn-secondary">
              Back
            </button>
          </div>
        </div>
      )}

      {/* Step: Payment */}
      {currentStep === 'payment' && pricing && (
        <div className="card">
          <h2 className="text-2xl font-semibold mb-6">Payment</h2>

          <div className="bg-gray-50 rounded-lg p-6 mb-6">
            <h3 className="font-semibold mb-4">Order Summary</h3>

            <div className="space-y-2">
              <div className="flex justify-between">
                <span>Plan: {pricing.planName}</span>
                <span>{pricing.currency} {pricing.basePriceLocal.toFixed(2)}</span>
              </div>
              <div className="flex justify-between text-sm text-gray-600">
                <span>Tax ({(pricing.breakdown.taxRate * 100).toFixed(0)}%)</span>
                <span>{pricing.currency} {pricing.tax.toFixed(2)}</span>
              </div>
              <div className="flex justify-between text-sm text-gray-600">
                <span>Service Fee</span>
                <span>{pricing.currency} {pricing.serviceFee.toFixed(2)}</span>
              </div>
              <div className="border-t pt-2 mt-2">
                <div className="flex justify-between font-bold text-lg">
                  <span>Total</span>
                  <span>{pricing.currency} {pricing.finalPrice.toFixed(2)}</span>
                </div>
              </div>
            </div>
          </div>

          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
            <p className="text-sm text-blue-800">
              This is a demo. Payment processing is simulated. Click "Complete Payment" to activate your event.
            </p>
          </div>

          <div className="flex justify-between">
            <button onClick={() => setCurrentStep('template')} className="btn-secondary">
              Back
            </button>
            <button
              onClick={handleCreateEvent}
              disabled={loading}
              className="btn-primary disabled:opacity-50"
            >
              {loading ? 'Processing...' : 'Complete Payment'}
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
