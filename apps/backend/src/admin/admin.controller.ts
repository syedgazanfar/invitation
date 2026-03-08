import { Controller, Get, Patch, Param, Query, UseGuards, DefaultValuePipe, ParseIntPipe } from '@nestjs/common';
import { AdminService } from './admin.service';
import { AdminGuard } from './admin.guard';
import { JwtAuthGuard } from '../auth/guards/jwt-auth.guard';
import { CurrentUser, CurrentUserPayload } from '../common/decorators/current-user.decorator';

@Controller('admin')
@UseGuards(JwtAuthGuard, AdminGuard)
export class AdminController {
  constructor(private adminService: AdminService) {}

  @Get('stats')
  async getStats() {
    const data = await this.adminService.getStats();
    return { success: true, data };
  }

  @Get('users')
  async getUsers(@Query('search') search?: string) {
    const data = await this.adminService.getAllUsers(search);
    return { success: true, data };
  }

  @Get('events')
  async getEvents(
    @Query('status') status?: string,
    @Query('page', new DefaultValuePipe(1), ParseIntPipe) page: number = 1,
    @Query('limit', new DefaultValuePipe(20), ParseIntPipe) limit: number = 20,
  ) {
    const data = await this.adminService.getAllEvents(status, page, limit);
    return { success: true, data };
  }

  @Patch('users/:id/toggle-admin')
  async toggleAdmin(
    @Param('id') targetId: string,
    @CurrentUser() user: CurrentUserPayload,
  ) {
    const data = await this.adminService.toggleAdminStatus(targetId, user.userId);
    return { success: !!data, data };
  }
}
