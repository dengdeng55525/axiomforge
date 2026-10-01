import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue";
export default defineConfig({
  plugins: [vue()],
  base: "/app/",
  server: {
    port: 5173,
    proxy: Object.fromEntries(
      [
        "health",
        "system",
        "harness",
        "runs",
        "config",
        "graph",
        "capabilities",
        "datasets",
        "inference",
      ].map((p) => [
        "/" + p,
        {
          target: process.env.ALGOFORGE_API_URL || "http://127.0.0.1:8000",
          changeOrigin: false,
        },
      ]),
    ),
  },
  build: { outDir: "dist", sourcemap: false },
});
