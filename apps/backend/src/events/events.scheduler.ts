import { Injectable } from '@nestjs/common';
import { Cron, CronExpression } from '@nestjs/schedule';
import { EventsService } from './events.service';

@Injectable()
export class EventsScheduler {
  constructor(private eventsService: EventsService) {}

  // Fix #7: Run expiry check every 5 minutes instead of on every dashboard GET
  @Cron(CronExpression.EVERY_5_MINUTES)
  async expireStaleEvents() {
    await this.eventsService.checkAndUpdateExpiredEvents();
  }
}
