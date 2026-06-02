/** @type {import('next').NextConfig} */
const isStatic = process.env.NEXT_OUTPUT === "export";

const nextConfig = {
  // Capacitor 빌드용 정적 export 모드
  ...(isStatic && {
    output: "export",
    images: { unoptimized: true },
  }),
  // 웹 dev: 백엔드로 프록시 (Capacitor 빌드 때는 NEXT_PUBLIC_API_BASE 환경변수 사용)
  async rewrites() {
    if (isStatic) return [];
    return [
      { source: "/api/:path*", destination: "http://localhost:8000/api/:path*" },
      { source: "/files/:path*", destination: "http://localhost:8000/files/:path*" },
    ];
  },
};
module.exports = nextConfig;
