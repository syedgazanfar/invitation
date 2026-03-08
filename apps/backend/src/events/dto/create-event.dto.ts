import { IsString, IsDateString, IsOptional, IsEnum, IsNumber, Min, Max } from 'class-validator';
import { PlanCode } from '@prisma/client';

export class CreateEventDto {
  @IsEnum(PlanCode)
  planCode: PlanCode;

  @IsString()
  templateId: string;

  @IsString()
  brideName: string;

  @IsString()
  groomName: string;

  @IsDateString()
  weddingDate: string;

  @IsString()
  startTime: string;

  @IsOptional()
  @IsString()
  timezone?: string;

  @IsString()
  venueName: string;

  @IsString()
  address: string;

  @IsString()
  city: string;

  @IsString()
  country: string;

  @IsOptional()
  @IsNumber()
  @Min(-90)
  @Max(90)
  lat?: number;

  @IsOptional()
  @IsNumber()
  @Min(-180)
  @Max(180)
  lng?: number;

  @IsOptional()
  @IsString()
  message?: string;
}
