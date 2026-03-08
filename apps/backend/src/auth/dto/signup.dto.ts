import { IsEmail, IsString, MinLength, MaxLength, IsOptional, IsNotEmpty, Length } from 'class-validator';
import { Transform } from 'class-transformer';

export class SignupDto {
  @IsEmail()
  @IsNotEmpty()
  @MaxLength(254)
  @Transform(({ value }) => value?.toLowerCase().trim())
  email: string;

  @IsString()
  @MinLength(8)
  @MaxLength(128)
  password: string;

  @IsOptional()
  @IsString()
  @Length(2, 2)
  @Transform(({ value }) => value?.toUpperCase())
  preferredCountry?: string;

  @IsOptional()
  @IsString()
  @Length(3, 3)
  @Transform(({ value }) => value?.toUpperCase())
  preferredCurrency?: string;
}
