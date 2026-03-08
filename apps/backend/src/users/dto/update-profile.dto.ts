import { IsString, IsOptional, Length } from 'class-validator';
import { Transform } from 'class-transformer';

export class UpdateProfileDto {
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
