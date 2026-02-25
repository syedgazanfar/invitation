import { PrismaClient, PlanCode } from '@prisma/client';
import { allTemplates } from '../src/templates/data';

const prisma = new PrismaClient();

async function main() {
  console.log('Starting database seeding...');

  // Clear existing data (in development)
  if (process.env.NODE_ENV === 'development') {
    console.log('Clearing existing seed data...');
    await prisma.guest.deleteMany();
    await prisma.payment.deleteMany();
    await prisma.event.deleteMany();
    await prisma.template.deleteMany();
    await prisma.countryPricing.deleteMany();
    await prisma.plan.deleteMany();
  }

  // Seed Plans
  console.log('Seeding plans...');
  const plans = await Promise.all([
    prisma.plan.upsert({
      where: { code: PlanCode.BASIC },
      update: {},
      create: {
        code: PlanCode.BASIC,
        name: 'Basic Plan',
        basePriceUsd: 6.00,
        maxRegularGuests: 40,
        maxTestGuests: 5,
      },
    }),
    prisma.plan.upsert({
      where: { code: PlanCode.PREMIUM },
      update: {},
      create: {
        code: PlanCode.PREMIUM,
        name: 'Premium Plan',
        basePriceUsd: 12.00,
        maxRegularGuests: 100,
        maxTestGuests: 10,
      },
    }),
    prisma.plan.upsert({
      where: { code: PlanCode.LUXURY },
      update: {},
      create: {
        code: PlanCode.LUXURY,
        name: 'Luxury Plan',
        basePriceUsd: 20.00,
        maxRegularGuests: 150,
        maxTestGuests: 20,
      },
    }),
  ]);
  console.log(`Created ${plans.length} plans`);

  // Seed Country Pricing
  console.log('Seeding country pricing...');
  const countryPricingData = [
    {
      countryCode: 'US',
      countryName: 'United States',
      currency: 'USD',
      exchangeRate: 1.0000,
      multiplier: 1.00,
      taxRate: 0.08,
      serviceFee: 0.50,
    },
    {
      countryCode: 'IN',
      countryName: 'India',
      currency: 'INR',
      exchangeRate: 83.2500,
      multiplier: 0.90,
      taxRate: 0.18,
      serviceFee: 25.00,
    },
    {
      countryCode: 'GB',
      countryName: 'United Kingdom',
      currency: 'GBP',
      exchangeRate: 0.7900,
      multiplier: 1.10,
      taxRate: 0.20,
      serviceFee: 0.75,
    },
    {
      countryCode: 'CA',
      countryName: 'Canada',
      currency: 'CAD',
      exchangeRate: 1.3500,
      multiplier: 1.00,
      taxRate: 0.13,
      serviceFee: 0.60,
    },
    {
      countryCode: 'AU',
      countryName: 'Australia',
      currency: 'AUD',
      exchangeRate: 1.5000,
      multiplier: 1.05,
      taxRate: 0.10,
      serviceFee: 0.80,
    },
    {
      countryCode: 'DE',
      countryName: 'Germany',
      currency: 'EUR',
      exchangeRate: 0.9200,
      multiplier: 1.15,
      taxRate: 0.19,
      serviceFee: 0.70,
    },
    {
      countryCode: 'FR',
      countryName: 'France',
      currency: 'EUR',
      exchangeRate: 0.9200,
      multiplier: 1.15,
      taxRate: 0.20,
      serviceFee: 0.70,
    },
    {
      countryCode: 'JP',
      countryName: 'Japan',
      currency: 'JPY',
      exchangeRate: 145.0000,
      multiplier: 1.20,
      taxRate: 0.10,
      serviceFee: 100.00,
    },
    {
      countryCode: 'BR',
      countryName: 'Brazil',
      currency: 'BRL',
      exchangeRate: 5.0000,
      multiplier: 0.85,
      taxRate: 0.15,
      serviceFee: 2.00,
    },
    {
      countryCode: 'MX',
      countryName: 'Mexico',
      currency: 'MXN',
      exchangeRate: 17.0000,
      multiplier: 0.80,
      taxRate: 0.16,
      serviceFee: 10.00,
    },
  ];

  const countryPricing = await Promise.all(
    countryPricingData.map((data) =>
      prisma.countryPricing.upsert({
        where: { countryCode: data.countryCode },
        update: data,
        create: data,
      })
    )
  );
  console.log(`Created ${countryPricing.length} country pricing entries`);

  // Seed Templates
  console.log('Seeding templates...');
  const templatesToCreate = allTemplates.map((t) => ({
    id: t.id,
    name: t.name,
    planCode: t.category,
    previewUrl: t.previewUrl,
    description: `Beautiful ${t.name} template for your special day`,
  }));

  const createdTemplates = await prisma.template.createMany({
    data: templatesToCreate,
    skipDuplicates: true,
  });
  console.log(`Created ${createdTemplates.count} templates`);

  console.log('Database seeding completed successfully!');
  console.log(`
Summary:
- Plans: 3 (BASIC, PREMIUM, LUXURY)
- Country Pricing: ${countryPricing.length} countries
- Templates: ${createdTemplates.count}
  `);
}

main()
  .catch((e) => {
    console.error('Error during seeding:', e);
    process.exit(1);
  })
  .finally(async () => {
    await prisma.$disconnect();
  });
