import { PlanCode } from '@prisma/client';

const BASE = '/templates';

export const premiumTemplates = [
  { id: 'premium-1',  name: 'Gilded Edges',         category: PlanCode.PREMIUM, previewUrl: `${BASE}/premium-1.html` },
  { id: 'premium-2',  name: 'Royal Crest',           category: PlanCode.PREMIUM, previewUrl: `${BASE}/premium-2.html` },
  { id: 'premium-3',  name: 'Lace & Pearls',         category: PlanCode.PREMIUM, previewUrl: `${BASE}/premium-3.html` },
  { id: 'premium-4',  name: 'Art Deco Glam',         category: PlanCode.PREMIUM, previewUrl: `${BASE}/premium-4.html` },
  { id: 'premium-5',  name: 'Vintage Floral',        category: PlanCode.PREMIUM, previewUrl: `${BASE}/premium-5.html` },
  { id: 'premium-6',  name: 'Satin & Silk',          category: PlanCode.PREMIUM, previewUrl: `${BASE}/premium-6.html` },
  { id: 'premium-7',  name: 'Golden Wreath',         category: PlanCode.PREMIUM, previewUrl: `${BASE}/premium-7.html` },
  { id: 'premium-8',  name: 'Monogrammed Elegance',  category: PlanCode.PREMIUM, previewUrl: `${BASE}/premium-8.html` },
  { id: 'premium-9',  name: 'Enchanted Forest',      category: PlanCode.PREMIUM, previewUrl: `${BASE}/premium-9.html` },
  { id: 'premium-10', name: 'Starry Night',          category: PlanCode.PREMIUM, previewUrl: `${BASE}/premium-10.html` },
  { id: 'premium-11', name: 'Regal Damask',          category: PlanCode.PREMIUM, previewUrl: `${BASE}/premium-11.html` },
  { id: 'premium-12', name: 'Ocean Breeze',          category: PlanCode.PREMIUM, previewUrl: `${BASE}/premium-12.html` },
  { id: 'premium-13', name: 'Tuscan Sunset',         category: PlanCode.PREMIUM, previewUrl: `${BASE}/premium-13.html` },
  { id: 'premium-14', name: 'Marble & Gold',         category: PlanCode.PREMIUM, previewUrl: `${BASE}/premium-14.html` },
  { id: 'premium-15', name: 'Chic Calligraphy',      category: PlanCode.PREMIUM, previewUrl: `${BASE}/premium-15.html` },
];
