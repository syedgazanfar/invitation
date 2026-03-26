'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { eventsAPI, plansAPI, templatesAPI } from '@/lib/api';
import { Plan, Template } from '@/types';

type Step = 'details' | 'plan' | 'template';

export default function NewEventPage() {
  const router = useRouter();

  const [currentStep, setCurrentStep] = useState<Step>('details');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const [plans, setPlans] = useState<Plan[]>([]);
  const [templates, setTemplates] = useState<Template[]>([]);

  const [eventData, setEventData] = useState({
    event_title: '',
    event_date: '',
    event_time: '',
    event_venue: '',
    event_address: '',
    host_name: '',
    custom_message: '',
  });

  const [selectedPlan, setSelectedPlan] = useState<string | null>(null);
  const [selectedTemplate, setSelectedTemplate] = useState<string | null>(null);
  const [orderId, setOrderId] = useState<string | null>(null);

  useEffect(() => {
    plansAPI.getAll()
      .then((res) => setPlans(res.data.results ?? []))
      .catch((err) => console.error('Failed to load plans:', err));
  }, []);

  const handleDetailsNext = () => {
    if (!eventData.event_title || !eventData.event_date || !eventData.event_venue ||
        !eventData.event_address || !eventData.host_name) {
      setError('Please fill in all required fields');
      return;
    }
    setError('');
    setCurrentStep('plan');
  };

  const handlePlanSelect = async (planCode: string) => {
    setSelectedPlan(planCode);
    try {
      const res = await templatesAPI.getByPlan(planCode);
      setTemplates(res.data.results ?? res.data.data ?? []);
    } catch (err) {
      console.error('Failed to load templates:', err);
      setTemplates([]);
    }
    setCurrentStep('template');
  };

  const handleTemplateSelect = (templateId: string) => {
    setSelectedTemplate(templateId);
  };

  const handleCreateInvitation = async () => {
    if (!selectedPlan || !selectedTemplate) return;

    setLoading(true);
    setError('');

    try {
      // Step 1: Create order for the selected plan
      const orderRes = await eventsAPI.createOrder({ plan_code: selectedPlan });
      const newOrderId = orderRes.data.id;
      setOrderId(newOrderId);

      // Step 2: Create invitation linked to the order
      const invRes = await eventsAPI.create({
        order: newOrderId,
        template: selectedTemplate,
        ...eventData,
      });

      router.push(`/dashboard`);
    } catch (err: any) {
      setError(err.response?.data?.detail || err.response?.data?.message || 'Failed to create invitation');
    } finally {
      setLoading(false);
    }
  };

  const stepIndex = ['details', 'plan', 'template'].indexOf(currentStep);

  return (
    <div className="max-w-4xl mx-auto">
      <h1 className="text-3xl font-bold text-gray-900 mb-8">Create Wedding Invitation</h1>

      {/* Progress */}
      <div className="mb-8">
        <div className="flex items-center justify-between">
          {(['Details', 'Plan', 'Template'] as const).map((label, index) => (
            <div key={label} className="flex items-center flex-1">
              <div className={`flex items-center justify-center w-10 h-10 rounded-full text-sm font-semibold ${
                stepIndex === index ? 'bg-pink-600 text-white' :
                stepIndex > index ? 'bg-green-600 text-white' : 'bg-gray-300 text-gray-600'
              }`}>
                {index + 1}
              </div>
              {index < 2 && (
                <div className={`flex-1 h-1 mx-2 ${stepIndex > index ? 'bg-green-600' : 'bg-gray-300'}`} />
              )}
            </div>
          ))}
        </div>
        <div className="flex justify-between mt-2 text-sm text-gray-600">
          <span>Details</span>
          <span>Plan</span>
          <span>Template</span>
        </div>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg mb-6">
          {error}
        </div>
      )}

      {/* Step 1: Details */}
      {currentStep === 'details' && (
        <div className="card">
          <h2 className="text-2xl font-semibold mb-6">Event Details</h2>

          <div className="grid md:grid-cols-2 gap-6">
            <div className="md:col-span-2">
              <label className="block text-sm font-medium text-gray-700 mb-2">Event Title *</label>
              <input
                type="text"
                required
                placeholder="e.g. Priya & Rahul Wedding"
                className="input-field"
                value={eventData.event_title}
                onChange={(e) => setEventData({ ...eventData, event_title: e.target.value })}
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Event Date *</label>
              <input
                type="date"
                required
                className="input-field"
                value={eventData.event_date}
                onChange={(e) => setEventData({ ...eventData, event_date: e.target.value })}
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Event Time</label>
              <input
                type="time"
                className="input-field"
                value={eventData.event_time}
                onChange={(e) => setEventData({ ...eventData, event_time: e.target.value })}
              />
            </div>

            <div className="md:col-span-2">
              <label className="block text-sm font-medium text-gray-700 mb-2">Host Name *</label>
              <input
                type="text"
                required
                placeholder="e.g. Sharma Family"
                className="input-field"
                value={eventData.host_name}
                onChange={(e) => setEventData({ ...eventData, host_name: e.target.value })}
              />
            </div>

            <div className="md:col-span-2">
              <label className="block text-sm font-medium text-gray-700 mb-2">Venue Name *</label>
              <input
                type="text"
                required
                className="input-field"
                value={eventData.event_venue}
                onChange={(e) => setEventData({ ...eventData, event_venue: e.target.value })}
              />
            </div>

            <div className="md:col-span-2">
              <label className="block text-sm font-medium text-gray-700 mb-2">Address *</label>
              <input
                type="text"
                required
                className="input-field"
                value={eventData.event_address}
                onChange={(e) => setEventData({ ...eventData, event_address: e.target.value })}
              />
            </div>

            <div className="md:col-span-2">
              <label className="block text-sm font-medium text-gray-700 mb-2">Custom Message (Optional)</label>
              <textarea
                rows={3}
                className="input-field"
                placeholder="A warm invitation message for your guests..."
                value={eventData.custom_message}
                onChange={(e) => setEventData({ ...eventData, custom_message: e.target.value })}
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

      {/* Step 2: Plan */}
      {currentStep === 'plan' && (
        <div className="card">
          <h2 className="text-2xl font-semibold mb-6">Choose Your Plan</h2>

          {plans.length === 0 ? (
            <p className="text-gray-500 text-center py-8">Loading plans...</p>
          ) : (
            <div className="grid md:grid-cols-3 gap-6">
              {plans.map((plan) => (
                <div
                  key={plan.code}
                  onClick={() => handlePlanSelect(plan.code)}
                  className={`border-2 rounded-xl p-6 cursor-pointer transition-all ${
                    selectedPlan === plan.code
                      ? 'border-pink-500 bg-pink-50'
                      : 'border-gray-200 hover:border-pink-300'
                  }`}
                >
                  <h3 className="text-xl font-bold mb-1">{plan.name}</h3>
                  <p className="text-2xl font-bold text-pink-600 mb-3">{plan.display_price}</p>
                  <p className="text-sm text-gray-500 mb-4">{plan.description}</p>
                  <ul className="space-y-1 text-sm text-gray-700">
                    {(plan.features ?? []).map((f, i) => (
                      <li key={i} className="flex items-center gap-1">
                        <span className="text-green-500">✓</span> {f}
                      </li>
                    ))}
                  </ul>
                </div>
              ))}
            </div>
          )}

          <div className="mt-6 flex justify-between">
            <button onClick={() => setCurrentStep('details')} className="btn-secondary">
              Back
            </button>
          </div>
        </div>
      )}

      {/* Step 3: Template */}
      {currentStep === 'template' && (
        <div className="card">
          <h2 className="text-2xl font-semibold mb-6">Choose a Template</h2>

          {templates.length === 0 ? (
            <p className="text-gray-500 text-center py-8">No templates available for this plan.</p>
          ) : (
            <div className="grid md:grid-cols-3 gap-6">
              {templates.map((template) => (
                <div
                  key={template.id}
                  onClick={() => handleTemplateSelect(template.id)}
                  className={`border-2 rounded-xl p-4 cursor-pointer transition-all ${
                    selectedTemplate === template.id
                      ? 'border-pink-500 bg-pink-50'
                      : 'border-gray-200 hover:border-pink-300'
                  }`}
                >
                  {template.thumbnail && (
                    <div className="aspect-video bg-gray-100 rounded-lg mb-3 overflow-hidden">
                      <img src={template.thumbnail} alt={template.name} className="w-full h-full object-cover" />
                    </div>
                  )}
                  <h3 className="font-semibold">{template.name}</h3>
                  <p className="text-sm text-gray-500">{template.description}</p>
                </div>
              ))}
            </div>
          )}

          <div className="mt-6 flex justify-between">
            <button onClick={() => setCurrentStep('plan')} className="btn-secondary">
              Back
            </button>
            <button
              onClick={handleCreateInvitation}
              disabled={!selectedTemplate || loading}
              className="btn-primary disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? 'Creating...' : 'Create Invitation'}
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
