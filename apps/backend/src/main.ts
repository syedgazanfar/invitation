import { NestFactory } from '@nestjs/core';
import { ValidationPipe } from '@nestjs/common';
import { AppModule } from './app.module';
import { GlobalExceptionFilter } from './common/filters/http-exception.filter';
import helmet from 'helmet';
import * as express from 'express';

async function bootstrap() {
  const app = await NestFactory.create(AppModule);

  // Fix #3: Security headers (XSS, clickjacking, MIME sniffing, HSTS, CSP, etc.)
  app.use(helmet());

  // Fix #4: Limit request body size to prevent DoS via large payloads
  app.use(express.json({ limit: '50kb' }));
  app.use(express.urlencoded({ extended: true, limit: '50kb' }));

  app.enableCors({
    origin: process.env.CORS_ORIGINS?.split(',') || 'http://localhost:9300',
    credentials: true,
  });

  app.useGlobalFilters(new GlobalExceptionFilter());

  app.useGlobalPipes(
    new ValidationPipe({
      whitelist: true,
      forbidNonWhitelisted: true,
      transform: true,
    }),
  );

  app.setGlobalPrefix('api');

  const port = process.env.PORT || 9301;
  await app.listen(port);

  console.log(`
========================================
  Wedding Invitations Platform API
========================================
  Environment: ${process.env.NODE_ENV || 'development'}
  Port: ${port}
  URL: http://localhost:${port}/api
========================================
  `);
}

bootstrap();
