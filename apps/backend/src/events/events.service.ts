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

    // Sanitize values to prevent CSV formula injection (=, +, -, @ as first char)
    const sanitizeCsv = (val: string) =>
      /^[=+\-@\t\r]/.test(val) ? `\t${val}` : val;

    const headers = 'Guest Name,Is Test,IP Address,User Agent,Created At\n';
    const rows = guests
      .map((g) => [
        sanitizeCsv(g.guestName),
        g.isTest,
        sanitizeCsv(g.ip ?? ''),
        sanitizeCsv(g.userAgent ?? ''),
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

  async getAnalytics(eventId: string, userId: string) {
    const event = await this.prisma.event.findUnique({ where: { id: eventId } });
    if (!event) throw new NotFoundException('Event not found');
    if (event.userId !== userId) throw new ForbiddenException('You do not have permission to view analytics for this event');

    const guests = await this.prisma.guest.findMany({
      where: { eventId },
      orderBy: { createdAt: 'asc' },
      select: { isTest: true, ip: true, userAgent: true, createdAt: true },
    });

    const total = guests.length;
    const regularCount = guests.filter((g) => !g.isTest).length;
    const testCount = guests.filter((g) => g.isTest).length;
    const uniqueIPs = new Set(guests.map((g) => g.ip).filter(Boolean)).size;
    const firstRegistration = guests[0]?.createdAt ?? null;
    const lastRegistration = guests[guests.length - 1]?.createdAt ?? null;

    // --- Timeline: one bucket per calendar day from activation (or first guest) ---
    const timelineMap = new Map<string, { regular: number; test: number }>();
    for (const g of guests) {
      const key = g.createdAt.toISOString().split('T')[0];
      const entry = timelineMap.get(key) ?? { regular: 0, test: 0 };
      g.isTest ? entry.test++ : entry.regular++;
      timelineMap.set(key, entry);
    }

    const timelineStart = event.activatedAt ?? firstRegistration ?? new Date();
    const timelineEnd = event.expiresAt && event.expiresAt < new Date() ? event.expiresAt : new Date();
    const timeline: { date: string; regular: number; test: number }[] = [];
    for (const d = new Date(timelineStart); d <= timelineEnd; d.setDate(d.getDate() + 1)) {
      const key = d.toISOString().split('T')[0];
      const entry = timelineMap.get(key) ?? { regular: 0, test: 0 };
      timeline.push({ date: key, regular: entry.regular, test: entry.test });
    }

    // --- Hourly distribution (0–23, UTC) ---
    const hourly = new Array(24).fill(0);
    for (const g of guests) hourly[g.createdAt.getUTCHours()]++;
    const hourlyDistribution = hourly.map((count, hour) => ({ hour, count }));

    // --- Summary extras ---
    const activeDays = timelineMap.size || 1;
    const avgPerDay = Math.round((total / activeDays) * 10) / 10;

    let peakDay: { date: string; count: number } | null = null;
    for (const [date, e] of timelineMap.entries()) {
      const c = e.regular + e.test;
      if (!peakDay || c > peakDay.count) peakDay = { date, count: c };
    }

    const maxHourVal = Math.max(...hourly);
    const peakHour = total > 0 ? hourly.indexOf(maxHourVal) : null;

    // --- UA breakdowns ---
    const deviceMap = new Map<string, number>();
    const browserMap = new Map<string, number>();
    const osMap = new Map<string, number>();

    for (const g of guests) {
      const ua = g.userAgent ?? '';
      const device = this.parseDevice(ua);
      const browser = this.parseBrowser(ua);
      const os = this.parseOS(ua);
      deviceMap.set(device, (deviceMap.get(device) ?? 0) + 1);
      browserMap.set(browser, (browserMap.get(browser) ?? 0) + 1);
      osMap.set(os, (osMap.get(os) ?? 0) + 1);
    }

    const toArray = (map: Map<string, number>) =>
      Array.from(map.entries())
        .map(([name, count]) => ({
          name,
          count,
          pct: total > 0 ? Math.round((count / total) * 100) : 0,
        }))
        .sort((a, b) => b.count - a.count);

    return {
      summary: { total, regularCount, testCount, uniqueIPs, firstRegistration, lastRegistration, avgPerDay, peakDay, peakHour },
      timeline,
      hourlyDistribution,
      devices: toArray(deviceMap),
      browsers: toArray(browserMap),
      os: toArray(osMap),
    };
  }

  private parseDevice(ua: string): string {
    if (/tablet|ipad/i.test(ua)) return 'Tablet';
    if (/mobile|android|iphone|ipod/i.test(ua)) return 'Mobile';
    return 'Desktop';
  }

  private parseBrowser(ua: string): string {
    if (/edg\//i.test(ua)) return 'Edge';
    if (/opr\/|opera/i.test(ua)) return 'Opera';
    if (/chrome\/[0-9]/i.test(ua)) return 'Chrome';
    if (/firefox\/[0-9]/i.test(ua)) return 'Firefox';
    if (/safari\/[0-9]/i.test(ua) && !/chrome/i.test(ua)) return 'Safari';
    return 'Other';
  }

  private parseOS(ua: string): string {
    if (/windows/i.test(ua)) return 'Windows';
    if (/android/i.test(ua)) return 'Android';
    if (/iphone|ipad|ipod/i.test(ua)) return 'iOS';
    if (/macintosh|mac os x/i.test(ua)) return 'macOS';
    if (/linux/i.test(ua)) return 'Linux';
    return 'Other';
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
