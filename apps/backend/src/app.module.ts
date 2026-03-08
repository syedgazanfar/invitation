import { Module } from '@nestjs/common';
import { ConfigModule } from '@nestjs/config';
import { ScheduleModule } from '@nestjs/schedule';
import { ThrottlerModule, ThrottlerGuard } from '@nestjs/throttler';
import { APP_GUARD } from '@nestjs/core';
import { PrismaModule } from './prisma/prisma.module';
import { AuthModule } from './auth/auth.module';
import { UsersModule } from './users/users.module';
import { PlansModule } from './plans/plans.module';
import { TemplatesModule } from './templates/templates.module';
import { EventsModule } from './events/events.module';
import { InvitationsModule } from './invitations/invitations.module';
import { AdminModule } from './admin/admin.module';

@Module({
  imports: [
    ConfigModule.forRoot({ isGlobal: true }),
    ScheduleModule.forRoot(),

    // Global rate limiting:
    //  - default: 60 requests / 60 seconds per IP
    //  - auth tier overridden per-controller with @Throttle()
    ThrottlerModule.forRoot([
      {
        name: 'default',
        ttl: 60_000,   // 1 minute window (ms)
        limit: 60,
      },
      {
        name: 'auth',
        ttl: 60_000,
        limit: 10,     // tighter limit applied explicitly on auth routes
      },
      {
        name: 'public',
        ttl: 60_000,
        limit: 30,     // invite / guest-registration endpoints
      },
    ]),

    PrismaModule,
    AuthModule,
    UsersModule,
    PlansModule,
    TemplatesModule,
    EventsModule,
    InvitationsModule,
    AdminModule,
  ],
  providers: [
    // Applies ThrottlerGuard globally; individual controllers can override
    { provide: APP_GUARD, useClass: ThrottlerGuard },
  ],
})
export class AppModule {}
