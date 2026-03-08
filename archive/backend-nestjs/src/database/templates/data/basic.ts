import { PlanCode } from '@prisma/client';

const BASE = '/templates';

export const basicTemplates = [
  { id: 'basic-1',  name: 'Minimalist Charm',  category: PlanCode.BASIC, previewUrl: `${BASE}/basic-1.html` },
  { id: 'basic-2',  name: 'Classic Script',    category: PlanCode.BASIC, previewUrl: `${BASE}/basic-2.html` },
  { id: 'basic-3',  name: 'Simple & Sweet',    category: PlanCode.BASIC, previewUrl: `${BASE}/basic-3.html` },
  { id: 'basic-4',  name: 'Modern Lines',      category: PlanCode.BASIC, previewUrl: `${BASE}/basic-4.html` },
  { id: 'basic-5',  name: 'Rustic Heart',      category: PlanCode.BASIC, previewUrl: `${BASE}/basic-5.html` },
  { id: 'basic-6',  name: 'Floral Border',     category: PlanCode.BASIC, previewUrl: `${BASE}/basic-6.html` },
  { id: 'basic-7',  name: 'Clean Type',        category: PlanCode.BASIC, previewUrl: `${BASE}/basic-7.html` },
  { id: 'basic-8',  name: 'Watercolor Wash',   category: PlanCode.BASIC, previewUrl: `${BASE}/basic-8.html` },
  { id: 'basic-9',  name: 'Elegant Frame',     category: PlanCode.BASIC, previewUrl: `${BASE}/basic-9.html` },
  { id: 'basic-10', name: 'Bold & Beautiful',  category: PlanCode.BASIC, previewUrl: `${BASE}/basic-10.html` },
  { id: 'basic-11', name: 'Geometric Shapes',  category: PlanCode.BASIC, previewUrl: `${BASE}/basic-11.html` },
  { id: 'basic-12', name: 'Leafy Accents',     category: PlanCode.BASIC, previewUrl: `${BASE}/basic-12.html` },
  { id: 'basic-13', name: 'Simply Stated',     category: PlanCode.BASIC, previewUrl: `${BASE}/basic-13.html` },
  { id: 'basic-14', name: 'Dotted Delight',    category: PlanCode.BASIC, previewUrl: `${BASE}/basic-14.html` },
  { id: 'basic-15', name: 'Corner Flourish',   category: PlanCode.BASIC, previewUrl: `${BASE}/basic-15.html` },
];
