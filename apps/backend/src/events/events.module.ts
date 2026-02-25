import { Module } from '@nestjs/common';
import { EventsController } from './events.controller';
import { EventsService } from './events.service';
import { PaymentService } from './payment.service';
import { PricingModule } from '../pricing/pricing.module';

@Module({
  imports: [PricingModule],
  controllers: [EventsController],
  providers: [EventsService, PaymentService],
  exports: [EventsService],
})
export class EventsModule {}
