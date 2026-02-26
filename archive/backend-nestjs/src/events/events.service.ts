import { Injectable, NotFoundException, ForbiddenException, BadRequestException } from '@nestjs/common';
import { PrismaService } from '../prisma/prisma.service';
import { CreateEventDto } from './dto/create-event.dto';
import { UpdateEventDto } from './dto/update-event.dto';
import { EventStatus } from '@prisma/client';
import { customAlphabet } from 'nanoid';

const nanoid = customAlphabet('abcdefghijklmnopqrstuvwxyz0123456789', 12);

@Injectable()
export class EventsService {
  constructor(private prisma: PrismaService) {}

  /**
   * Create a new event in DRAFT status
   */
  async create(userId: string, createEventDto: CreateEventDto) {
    // Verify template exists and belongs to the selected plan
    const template = await this.prisma.template.findUnique({
      where: { id: createEventDto.templateId },
    });

    if (!template) {
      throw new NotFoundException('Template not found');
    }

    if (template.planCode !== createEventDto.planCode) {
      throw new BadRequestException('Template does not belong to the selected plan');
    }

    // Create event
    const event = await this.prisma.event.create({
      data: {
        userId,
        planCode: createEventDto.planCode,
        templateId: createEventDto.templateId,
        brideName: createEventDto.brideName,
        groomName: createEventDto.groomName,
        weddingDate: new Date(createEventDto.weddingDate),
        startTime: createEventDto.startTime,
        timezone: createEventDto.timezone || 'UTC',
        venueName: createEventDto.venueName,
        address: createEventDto.address,
        city: createEventDto.city,
        country: createEventDto.country,
        lat: createEventDto.lat,
        lng: createEventDto.lng,
        message: createEventDto.message,
        status: EventStatus.DRAFT,
      },
      include: {
        plan: true,
        template: true,
      },
    });

    return event;
  }

  /**
   * Update event (only allowed if status is DRAFT)
   */
  async update(eventId: string, userId: string, updateEventDto: UpdateEventDto) {
    const event = await this.prisma.event.findUnique({
      where: { id: eventId },
    });

    if (!event) {
      throw new NotFoundException('Event not found');
    }

    if (event.userId !== userId) {
      throw new ForbiddenException('You do not have permission to update this event');
    }

    if (event.status !== EventStatus.DRAFT) {
      throw new BadRequestException('Cannot update event that is not in DRAFT status');
    }

    // If templateId is being updated, verify it
    if (updateEventDto.templateId) {
      const template = await this.prisma.template.findUnique({
        where: { id: updateEventDto.templateId },
      });

      if (!template || template.planCode !== event.planCode) {
        throw new BadRequestException('Invalid template for this plan');
      }
    }

    const updatedEvent = await this.prisma.event.update({
      where: { id: eventId },
      data: {
        ...updateEventDto,
        weddingDate: updateEventDto.weddingDate ? new Date(updateEventDto.weddingDate) : undefined,
      },
      include: {
        plan: true,
        template: true,
      },
    });

    return updatedEvent;
  }

  /**
   * Activate event after successful payment
   * Generates slug and sets expiry date (5 days from activation)
   */
  async activate(eventId: string, userId: string) {
    const event = await this.prisma.event.findUnique({
      where: { id: eventId },
      include: { payment: true },
    });

    if (!event) {
      throw new NotFoundException('Event not found');
    }

    if (event.userId !== userId) {
      throw new ForbiddenException('You do not have permission to activate this event');
    }

    if (event.status !== EventStatus.DRAFT) {
      throw new BadRequestException('Event is already activated');
    }

    if (!event.payment || event.payment.status !== 'COMPLETED') {
      throw new BadRequestException('Payment must be completed before activating event');
    }

    // Generate unique slug
    const slug = await this.generateUniqueSlug();

    // Set activation and expiry dates
    const now = new Date();
    const expiresAt = new Date(now);
    expiresAt.setDate(expiresAt.getDate() + 5); // 5 days validity

    const activatedEvent = await this.prisma.event.update({
      where: { id: eventId },
      data: {
        status: EventStatus.ACTIVE,
        slug,
        activatedAt: now,
        expiresAt,
      },
      include: {
        plan: true,
        template: true,
        payment: true,
      },
    });

    return activatedEvent;
  }

  /**
   * Get all events for a user
   */
  async findAllByUser(userId: string) {
    const events = await this.prisma.event.findMany({
      where: { userId },
      include: {
        plan: true,
        template: true,
        payment: true,
        _count: {
          select: {
            guests: {
              where: { isTest: false },
            },
          },
        },
      },
      orderBy: {
        createdAt: 'desc',
      },
    });

    // Enhance with computed fields
    return Promise.all(
      events.map(async (event) => {
        const guestStats = await this.getGuestStats(event.id);
        return {
          ...event,
          guestStats,
          inviteUrl: event.slug ? `${process.env.FRONTEND_URL}/invite/${event.slug}` : null,
        };
      })
    );
  }

