import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  agentRules: false,
  poweredByHeader: false,
  async rewrites() {
    const backend = process.env.PREFLIGHT_API_URL;
    return backend ? [{ source: "/preflight-api/:path*", destination: `${backend.replace(/\/+$/, "")}/:path*` }] : [];
  },
};

export default nextConfig;
