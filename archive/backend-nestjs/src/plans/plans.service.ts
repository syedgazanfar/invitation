import { Injectable } from '@nestjs/common';
import { PrismaService } from '../prisma/prisma.service';

@Injectable()
export class PlansService {
  constructor(private prisma: PrismaService) {}

  async findAll() {
    return this.prisma.plan.findMany({
      orderBy: {
        basePriceUsd: 'asc',
      },
    });
  }

  async findOne(code: string) {
    return this.prisma.plan.findUnique({
      where: { code: code as any },
    });
  }
}
