import { Injectable } from '@nestjs/common';
import { PrismaService } from '../prisma/prisma.service';
import { EventStatus } from '@prisma/client';

@Injectable()
export class AdminService {
  constructor(private prisma: PrismaService) {}

  async getStats() {
    const now = new Date();
    const startOfToday = new Date(now.getFullYear(), now.getMonth(), now.getDate());
    const startOfMonth = new Date(now.getFullYear(), now.getMonth(), 1);

    const [
      totalUsers,
      newUsersToday,
      newUsersThisMonth,
      totalEvents,
      draftEvents,
      activeEvents,
      expiredEvents,
      totalGuests,
      guestsToday,
      totalPayments,
      completedPayments,
    ] = await Promise.all([
      this.prisma.user.count(),
      this.prisma.user.count({ where: { createdAt: { gte: startOfToday } } }),
      this.prisma.user.count({ where: { createdAt: { gte: startOfMonth } } }),
      this.prisma.event.count(),
      this.prisma.event.count({ where: { status: EventStatus.DRAFT } }),
      this.prisma.event.count({ where: { status: EventStatus.ACTIVE } }),
      this.prisma.event.count({ where: { status: EventStatus.EXPIRED } }),
      this.prisma.guest.count(),
      this.prisma.guest.count({ where: { createdAt: { gte: startOfToday } } }),
      this.prisma.payment.count(),
      this.prisma.payment.aggregate({
        where: { status: 'COMPLETED' },
        _sum: { amount: true },
        _count: true,
      }),
    ]);

    return {
      users: {
        total: totalUsers,
        newToday: newUsersToday,
        newThisMonth: newUsersThisMonth,
      },
      events: {
        total: totalEvents,
        draft: draftEvents,
        active: activeEvents,
        expired: expiredEvents,
      },
      guests: {
        total: totalGuests,
        today: guestsToday,
      },
      revenue: {
        totalCompleted: completedPayments._count,
        totalAmount: Number(completedPayments._sum.amount ?? 0),
        totalPayments,
      },
    };
  }

  async getAllUsers(search?: string) {
    const where = search
      ? { email: { contains: search, mode: 'insensitive' as const } }
      : {};

    const users = await this.prisma.user.findMany({
      where,
      select: {
        id: true,
        email: true,
        preferredCountry: true,
        preferredCurrency: true,
        isAdmin: true,
        createdAt: true,
        _count: { select: { events: true } },
      },
      orderBy: { createdAt: 'desc' },
    });

    return users.map((u) => ({
      id: u.id,
      email: u.email,
      preferredCountry: u.preferredCountry,
      preferredCurrency: u.preferredCurrency,
      isAdmin: u.isAdmin,
      createdAt: u.createdAt,
      eventCount: u._count.events,
    }));
  }

  async getAllEvents(status?: string, page = 1, limit = 20) {
    const where = status ? { status: status as EventStatus } : {};
    const skip = (page - 1) * limit;

    const [events, total] = await Promise.all([
      this.prisma.event.findMany({
        where,
        include: {
          user: { select: { id: true, email: true } },
          plan: { select: { code: true, name: true } },
          payment: { select: { status: true, amount: true, currency: true } },
          _count: { select: { guests: true } },
        },
        orderBy: { createdAt: 'desc' },
        skip,
        take: limit,
      }),
      this.prisma.event.count({ where }),
    ]);

    return {
      events: events.map((e) => ({
        id: e.id,
        brideName: e.brideName,
        groomName: e.groomName,
        weddingDate: e.weddingDate,
        status: e.status,
        planCode: e.planCode,
        planName: e.plan.name,
        slug: e.slug,
        createdAt: e.createdAt,
        expiresAt: e.expiresAt,
        user: e.user,
        payment: e.payment,
        guestCount: e._count.guests,
      })),
      pagination: { page, limit, total, totalPages: Math.ceil(total / limit) },
    };
  }

  async toggleAdminStatus(targetUserId: string, requestingUserId: string) {
    const user = await this.prisma.user.findUnique({ where: { id: targetUserId } });
    if (!user) return null;
    // Prevent self-demotion
    if (targetUserId === requestingUserId) return null;

    return this.prisma.user.update({
      where: { id: targetUserId },
      data: { isAdmin: !user.isAdmin },
      select: { id: true, email: true, isAdmin: true },
    });
  }
}
