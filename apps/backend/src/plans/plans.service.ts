import { Injectable, NotFoundException } from '@nestjs/common';
import { PrismaService } from '../prisma/prisma.service';
import { PlanCode } from '@prisma/client';

@Injectable()
export class PlansService {
  constructor(private prisma: PrismaService) {}

  async findAll() {
    return this.prisma.plan.findMany({
      orderBy: { basePriceUsd: 'asc' },
    });
  }

  async findOne(code: string) {
    const planCode = code.toUpperCase();

    if (!Object.values(PlanCode).includes(planCode as PlanCode)) {
      throw new NotFoundException(`Plan '${code}' not found`);
    }

    const plan = await this.prisma.plan.findUnique({
      where: { code: planCode as PlanCode },
    });

    if (!plan) {
      throw new NotFoundException(`Plan '${code}' not found`);
    }

    return plan;
  }
}
