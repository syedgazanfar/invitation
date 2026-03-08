import { IsString, IsOptional, IsIn, Length } from 'class-validator';

const ALLOWED_METHODS = ['card', 'bank_transfer'] as const;
const COUNTRY_CODE_REGEX = /^[A-Z]{2}$/;

export class ProcessPaymentDto {
  @IsString()
  @Length(2, 2)
  countryCode: string;

  @IsOptional()
  @IsString()
  @IsIn(ALLOWED_METHODS)
  paymentMethod?: string;
}
