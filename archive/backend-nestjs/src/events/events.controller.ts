import {
  Controller,
  Get,
  Post,
  Put,
  Body,
  Param,
  Query,
  UseGuards,
  Request,
  HttpCode,
  HttpStatus,
  Res,
} from '@nestjs/common';
import { Response } from 'express';
import { EventsService } from './events.service';
import { PaymentService } from './payment.service';
import { CreateEventDto } from './dto/create-event.dto';
import { UpdateEventDto } from './dto/update-event.dto';
import { ProcessPaymentDto } from './dto/process-payment.dto';
import { JwtAuthGuard } from '../auth/guards/jwt-auth.guard';

@Controller('events')
@UseGuards(JwtAuthGuard)
export class EventsController {
  constructor(
    private eventsService: EventsService,
    private paymentService: PaymentService,
  ) {}

  @Post()
  async create(@Request() req, @Body() createEventDto: CreateEventDto) {
    const event = await this.eventsService.create(req.user.userId, createEventDto);
    return {
      success: true,
      data: event,
    };
  }

  @Put(':id')
  async update(
    @Request() req,
    @Param('id') id: string,
    @Body() updateEventDto: UpdateEventDto,
  ) {
    const event = await this.eventsService.update(id, req.user.userId, updateEventDto);
    return {
      success: true,
      data: event,
    };
  }

  @Post(':id/payment')
  @HttpCode(HttpStatus.OK)
  async processPayment(
    @Request() req,
    @Param('id') eventId: string,
    @Body() paymentDto: ProcessPaymentDto,
  ) {
    const result = await this.paymentService.processPayment(
      eventId,
      paymentDto.countryCode,
      paymentDto.paymentMethod,
      paymentDto.simulateFailure,
    );

    return {
      success: result.success,
      data: result,
    };
  }

  @Post(':id/activate')
  @HttpCode(HttpStatus.OK)
  async activate(@Request() req, @Param('id') eventId: string) {
    const event = await this.eventsService.activate(eventId, req.user.userId);
    return {
      success: true,
      data: event,
    };
  }

  @Get()
  async findAll(@Request() req) {
    const events = await this.eventsService.findAllByUser(req.user.userId);
    return {
      success: true,
      data: events,
    };
  }

  @Get(':id')
  async findOne(@Request() req, @Param('id') id: string) {
    const event = await this.eventsService.findOne(id, req.user.userId);
    return {
      success: true,
      data: event,
    };
  }

  @Get(':id/guests')
  async getGuests(
    @Request() req,
    @Param('id') eventId: string,
    @Query('page') page: string = '1',
    @Query('limit') limit: string = '50',
  ) {
    const result = await this.eventsService.getGuests(
      eventId,
      req.user.userId,
      parseInt(page),
      parseInt(limit),
    );

    return {
      success: true,
      data: result,
    };
  }

  @Get(':id/guests/stats')
  async getGuestStats(@Request() req, @Param('id') eventId: string) {
    // Verify ownership first
    await this.eventsService.findOne(eventId, req.user.userId);

    const stats = await this.eventsService.getGuestStats(eventId);
    return {
      success: true,
      data: stats,
    };
  }

  @Get(':id/guests/export')
  async exportGuests(@Request() req, @Param('id') eventId: string, @Res() res: Response) {
    const csv = await this.eventsService.exportGuestsCSV(eventId, req.user.userId);

    res.header('Content-Type', 'text/csv');
    res.header('Content-Disposition', `attachment; filename="event-${eventId}-guests.csv"`);
    res.send(csv);
  }
}
