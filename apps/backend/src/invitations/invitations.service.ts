import { Injectable, NotFoundException, BadRequestException } from '@nestjs/common';
import { PrismaService } from '../prisma/prisma.service';
import { EventStatus } from '@prisma/client';

@Injectable()
export class InvitationsService {
  constructor(private prisma: PrismaService) {}

  async getInvitationMeta(slug: string) {
    const event = await this.findActiveEvent(slug);
    return {
      slug: event.slug,
      status: event.status,
      expiresAt: event.expiresAt,
      templateName: event.template.name,
      templatePreviewUrl: event.template.previewUrl,
    };
  }

  async registerGuest(
    slug: string,
    guestName: string,
    isTest: boolean = false,
    ip?: string,
    userAgent?: string,
  ) {
    // Atomic check-and-insert to prevent race conditions on guest limits
    return this.prisma.$transaction(async (tx) => {
      const event = await tx.event.findUnique({
        where: { slug },
        include: { plan: true, template: true },
      });

      if (!event) throw new NotFoundException('Invitation not found');
      if (event.status !== EventStatus.ACTIVE) throw new BadRequestException('This invitation is not active');

      if (event.expiresAt && new Date() > event.expiresAt) {
        await tx.event.update({ where: { id: event.id }, data: { status: EventStatus.EXPIRED } });
        throw new BadRequestException('This invitation has expired');
      }

      const guestCount = await tx.guest.count({ where: { eventId: event.id, isTest } });
      const limit = isTest ? event.plan.maxTestGuests : event.plan.maxRegularGuests;
      const limitLabel = isTest ? 'Test guest' : 'Guest';

      if (guestCount >= limit) {
        throw new BadRequestException(`${limitLabel} limit reached (${limit} maximum)`);
      }

      const guest = await tx.guest.create({
        data: { eventId: event.id, guestName, isTest, ip, userAgent },
      });

      return {
        guest: { id: guest.id, name: guest.guestName },
        event: {
          brideName: event.brideName,
          groomName: event.groomName,
          weddingDate: event.weddingDate,
          startTime: event.startTime,
          timezone: event.timezone,
          venueName: event.venueName,
          address: event.address,
          city: event.city,
          country: event.country,
          lat: event.lat ? Number(event.lat) : null,
          lng: event.lng ? Number(event.lng) : null,
          message: event.message,
        },
      };
    });
  }

  async getRemainingSlots(slug: string) {
    const event = await this.findActiveEvent(slug);

    const [regularCount, testCount] = await Promise.all([
      this.prisma.guest.count({ where: { eventId: event.id, isTest: false } }),
      this.prisma.guest.count({ where: { eventId: event.id, isTest: true } }),
    ]);

    return {
      regular: {
        used: regularCount,
        max: event.plan.maxRegularGuests,
        remaining: event.plan.maxRegularGuests - regularCount,
      },
      test: {
        used: testCount,
        max: event.plan.maxTestGuests,
        remaining: event.plan.maxTestGuests - testCount,
      },
    };
  }

  private async findActiveEvent(slug: string) {
    const event = await this.prisma.event.findUnique({
      where: { slug },
      include: { plan: true, template: true },
    });

    if (!event) throw new NotFoundException('Invitation not found');
    if (event.status !== EventStatus.ACTIVE) throw new BadRequestException('This invitation is not active');

    if (event.expiresAt && new Date() > event.expiresAt) {
      await this.prisma.event.update({
        where: { id: event.id },
        data: { status: EventStatus.EXPIRED },
      });
      throw new BadRequestException('This invitation has expired');
    }

    return event;
  }
}
