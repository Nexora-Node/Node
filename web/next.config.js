/** @type {import('next').NextConfig} */
const nextConfig = {
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || "https://node-production-712b.up.railway.app",
  },
  experimental: {
    serverActions: { allowedOrigins: ["*"] },
  },
};
module.exports = nextConfig;
