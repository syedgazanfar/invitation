import {
  Controller,
  Get,
  Post,
  Put,
  Delete,
  Body,
  Param,
  Query,
  UseGuards,
  HttpCode,
  HttpStatus,
  Res,
  ParseIntPipe,
  DefaultValuePipe,
} from '@nestjs/common';
import { Response } from 'express';
import { EventsService } from './events.service';
import { PaymentService } from './payment.service';
import { CreateEventDto } from './dto/create-event.dto';
import { UpdateEventDto } from './dto/update-event.dto';
import { ProcessPaymentDto } from './dto/process-payment.dto';
import { JwtAuthGuard } from '../auth/guards/jwt-auth.guard';
import { CurrentUser, CurrentUserPayload } from '../common/decorators/current-user.decorator';

@Controller('events')
@UseGuards(JwtAuthGuard)
export class EventsController {
  constructor(
    private eventsService: EventsService,
    private paymentService: PaymentService,
  ) {}

  @Post()
  @HttpCode(HttpStatus.CREATED)
  async create(@CurrentUser() user: CurrentUserPayload, @Body() createEventDto: CreateEventDto) {
    const event = await this.eventsService.create(user.userId, createEventDto);
    return { success: true, data: event };
  }

  @Put(':id')
  async update(
    @CurrentUser() user: CurrentUserPayload,
    @Param('id') id: string,
    @Body() updateEventDto: UpdateEventDto,
  ) {
    const event = await this.eventsService.update(id, user.userId, updateEventDto);
    return { success: true, data: event };
  }

  @Post(':id/payment')
  @HttpCode(HttpStatus.OK)
  async processPayment(
    @CurrentUser() user: CurrentUserPayload,
    @Param('id') eventId: string,
    @Body() paymentDto: ProcessPaymentDto,
  ) {
    const result = await this.paymentService.processPayment(
      eventId,
      user.userId,
      paymentDto.countryCode,
      paymentDto.paymentMethod,
    );
    return { success: result.success, data: result };
  }

  @Post(':id/activate')
  @HttpCode(HttpStatus.OK)
  async activate(@CurrentUser() user: CurrentUserPayload, @Param('id') eventId: string) {
    const event = await this.eventsService.activate(eventId, user.userId);
    return { success: true, data: event };
  }

  @Get()
  async findAll(@CurrentUser() user: CurrentUserPayload) {
    const events = await this.eventsService.findAllByUser(user.userId);
    return { success: true, data: events };
  }

  // Static sub-routes must come before the generic /:id/guests route
  @Get(':id/analytics')
  async getAnalytics(@CurrentUser() user: CurrentUserPayload, @Param('id') eventId: string) {
    const analytics = await this.eventsService.getAnalytics(eventId, user.userId);
    return { success: true, data: analytics };
  }

  @Get(':id/guests/stats')
  async getGuestStats(@CurrentUser() user: CurrentUserPayload, @Param('id') eventId: string) {
    await this.eventsService.findOne(eventId, user.userId);
    const stats = await this.eventsService.getGuestStats(eventId);
    return { success: true, data: stats };
  }

  @Get(':id/guests/export')
  async exportGuests(
    @CurrentUser() user: CurrentUserPayload,
    @Param('id') eventId: string,
    @Res() res: Response,
  ) {
    const csv = await this.eventsService.exportGuestsCSV(eventId, user.userId);
    res.header('Content-Type', 'text/csv');
    res.header('Content-Disposition', `attachment; filename="guests-${eventId}.csv"`);
    res.send(csv);
  }

  @Get(':id/guests')
  async getGuests(
    @CurrentUser() user: CurrentUserPayload,
    @Param('id') eventId: string,
    @Query('page', new DefaultValuePipe(1), ParseIntPipe) page: number,
    @Query('limit', new DefaultValuePipe(50), ParseIntPipe) limit: number,
  ) {
    const result = await this.eventsService.getGuests(eventId, user.userId, page, limit);
    return { success: true, data: result };
  }

  @Get(':id')
  async findOne(@CurrentUser() user: CurrentUserPayload, @Param('id') id: string) {
    const event = await this.eventsService.findOne(id, user.userId);
    return { success: true, data: event };
  }

  @Delete(':id')
  @HttpCode(HttpStatus.OK)
  async delete(@CurrentUser() user: CurrentUserPayload, @Param('id') id: string) {
    const result = await this.eventsService.delete(id, user.userId);
    return { success: true, data: result };
  }
}
