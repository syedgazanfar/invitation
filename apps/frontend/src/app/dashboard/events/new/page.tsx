'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { eventsAPI, plansAPI, templatesAPI, apiErrorMessage } from '@/lib/api';
import { orderCreatePayload, pickReusableOrder } from '@/lib/orders';
import { bannerError, invitationFormData } from '@/lib/invitationForm';
import type { ApiEnvelope, InvitationDetail, OrderSummary, Paginated, Plan, Template } from '@/lib/types';

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
  const [existingOrder, setExistingOrder] = useState<OrderSummary | null>(null);
  const [notice, setNotice] = useState('');
  const [banner, setBanner] = useState<File | null>(null);
  const [bannerPreview, setBannerPreview] = useState<string | null>(null);

  useEffect(() => () => { if (bannerPreview) URL.revokeObjectURL(bannerPreview); }, [bannerPreview]);

  const handleBannerChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0] ?? null;
    const problem = file ? bannerError(file) : null;
    if (problem) {
      setError(problem);
      e.target.value = '';
      return;
    }
    setError('');
    setBanner(file);
    setBannerPreview(file ? URL.createObjectURL(file) : null);
  };

  useEffect(() => {
    plansAPI.getAll()
      .then((res) => setPlans((res.data as Paginated<Plan>).results ?? []))
      .catch((err) => setError(apiErrorMessage(err, 'Failed to load plans')));
    eventsAPI.getOrders()
      .then((res) => setExistingOrder(pickReusableOrder((res.data as Paginated<OrderSummary>).results ?? [])))
      .catch(() => setExistingOrder(null));
  }, []);

  const handleDetailsNext = () => {
    if (!eventData.event_title || !eventData.event_date || !eventData.event_venue || !eventData.host_name) {
      setError('Please fill in all required fields');
      return;
    }
    const problem = bannerError(banner);
    if (problem) {
      setError(problem);
      return;
    }
    setError('');
    setCurrentStep('plan');
  };

  const handlePlanSelect = async (planCode: string) => {
    setSelectedPlan(planCode);
    try {
      const res = await templatesAPI.getByPlan(planCode);
      setTemplates((res.data as ApiEnvelope<{ plan: Plan; templates: Template[] }>).data?.templates ?? []);
    } catch (err) {
      setError(apiErrorMessage(err, 'Failed to load templates'));
      setTemplates([]);
    }
    setCurrentStep('template');
  };

  const handleTemplateSelect = (templateId: string) => {
    setSelectedTemplate(templateId);
  };

  const handleCreateInvitation = async () => {
    if (!selectedPlan || !selectedTemplate || !banner) return;

    setLoading(true);
    setError('');

    try {
      // Step 1: reuse the user's open order, or create one. Django only lets an
      // invitation attach to an APPROVED order, and admins approve the latest one.
      let order = existingOrder;
      if (!order) {
        const orderRes = await eventsAPI.createOrder(orderCreatePayload(selectedPlan));
        order = (orderRes.data as ApiEnvelope<OrderSummary>).data;
        setExistingOrder(order);
      }
      if (order.status !== 'APPROVED') {
        setNotice(
          `Your order ${order.order_number} is awaiting admin approval. ` +
            'Once it is approved, come back here to create your invitation. Your details are kept on this page until you leave it.',
        );
        return;
      }

      // Step 2: create the invitation linked to the order
      const { event_time, ...details } = eventData;
      const invRes = await eventsAPI.create(
        invitationFormData(
          {
            ...details,
            order_id: order.id,
            template_id: selectedTemplate,
            event_date: new Date(`${eventData.event_date}T${event_time || '00:00'}`).toISOString(),
          },
          banner,
        ),
      );

      const created = (invRes.data as ApiEnvelope<InvitationDetail>).data;
      router.push(created?.slug ? `/dashboard/events/${created.slug}` : '/dashboard');
    } catch (err) {
      setError(apiErrorMessage(err, 'Failed to create invitation'));
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

      {notice && (
        <div className="bg-blue-50 border border-blue-200 text-blue-800 px-4 py-3 rounded-lg mb-6">{notice}</div>
      )}

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
              <label className="block text-sm font-medium text-gray-700 mb-2">Address</label>
              <input
                type="text"
                className="input-field"
                value={eventData.event_address}
                onChange={(e) => setEventData({ ...eventData, event_address: e.target.value })}
              />
            </div>

            <div className="md:col-span-2">
              <label htmlFor="banner" className="block text-sm font-medium text-gray-700 mb-2">Banner Image *</label>
              <input
                id="banner"
                type="file"
                accept=".jpg,.jpeg,.png,.webp,image/jpeg,image/png,image/webp"
                className="block w-full text-sm text-gray-600 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:bg-pink-50 file:text-pink-700 hover:file:bg-pink-100"
                onChange={handleBannerChange}
              />
              <p className="text-xs text-gray-500 mt-1">JPG, PNG or WEBP, up to 15 MB. Shown at the top of your invitation.</p>
              {bannerPreview && (
                // eslint-disable-next-line @next/next/no-img-element
                <img src={bannerPreview} alt="Banner preview" className="mt-3 w-full max-h-48 object-cover rounded-lg" />
              )}
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
                      {/* eslint-disable-next-line @next/next/no-img-element */}
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
