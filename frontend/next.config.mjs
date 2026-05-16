/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  images: {
    remotePatterns: [
      { protocol: "https", hostname: "qr.sepay.vn" },
    ],
  },
};

export default nextConfig;
