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
    simulateFailure: boolean = false,
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

    if (event.payment) {
      throw new BadRequestException('Payment has already been processed for this event');
    }

    const pricing = await this.pricingService.calculatePlanPrice(event.planCode, countryCode);

    const transactionId = `TXN_${nanoid()}`;
    const paymentStatus = simulateFailure ? PaymentStatus.FAILED : PaymentStatus.COMPLETED;

    const payment = await this.prisma.payment.create({
      data: {
        eventId,
        amount: pricing.finalPrice,
        currency: pricing.currency,
        countryCode,
        status: paymentStatus,
        paymentMethod,
        transactionId,
      },
    });

    return {
      payment,
      pricing,
      success: paymentStatus === PaymentStatus.COMPLETED,
    };
  }

  async getPaymentByEventId(eventId: string) {
    return this.prisma.payment.findUnique({ where: { eventId } });
  }
}
