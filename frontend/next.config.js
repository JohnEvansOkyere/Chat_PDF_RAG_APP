/** @type {import('next').NextConfig} */
const nextConfig = {
  async rewrites() {
    const apiUrl =
      process.env.BACKEND_API_URL ||
      process.env.NEXT_PUBLIC_API_URL ||
      'http://localhost:8000/api';
    
    return [
      {
        source: '/api/:path*',
        destination: `${apiUrl}/:path*`,
      },
    ];
  },

  images: {
    domains: [
      'localhost',
      '127.0.0.1',
      'chat-pdf-rag-app.onrender.com',
    ],
  },
};

module.exports = nextConfig;
