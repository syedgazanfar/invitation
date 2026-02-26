import { IsString, IsBoolean, IsOptional } from 'class-validator';

export class ProcessPaymentDto {
  @IsString()
  countryCode: string;

  @IsOptional()
  @IsString()
  paymentMethod?: string;

  @IsOptional()
  @IsBoolean()
  simulateFailure?: boolean;
}
