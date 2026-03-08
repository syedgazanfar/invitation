import { PlanCode } from '@prisma/client';

const BASE = '/templates';

export const luxuryTemplates = [
  { id: 'luxury-1',  name: 'Diamond Dust',          category: PlanCode.LUXURY, previewUrl: `${BASE}/luxury-1.html` },
  { id: 'luxury-2',  name: 'Velvet & Gold Foil',    category: PlanCode.LUXURY, previewUrl: `${BASE}/luxury-2.html` },
  { id: 'luxury-3',  name: 'Crystal Brooch',        category: PlanCode.LUXURY, previewUrl: `${BASE}/luxury-3.html` },
  { id: 'luxury-4',  name: 'Letterpress Luxury',    category: PlanCode.LUXURY, previewUrl: `${BASE}/luxury-4.html` },
  { id: 'luxury-5',  name: 'Silk Ribbon',           category: PlanCode.LUXURY, previewUrl: `${BASE}/luxury-5.html` },
  { id: 'luxury-6',  name: 'Gatsby Gala',           category: PlanCode.LUXURY, previewUrl: `${BASE}/luxury-6.html` },
  { id: 'luxury-7',  name: 'Royal Invitation',      category: PlanCode.LUXURY, previewUrl: `${BASE}/luxury-7.html` },
  { id: 'luxury-8',  name: 'Fairytale Castle',      category: PlanCode.LUXURY, previewUrl: `${BASE}/luxury-8.html` },
  { id: 'luxury-9',  name: 'Midnight Masquerade',   category: PlanCode.LUXURY, previewUrl: `${BASE}/luxury-9.html` },
  { id: 'luxury-10', name: 'Opulent Orchid',        category: PlanCode.LUXURY, previewUrl: `${BASE}/luxury-10.html` },
  { id: 'luxury-11', name: 'Champagne Celebration', category: PlanCode.LUXURY, previewUrl: `${BASE}/luxury-11.html` },
  { id: 'luxury-12', name: 'Celestial Dream',       category: PlanCode.LUXURY, previewUrl: `${BASE}/luxury-12.html` },
  { id: 'luxury-13', name: 'Secret Garden',         category: PlanCode.LUXURY, previewUrl: `${BASE}/luxury-13.html` },
  { id: 'luxury-14', name: 'Black Tie Affair',      category: PlanCode.LUXURY, previewUrl: `${BASE}/luxury-14.html` },
  { id: 'luxury-15', name: 'Rose Gold Romance',     category: PlanCode.LUXURY, previewUrl: `${BASE}/luxury-15.html` },
  { id: 'luxury-16', name: 'Emerald Isle',          category: PlanCode.LUXURY, previewUrl: `${BASE}/luxury-16.html` },
  { id: 'luxury-17', name: 'Sapphire Skies',        category: PlanCode.LUXURY, previewUrl: `${BASE}/luxury-17.html` },
  { id: 'luxury-18', name: 'Platinum Peony',        category: PlanCode.LUXURY, previewUrl: `${BASE}/luxury-18.html` },
  { id: 'luxury-19', name: 'Glimmering Gala',       category: PlanCode.LUXURY, previewUrl: `${BASE}/luxury-19.html` },
  { id: 'luxury-20', name: 'Timeless Treasure',     category: PlanCode.LUXURY, previewUrl: `${BASE}/luxury-20.html` },
];
