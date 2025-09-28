/** @type {import('next').NextConfig} */
const nextConfig = {
  async rewrites() {
    const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api';
    console.log('🔧 BUILD TIME - API URL in rewrites:', apiUrl);
    console.log('🔧 BUILD TIME - Environment check:', {
      API_URL: process.env.NEXT_PUBLIC_API_URL,
      SUPABASE_URL: process.env.NEXT_PUBLIC_SUPABASE_URL,
      NODE_ENV: process.env.NODE_ENV,
      allEnvKeys: Object.keys(process.env).filter(key => key.startsWith('NEXT_PUBLIC_'))
    });
    
    return [
      {
        source: '/api/:path*',
        destination: `${apiUrl}/:path*`,
      },
    ];
  },
  
  // Environment variables (this ensures they're available to the app)
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL,
    NEXT_PUBLIC_SUPABASE_URL: process.env.NEXT_PUBLIC_SUPABASE_URL,
    NEXT_PUBLIC_SUPABASE_ANON_KEY: process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY,
  },
  
  // Add domains for images if you're using next/image with external URLs
  images: {
    domains: [
      'localhost',
      '127.0.0.1',
      'chat-pdf-rag-app.onrender.com',
    ],
  },
};

module.exports = nextConfig;