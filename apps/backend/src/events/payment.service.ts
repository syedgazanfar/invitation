import { Injectable } from '@nestjs/common';
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

  /**
   * Process payment (stubbed implementation)
   * In production, this would integrate with Stripe/PayPal
   */
  async processPayment(
    eventId: string,
    countryCode: string,
    paymentMethod: string = 'card',
    simulateFailure: boolean = false
  ) {
    // Get event details
    const event = await this.prisma.event.findUnique({
      where: { id: eventId },
      include: { plan: true },
    });

    if (!event) {
      throw new Error('Event not found');
    }

    // Calculate pricing
    const pricing = await this.pricingService.calculatePlanPrice(
      event.planCode,
      countryCode
    );

    // Simulate payment processing
    const transactionId = `TXN_${nanoid()}`;

    // Simulate success/failure
    const paymentStatus = simulateFailure ? PaymentStatus.FAILED : PaymentStatus.COMPLETED;

    // Create payment record
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
    return this.prisma.payment.findUnique({
      where: { eventId },
    });
  }
}
