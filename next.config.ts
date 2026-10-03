import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  agentRules: false,
  poweredByHeader: false,
  // Lets the Conductor workspace preview load dev assets; no effect on production builds.
  allowedDevOrigins: ["127.0.0.1", "*.conductor.show"],
  async rewrites() {
    const backend = process.env.PREFLIGHT_API_URL;
    return backend ? [{ source: "/preflight-api/:path*", destination: `${backend.replace(/\/+$/, "")}/:path*` }] : [];
  },
};

export default nextConfig;
