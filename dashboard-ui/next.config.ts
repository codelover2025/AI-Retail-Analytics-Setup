import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  reactStrictMode: true,
  output: "standalone",
  /** Proxy API in dev — avoids browser CORS / connection issues */
  async rewrites() {
    const api = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";
    return [
      {
        source: "/backend-api/:path*",
        destination: `${api}/:path*`,
      },
    ];
  },
};

export default nextConfig;

