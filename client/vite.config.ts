import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// Vite configuration for the AI Researcher client.
// - Proxies /api to the FastAPI backend on port 8000 during development.
// - Uses React with modern JSX transform.

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      "/api": {
        target: "http://localhost:8000",
        changeOrigin: true
      }
    }
  },
  preview: {
    port: 4173
  },
  optimizeDeps: {
    include: ["jspdf", "docx", "pptxgenjs"]
  }
});


