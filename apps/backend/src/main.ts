import { NestFactory } from '@nestjs/core';
import { ValidationPipe } from '@nestjs/common';
import { AppModule } from './app.module';

async function bootstrap() {
  const app = await NestFactory.create(AppModule);

  // Enable CORS
  app.enableCors({
    origin: process.env.CORS_ORIGINS?.split(',') || 'http://localhost:9300',
    credentials: true,
  });

  // Global validation pipe
  app.useGlobalPipes(
    new ValidationPipe({
      whitelist: true,
      forbidNonWhitelisted: true,
      transform: true,
    })
  );

  // Global prefix
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
