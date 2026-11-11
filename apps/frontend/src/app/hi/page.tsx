import Landing from '../_landing/Landing';
import { landingMetadata } from '../_landing/metadata';

export const metadata = landingMetadata('hi');

export default function HindiHomePage() {
  return <Landing locale="hi" />;
}
