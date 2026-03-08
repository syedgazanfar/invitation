import { basicTemplates } from './basic';
import { premiumTemplates } from './premium';
import { luxuryTemplates } from './luxury';

export const allTemplates = [
  ...basicTemplates,
  ...premiumTemplates,
  ...luxuryTemplates,
];
