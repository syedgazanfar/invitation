import { Controller, Get, Post, Param, Body, Ip, Headers } from '@nestjs/common';
import { InvitationsService } from './invitations.service';
import { RegisterGuestDto } from './dto/register-guest.dto';

@Controller('invite')
export class InvitationsController {
  constructor(private invitationsService: InvitationsService) {}

  @Get(':slug')
  async getMeta(@Param('slug') slug: string) {
    const meta = await this.invitationsService.getInvitationMeta(slug);
    return {
      success: true,
      data: meta,
    };
  }

  @Post(':slug/register-guest')
  async registerGuest(
    @Param('slug') slug: string,
    @Body() registerGuestDto: RegisterGuestDto,
    @Ip() ip: string,
    @Headers('user-agent') userAgent: string,
  ) {
    const invitation = await this.invitationsService.registerGuest(
      slug,
      registerGuestDto.guestName,
      registerGuestDto.isTest || false,
      ip,
      userAgent,
    );

    return {
      success: true,
      data: invitation,
    };
  }

  @Get(':slug/slots')
  async getSlots(@Param('slug') slug: string) {
    const slots = await this.invitationsService.getRemainingSlots(slug);
    return {
      success: true,
      data: slots,
    };
  }
}
