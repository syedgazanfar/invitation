import {
  Injectable,
  NotFoundException,
  ForbiddenException,
  BadRequestException,
} from '@nestjs/common';
import { PrismaService } from '../prisma/prisma.service';
import { CreateEventDto } from './dto/create-event.dto';
import { UpdateEventDto } from './dto/update-event.dto';
import { EventStatus } from '@prisma/client';
import { customAlphabet } from 'nanoid';

const nanoid = customAlphabet('abcdefghijklmnopqrstuvwxyz0123456789', 12);

@Injectable()
export class EventsService {
  constructor(private prisma: PrismaService) {}

  async create(userId: string, createEventDto: CreateEventDto) {
    const template = await this.prisma.template.findUnique({
      where: { id: createEventDto.templateId },
    });

    if (!template) {
      throw new NotFoundException('Template not found');
    }

    if (template.planCode !== createEventDto.planCode) {
      throw new BadRequestException('Template does not belong to the selected plan');
    }

    return this.prisma.event.create({
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
      include: { plan: true, template: true },
    });
  }

  async update(eventId: string, userId: string, updateEventDto: UpdateEventDto) {
    const event = await this.prisma.event.findUnique({ where: { id: eventId } });

    if (!event) throw new NotFoundException('Event not found');
    if (event.userId !== userId) throw new ForbiddenException('You do not have permission to update this event');
    if (event.status !== EventStatus.DRAFT) throw new BadRequestException('Only DRAFT events can be updated');

    if (updateEventDto.templateId) {
      const template = await this.prisma.template.findUnique({
        where: { id: updateEventDto.templateId },
      });
      if (!template || template.planCode !== event.planCode) {
        throw new BadRequestException('Invalid template for this plan');
      }
    }

    return this.prisma.event.update({
      where: { id: eventId },
      data: {
        ...updateEventDto,
        weddingDate: updateEventDto.weddingDate ? new Date(updateEventDto.weddingDate) : undefined,
      },
      include: { plan: true, template: true },
    });
  }

  async activate(eventId: string, userId: string) {
    const event = await this.prisma.event.findUnique({
      where: { id: eventId },
      include: { payment: true },
    });

    if (!event) throw new NotFoundException('Event not found');
    if (event.userId !== userId) throw new ForbiddenException('You do not have permission to activate this event');
    if (event.status !== EventStatus.DRAFT) throw new BadRequestException('Only DRAFT events can be activated');

    if (!event.payment || event.payment.status !== 'COMPLETED') {
      throw new BadRequestException('Payment must be completed before activating the event');
    }

    const slug = await this.generateUniqueSlug();
    const now = new Date();
    const expiresAt = new Date(now);
    expiresAt.setDate(expiresAt.getDate() + 5);

    return this.prisma.event.update({
      where: { id: eventId },
      data: { status: EventStatus.ACTIVE, slug, activatedAt: now, expiresAt },
      include: { plan: true, template: true, payment: true },
    });
  }

  async findAllByUser(userId: string) {
    // Auto-expire events that have passed their expiry date before listing
    await this.checkAndUpdateExpiredEvents();
    const events = await this.prisma.event.findMany({
      where: { userId },
      include: { plan: true, template: true, payment: true },
      orderBy: { createdAt: 'desc' },
    });

    if (events.length === 0) return [];

    // Single aggregation query replaces N+1 per-event getGuestStats calls
    const eventIds = events.map((e) => e.id);
    const guestCounts = await this.prisma.guest.groupBy({
      by: ['eventId', 'isTest'],
      where: { eventId: { in: eventIds } },
      _count: { id: true },
    });

    const countMap = new Map<string, { regular: number; test: number }>();
    for (const gc of guestCounts) {
      const entry = countMap.get(gc.eventId) ?? { regular: 0, test: 0 };
      if (gc.isTest) { entry.test = gc._count.id; } else { entry.regular = gc._count.id; }
      countMap.set(gc.eventId, entry);
    }

    const frontendUrl = process.env.FRONTEND_URL;
    return events.map((event) => {
      const counts = countMap.get(event.id) ?? { regular: 0, test: 0 };
      return {
        ...event,
        guestStats: this.buildGuestStats(counts.regular, counts.test, event.plan),
        inviteUrl: event.slug ? `${frontendUrl}/invite/${event.slug}` : null,
      };
    });
  }

