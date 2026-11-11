import Landing from './_landing/Landing';
import { landingMetadata } from './_landing/metadata';

export const metadata = landingMetadata('en');

export default function HomePage() {
  return <Landing locale="en" />;
}
