import Landing from '../_landing/Landing';
import { landingMetadata } from '../_landing/metadata';

export const metadata = landingMetadata('mr');

export default function MarathiHomePage() {
  return <Landing locale="mr" />;
}