  async findOne(eventId: string, userId: string) {
    const event = await this.prisma.event.findUnique({
      where: { id: eventId },
      include: { plan: true, template: true, payment: true },
    });

    if (!event) throw new NotFoundException('Event not found');
    if (event.userId !== userId) throw new ForbiddenException('You do not have permission to view this event');

    const guestStats = await this.getGuestStats(eventId);
    return {
      ...event,
      guestStats,
      inviteUrl: event.slug ? `${process.env.FRONTEND_URL}/invite/${event.slug}` : null,
    };
  }

  async getGuestStats(eventId: string) {
    const event = await this.prisma.event.findUnique({
      where: { id: eventId },
      include: { plan: true },
    });

    if (!event) throw new NotFoundException('Event not found');

    const [regularCount, testCount] = await Promise.all([
      this.prisma.guest.count({ where: { eventId, isTest: false } }),
      this.prisma.guest.count({ where: { eventId, isTest: true } }),
    ]);

    return this.buildGuestStats(regularCount, testCount, event.plan);
  }

  async getGuests(eventId: string, userId: string, page: number = 1, limit: number = 50) {
    const event = await this.prisma.event.findUnique({ where: { id: eventId } });

    if (!event) throw new NotFoundException('Event not found');
    if (event.userId !== userId) throw new ForbiddenException('You do not have permission to view guests');

    const skip = (page - 1) * limit;
    const [guests, total] = await Promise.all([
      this.prisma.guest.findMany({
        where: { eventId },
        orderBy: { createdAt: 'desc' },
        skip,
        take: limit,
      }),
      this.prisma.guest.count({ where: { eventId } }),
    ]);

    return {
      guests,
      pagination: { page, limit, total, totalPages: Math.ceil(total / limit) },
    };
  }

  async exportGuestsCSV(eventId: string, userId: string): Promise<string> {
    const event = await this.prisma.event.findUnique({ where: { id: eventId } });

    if (!event) throw new NotFoundException('Event not found');
    if (event.userId !== userId) throw new ForbiddenException('You do not have permission to export guests');

    const guests = await this.prisma.guest.findMany({
      where: { eventId },
      orderBy: { createdAt: 'desc' },
    });

    const headers = 'Guest Name,Is Test,IP Address,User Agent,Created At\n';
    const rows = guests
      .map((g) => [
        g.guestName,
        g.isTest,
        g.ip ?? '',
        g.userAgent ?? '',
        g.createdAt.toISOString(),
      ].map((v) => `"${String(v).replace(/"/g, '""')}"`).join(','))
      .join('\n');

    return headers + rows;
  }

  async checkAndUpdateExpiredEvents() {
    await this.prisma.event.updateMany({
      where: { status: EventStatus.ACTIVE, expiresAt: { lte: new Date() } },
      data: { status: EventStatus.EXPIRED },
    });
  }

  async delete(eventId: string, userId: string) {
    const event = await this.prisma.event.findUnique({ where: { id: eventId } });

    if (!event) throw new NotFoundException('Event not found');
    if (event.userId !== userId) throw new ForbiddenException('You do not have permission to delete this event');
    if (event.status !== EventStatus.DRAFT) throw new BadRequestException('Only DRAFT events can be deleted');

    await this.prisma.event.delete({ where: { id: eventId } });
    return { deleted: true };
  }

  private buildGuestStats(
    regularCount: number,
    testCount: number,
    plan: { maxRegularGuests: number; maxTestGuests: number },
  ) {
    return {
      regularGuests: {
        current: regularCount,
        max: plan.maxRegularGuests,
        remaining: plan.maxRegularGuests - regularCount,
      },
      testGuests: {
        current: testCount,
        max: plan.maxTestGuests,
        remaining: plan.maxTestGuests - testCount,
      },
      total: {
        current: regularCount + testCount,
        max: plan.maxRegularGuests + plan.maxTestGuests,
        remaining: plan.maxRegularGuests + plan.maxTestGuests - regularCount - testCount,
      },
    };
  }

  private async generateUniqueSlug(): Promise<string> {
    for (let attempt = 0; attempt < 10; attempt++) {
      const slug = nanoid();
      const existing = await this.prisma.event.findUnique({ where: { slug } });
      if (!existing) return slug;
    }
    throw new Error('Failed to generate unique slug after 10 attempts');
  }
}
