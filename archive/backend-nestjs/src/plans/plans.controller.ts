import { Controller, Get, Query, Param } from '@nestjs/common';
import { PlansService } from './plans.service';
import { PricingService } from '../pricing/pricing.service';

@Controller('plans')
export class PlansController {
  constructor(
    private plansService: PlansService,
    private pricingService: PricingService,
  ) {}

  @Get()
  async findAll() {
    const plans = await this.plansService.findAll();
    return {
      success: true,
      data: plans.map(plan => ({
        code: plan.code,
        name: plan.name,
        basePriceUsd: Number(plan.basePriceUsd),
        maxRegularGuests: plan.maxRegularGuests,
        maxTestGuests: plan.maxTestGuests,
        totalGuestLimit: plan.maxRegularGuests + plan.maxTestGuests,
      })),
    };
  }

  @Get('pricing')
  async getPricing(@Query('country') countryCode: string = 'US') {
    const pricing = await this.pricingService.getAllPlansPricing(countryCode);
    return {
      success: true,
      data: pricing,
    };
  }

  @Get('countries')
  async getCountries() {
    const countries = await this.pricingService.getAvailableCountries();
    return {
      success: true,
      data: countries,
    };
  }

  @Get(':code')
  async findOne(@Param('code') code: string) {
    const plan = await this.plansService.findOne(code);
    return {
      success: true,
      data: plan,
    };
  }
}
