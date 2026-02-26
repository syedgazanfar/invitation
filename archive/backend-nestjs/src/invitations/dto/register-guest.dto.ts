import { IsString, IsBoolean, IsOptional, MinLength, MaxLength } from 'class-validator';

export class RegisterGuestDto {
  @IsString()
  @MinLength(2)
  @MaxLength(100)
  guestName: string;

  @IsOptional()
  @IsBoolean()
  isTest?: boolean;
}
