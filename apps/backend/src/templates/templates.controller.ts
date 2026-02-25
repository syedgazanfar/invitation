import { Controller, Get, Query } from '@nestjs/common';
import { TemplatesService } from './templates.service';
import { PlanCode } from '@prisma/client';

@Controller('templates')
export class TemplatesController {
  constructor(private templatesService: TemplatesService) {}

  @Get()
  async findAll(@Query('plan') planCode?: PlanCode) {
    const templates = await this.templatesService.findByPlan(planCode);
    return {
      success: true,
      data: templates,
    };
  }
}