  /**
   * Get single event by ID
   */
  async findOne(eventId: string, userId: string) {
    const event = await this.prisma.event.findUnique({
      where: { id: eventId },
      include: {
        plan: true,
        template: true,
        payment: true,
      },
    });

    if (!event) {
      throw new NotFoundException('Event not found');
    }

    if (event.userId !== userId) {
      throw new ForbiddenException('You do not have permission to view this event');
    }

    const guestStats = await this.getGuestStats(eventId);

    return {
      ...event,
      guestStats,
      inviteUrl: event.slug ? `${process.env.FRONTEND_URL}/invite/${event.slug}` : null,
    };
  }

  /**
   * Get guest statistics for an event
   */
  async getGuestStats(eventId: string) {
    const event = await this.prisma.event.findUnique({
      where: { id: eventId },
      include: { plan: true },
    });

    if (!event) {
      throw new NotFoundException('Event not found');
    }

    const regularGuestsCount = await this.prisma.guest.count({
      where: {
        eventId,
        isTest: false,
      },
    });

    const testGuestsCount = await this.prisma.guest.count({
      where: {
        eventId,
        isTest: true,
      },
    });

    const totalGuests = regularGuestsCount + testGuestsCount;

    return {
      regularGuests: {
        current: regularGuestsCount,
        max: event.plan.maxRegularGuests,
        remaining: event.plan.maxRegularGuests - regularGuestsCount,
      },
      testGuests: {
        current: testGuestsCount,
        max: event.plan.maxTestGuests,
        remaining: event.plan.maxTestGuests - testGuestsCount,
      },
      total: {
        current: totalGuests,
        max: event.plan.maxRegularGuests + event.plan.maxTestGuests,
        remaining: (event.plan.maxRegularGuests + event.plan.maxTestGuests) - totalGuests,
      },
    };
  }

  /**
   * Get all guests for an event with pagination
   */
  async getGuests(eventId: string, userId: string, page: number = 1, limit: number = 50) {
    const event = await this.prisma.event.findUnique({
      where: { id: eventId },
    });

    if (!event) {
      throw new NotFoundException('Event not found');
    }

    if (event.userId !== userId) {
      throw new ForbiddenException('You do not have permission to view guests');
    }

    const skip = (page - 1) * limit;

    const [guests, total] = await Promise.all([
      this.prisma.guest.findMany({
        where: { eventId },
        orderBy: { createdAt: 'desc' },
        skip,
        take: limit,
      }),
      this.prisma.guest.count({
        where: { eventId },
      }),
    ]);

    return {
      guests,
      pagination: {
        page,
        limit,
        total,
        totalPages: Math.ceil(total / limit),
      },
    };
  }

  /**
   * Export guests as CSV
   */
  async exportGuestsCSV(eventId: string, userId: string): Promise<string> {
    const event = await this.prisma.event.findUnique({
      where: { id: eventId },
    });

    if (!event) {
      throw new NotFoundException('Event not found');
    }

    if (event.userId !== userId) {
      throw new ForbiddenException('You do not have permission to export guests');
    }

    const guests = await this.prisma.guest.findMany({
      where: { eventId },
      orderBy: { createdAt: 'desc' },
    });

    // Generate CSV
    const headers = 'Guest Name,Is Test,IP Address,User Agent,Created At\n';
    const rows = guests.map(guest =>
      `"${guest.guestName}","${guest.isTest}","${guest.ip || ''}","${guest.userAgent || ''}","${guest.createdAt.toISOString()}"`
    ).join('\n');

    return headers + rows;
  }

  /**
   * Generate a unique slug for the invitation URL
   */
  private async generateUniqueSlug(): Promise<string> {
    let attempts = 0;
    const maxAttempts = 10;

    while (attempts < maxAttempts) {
      const slug = nanoid();
      const existing = await this.prisma.event.findUnique({
        where: { slug },
      });

      if (!existing) {
        return slug;
      }

      attempts++;
    }

    throw new Error('Failed to generate unique slug');
  }

  /**
   * Check if event is expired and update status
   */
  async checkAndUpdateExpiredEvents() {
    const now = new Date();

    await this.prisma.event.updateMany({
      where: {
        status: EventStatus.ACTIVE,
        expiresAt: {
          lte: now,
        },
      },
      data: {
        status: EventStatus.EXPIRED,
      },
    });
  }
}
