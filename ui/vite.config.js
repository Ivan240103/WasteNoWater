import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// In production nginx proxies /api and /sim (see nginx.conf).
// For `npm run dev` the same routes are proxied to the services on localhost.
export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    proxy: {
      "/api": "http://localhost:8000",
      "/sim": { target: "http://localhost:8001", rewrite: (p) => p.replace(/^\/sim/, "") },
    },
  },
});
