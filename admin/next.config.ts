import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  allowedDevOrigins: [
    '75c5d1c6-ab46-486d-9c80-fa4c33ea849b-00-118tbzfrr5rmh.pike.replit.dev',
    '75b0aa88-92c4-4424-ab49-9d1664b48129-00-1g9yoro9o3zfq.sisko.replit.dev',
    'localhost',
    '127.0.0.1',
  ],
  async rewrites() {
    return [
      {
        source: '/telegram/webhook',
        destination: 'http://localhost:8080/telegram/webhook',
      },
      {
        source: '/oxapay/webhook',
        destination: 'http://localhost:8080/oxapay/webhook',
      },
    ];
  },
  async headers() {
    return [
      {
        source: '/api/:path*',
        headers: [
          {
            key: 'Access-Control-Allow-Origin',
            value: '*',
          },
          {
            key: 'Access-Control-Allow-Methods',
            value: 'GET, POST, PUT, DELETE, OPTIONS',
          },
          {
            key: 'Access-Control-Allow-Headers',
            value: 'Content-Type, Authorization',
          },
          {
            key: 'Access-Control-Allow-Credentials',
            value: 'true',
          },
        ],
      },
      {
        source: '/(.*)',
        headers: [
          {
            key: 'Cache-Control',
            value: 'no-store, must-revalidate',
          },
        ],
      },
    ];
  },
};

export default nextConfig;
