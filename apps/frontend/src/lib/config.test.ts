import { describe, expect, it } from 'vitest';
import { createRequire } from 'module';

const nodeRequire = createRequire(import.meta.url);

describe('next.config.js', () => {
  it('defaults NEXT_PUBLIC_API_URL to the Django API, not the retired NestJS one', () => {
    const saved = process.env.NEXT_PUBLIC_API_URL;
    delete process.env.NEXT_PUBLIC_API_URL;
    try {
      const configPath = nodeRequire.resolve('../../next.config.js');
      delete nodeRequire.cache[configPath];
      const config = nodeRequire(configPath);
      expect(config.env.NEXT_PUBLIC_API_URL).toBe('http://localhost:8000/api/v1');
    } finally {
      if (saved !== undefined) process.env.NEXT_PUBLIC_API_URL = saved;
    }
  });
});
