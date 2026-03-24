/** @type {import('next').NextConfig} */
const nextConfig = {
  experimental: {
    externalDir: true
  },
  transpilePackages: ["@legalos/contracts", "@legalos/ui"]
};

export default nextConfig;
