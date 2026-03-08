import { Injectable, NotFoundException } from '@nestjs/common';
import { PrismaService } from '../prisma/prisma.service';
import { PlanCode } from '@prisma/client';
import { Decimal } from '@prisma/client/runtime/library';

export interface PriceBreakdown {
  planCode: PlanCode;
  planName: string;
  countryCode: string;
  currency: string;
  basePriceUsd: number;
  basePriceLocal: number;
  adjustedPrice: number;
  tax: number;
  serviceFee: number;
  finalPrice: number;
  breakdown: {
    baseUsd: number;
    exchangeRate: number;
    baseLocal: number;
    multiplier: number;
    adjusted: number;
    taxRate: number;
    taxAmount: number;
    serviceFee: number;
    total: number;
  };
}

export interface CountryPlanPricing {
  countryCode: string;
  countryName: string;
  currency: string;
  plans: PriceBreakdown[];
}

@Injectable()
export class PricingService {
  constructor(private prisma: PrismaService) {}

  /**
   * Calculate final price for a plan in a specific country
   * Formula: ((base_usd * exchange_rate) * multiplier) + tax + service_fee
   */
  async calculatePlanPrice(
    planCode: PlanCode,
    countryCode: string = 'US'
  ): Promise<PriceBreakdown> {
    // Fetch plan
    const plan = await this.prisma.plan.findUnique({
      where: { code: planCode },
    });

    if (!plan) {
      throw new NotFoundException(`Plan ${planCode} not found`);
    }

    // Fetch country pricing
    const countryPricing = await this.prisma.countryPricing.findUnique({
      where: { countryCode },
    });

    if (!countryPricing) {
      throw new NotFoundException(`Country pricing for ${countryCode} not found`);
    }

    // Convert Decimal to number for calculations
    const basePriceUsd = Number(plan.basePriceUsd);
    const exchangeRate = Number(countryPricing.exchangeRate);
    const multiplier = Number(countryPricing.multiplier);
    const taxRate = Number(countryPricing.taxRate);
    const serviceFee = Number(countryPricing.serviceFee);

    // Step 1: Convert USD to local currency
    const basePriceLocal = basePriceUsd * exchangeRate;

    // Step 2: Apply country-specific multiplier
    const adjustedPrice = basePriceLocal * multiplier;

    // Step 3: Calculate tax
    const tax = adjustedPrice * taxRate;

    // Step 4: Calculate final price
    const finalPrice = adjustedPrice + tax + serviceFee;

    return {
      planCode: plan.code,
      planName: plan.name,
      countryCode: countryPricing.countryCode,
      currency: countryPricing.currency,
      basePriceUsd,
      basePriceLocal: this.round(basePriceLocal),
      adjustedPrice: this.round(adjustedPrice),
      tax: this.round(tax),
      serviceFee,
      finalPrice: this.round(finalPrice),
      breakdown: {
        baseUsd: basePriceUsd,
        exchangeRate,
        baseLocal: this.round(basePriceLocal),
        multiplier,
        adjusted: this.round(adjustedPrice),
        taxRate,
        taxAmount: this.round(tax),
        serviceFee,
        total: this.round(finalPrice),
      },
    };
  }

  /**
   * Get pricing for all plans in a specific country
   */
  async getAllPlansPricing(countryCode: string = 'US'): Promise<CountryPlanPricing> {
    // Verify country exists
    const countryPricing = await this.prisma.countryPricing.findUnique({
      where: { countryCode },
    });

    if (!countryPricing) {
      throw new NotFoundException(`Country pricing for ${countryCode} not found`);
    }

    // Calculate pricing for all plans
    const planCodes = Object.values(PlanCode);
    const planPricing = await Promise.all(
      planCodes.map(code => this.calculatePlanPrice(code, countryCode))
    );

    return {
      countryCode: countryPricing.countryCode,
      countryName: countryPricing.countryName,
      currency: countryPricing.currency,
      plans: planPricing,
    };
  }

  /**
   * Get all available countries
   */
  async getAvailableCountries() {
    return this.prisma.countryPricing.findMany({
      select: {
        countryCode: true,
        countryName: true,
        currency: true,
      },
      orderBy: {
        countryName: 'asc',
      },
    });
  }

  /**
   * Round to 2 decimal places
   */
  private round(value: number): number {
    return Math.round(value * 100) / 100;
  }
}
