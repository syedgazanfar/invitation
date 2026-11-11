import { redirect } from 'next/navigation';

/** The enquiry form now lives on the single landing page. */
export default function EnquiryRedirect() {
  redirect('/#enquire');
}
