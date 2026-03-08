import {
  Injectable,
  NotFoundException,
  ForbiddenException,
  BadRequestException,
} from '@nestjs/common';
import { PrismaService } from '../prisma/prisma.service';
import { PricingService } from '../pricing/pricing.service';
import { PaymentStatus } from '@prisma/client';
import { customAlphabet } from 'nanoid';

const nanoid = customAlphabet('0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ', 16);

@Injectable()
export class PaymentService {
  constructor(
    private prisma: PrismaService,
    private pricingService: PricingService,
  ) {}

  async processPayment(
    eventId: string,
    userId: string,
    countryCode: string,
    paymentMethod: string = 'card',
  ) {
    const event = await this.prisma.event.findUnique({
      where: { id: eventId },
      include: { plan: true, payment: true },
    });

    if (!event) {
      throw new NotFoundException('Event not found');
    }

    if (event.userId !== userId) {
      throw new ForbiddenException('You do not have permission to process payment for this event');
    }

    // Block only if a COMPLETED payment already exists; a FAILED payment can be retried
    if (event.payment?.status === PaymentStatus.COMPLETED) {
      throw new BadRequestException('Payment has already been completed for this event');
    }

    const pricing = await this.pricingService.calculatePlanPrice(event.planCode, countryCode);

    const transactionId = `TXN_${nanoid()}`;

    // Upsert: replace any previous FAILED payment record, or create fresh
    const payment = await this.prisma.payment.upsert({
      where: { eventId },
      create: {
        eventId,
        amount: pricing.finalPrice,
        currency: pricing.currency,
        countryCode,
        status: PaymentStatus.COMPLETED,
        paymentMethod,
        transactionId,
      },
      update: {
        amount: pricing.finalPrice,
        currency: pricing.currency,
        countryCode,
        status: PaymentStatus.COMPLETED,
        paymentMethod,
        transactionId,
      },
    });

    return {
      payment,
      pricing,
      success: true,
    };
  }

  async getPaymentByEventId(eventId: string) {
    return this.prisma.payment.findUnique({ where: { eventId } });
  }
}
