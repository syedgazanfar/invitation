const path = require('path');

/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  // .next is a junction pointing to C:\Temp\wedding-next (outside OneDrive sync)
  images: {
    domains: ['placeholder.com'],
  },
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:9301/api',
  },
  webpack(config) {
    // Exclude legacy MUI pages/components from compilation — only src/app is active
    const legacyDirs = ['pages', 'components', 'hooks', 'services', 'config', 'types', 'utils'];
    const legacyFiles = ['App.tsx', 'index.tsx', 'theme.ts', 'setupTests.ts'];
    const srcBase = path.resolve(__dirname, 'src');

    config.module.rules.push({
      test: (filePath) => {
        if (!filePath.startsWith(srcBase)) return false;
        const rel = filePath.slice(srcBase.length + 1).replace(/\\/g, '/');
        return (
          legacyDirs.some((d) => rel.startsWith(d + '/')) ||
          legacyFiles.includes(rel)
        );
      },
      use: 'null-loader',
    });

    return config;
  },
};

module.exports = nextConfig;
