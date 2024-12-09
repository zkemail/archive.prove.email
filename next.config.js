/** @type {import('next').NextConfig} */

const cspValue = [
  "default-src 'self'",
  "style-src 'self' 'unsafe-inline'",
  "frame-ancestors 'none'",
  "script-src 'self' 'unsafe-inline' 'unsafe-eval'",
  "img-src 'self' https://authjs.dev/ data:", // https://authjs.dev/ for images during the login flow
  "connect-src 'self' https://*.alchemy.com https://*.prove.email", // https://*.alchemy.com used by Witness https://*.prove.email used by API
];

const nextConfig = {
  async headers() {
    return [
      {
        source: "/(.*)",
        headers: [
          {
            key: "Access-Control-Allow-Origin",
            value: "*",
          },
          {
            key: "Content-Security-Policy",
            value: cspValue.join("; "),
          },
          {
            key: "X-Content-Type-Options",
            value: "nosniff",
          },
          {
            key: "Strict-Transport-Security",
            value: "max-age=63072000; includeSubDomains; preload",
          },
        ],
      },
    ];
  },
};

module.exports = nextConfig;
