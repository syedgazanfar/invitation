import { Injectable, NotFoundException, BadRequestException } from '@nestjs/common';
import { PrismaService } from '../prisma/prisma.service';
import { EventStatus } from '@prisma/client';

@Injectable()
export class InvitationsService {
  constructor(private prisma: PrismaService) {}

  /**
   * Get invitation metadata by slug (public access)
   * Checks if event is active and not expired
   */
  async getInvitationMeta(slug: string) {
    const event = await this.prisma.event.findUnique({
      where: { slug },
      include: {
        plan: true,
        template: true,
      },
    });

    if (!event) {
      throw new NotFoundException('Invitation not found');
    }

    // Check if event is active
    if (event.status !== EventStatus.ACTIVE) {
      throw new BadRequestException('This invitation is not active');
    }

    // Check if expired
    const now = new Date();
    if (event.expiresAt && now > event.expiresAt) {
      // Auto-update status to expired
      await this.prisma.event.update({
        where: { id: event.id },
        data: { status: EventStatus.EXPIRED },
      });

      throw new BadRequestException('This invitation has expired');
    }

    // Return limited metadata (don't expose sensitive info)
    return {
      slug: event.slug,
      status: event.status,
      expiresAt: event.expiresAt,
      templateName: event.template.name,
      templatePreviewUrl: event.template.previewUrl,
    };
  }

  /**
   * Register a guest and return full invitation details
   * Enforces guest limits per plan
   */
  async registerGuest(
    slug: string,
    guestName: string,
    isTest: boolean = false,
    ip?: string,
    userAgent?: string
  ) {
    // Get event with plan details
    const event = await this.prisma.event.findUnique({
      where: { slug },
      include: {
        plan: true,
      },
    });

    if (!event) {
      throw new NotFoundException('Invitation not found');
    }

    // Check if event is active
    if (event.status !== EventStatus.ACTIVE) {
      throw new BadRequestException('This invitation is not active');
    }

    // Check if expired
    const now = new Date();
    if (event.expiresAt && now > event.expiresAt) {
      await this.prisma.event.update({
        where: { id: event.id },
        data: { status: EventStatus.EXPIRED },
      });

      throw new BadRequestException('This invitation has expired');
    }

    // Check guest limits
    const regularGuestsCount = await this.prisma.guest.count({
      where: {
        eventId: event.id,
        isTest: false,
      },
    });

    const testGuestsCount = await this.prisma.guest.count({
      where: {
        eventId: event.id,
        isTest: true,
      },
    });

    // Enforce limits based on guest type
    if (isTest) {
      if (testGuestsCount >= event.plan.maxTestGuests) {
        throw new BadRequestException(
          `Test guest limit reached (${event.plan.maxTestGuests} maximum)`
        );
      }
    } else {
      if (regularGuestsCount >= event.plan.maxRegularGuests) {
        throw new BadRequestException(
          `Guest limit reached (${event.plan.maxRegularGuests} maximum)`
        );
      }
    }

    // Create guest record
    const guest = await this.prisma.guest.create({
      data: {
        eventId: event.id,
        guestName,
        isTest,
        ip,
        userAgent,
      },
    });

    // Return full invitation details for the animation
    return {
      guest: {
        id: guest.id,
        name: guest.guestName,
      },
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
  }

  /**
   * Check remaining guest slots for an invitation
   */
  async getRemainingSlots(slug: string) {
    const event = await this.prisma.event.findUnique({
      where: { slug },
      include: {
        plan: true,
      },
    });

    if (!event) {
      throw new NotFoundException('Invitation not found');
    }

    const regularGuestsCount = await this.prisma.guest.count({
      where: {
        eventId: event.id,
        isTest: false,
      },
    });

    const testGuestsCount = await this.prisma.guest.count({
      where: {
        eventId: event.id,
        isTest: true,
      },
    });

    return {
      regular: {
        used: regularGuestsCount,
        max: event.plan.maxRegularGuests,
        remaining: event.plan.maxRegularGuests - regularGuestsCount,
      },
      test: {
        used: testGuestsCount,
        max: event.plan.maxTestGuests,
        remaining: event.plan.maxTestGuests - testGuestsCount,
      },
    };
  }
}
