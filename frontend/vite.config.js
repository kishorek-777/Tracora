import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { VitePWA } from 'vite-plugin-pwa'
import { fileURLToPath, URL } from 'node:url'

export default defineConfig(({ command }) => ({
  plugins: [
    react(),
    VitePWA({
      registerType: 'autoUpdate',
      injectRegister: null,
      manifestFilename: 'manifest.json',
      includeAssets: ['favicon.svg', 'icon-192.png', 'icon-512.png'],
      manifest: {
        name: 'Tracora Asset Scanner',
        short_name: 'Tracora',
        description: 'Asset custody and scanner PWA for Aionion Capital',
        start_url: '/mobile',
        scope: '/mobile',
        display: 'standalone',
        orientation: 'portrait',
        background_color: '#ffffff',
        theme_color: '#0f172a',
        icons: [
          {
            src: '/assets/tracora/frontend/icon-192.png',
            sizes: '192x192',
            type: 'image/png',
            purpose: 'any maskable',
          },
          {
            src: '/assets/tracora/frontend/icon-512.png',
            sizes: '512x512',
            type: 'image/png',
            purpose: 'any maskable',
          },
        ],
      },
      workbox: {
        navigateFallback: '/assets/tracora/frontend/mobile.html',
        navigateFallbackAllowlist: [/^\/mobile/],
        navigateFallbackDenylist: [/^\/api\//, /^\/assets\//, /^\/app/, /^\/tracora/],
        runtimeCaching: [
          {
            urlPattern: /^\/api\//,
            handler: 'NetworkOnly',
          },
          {
            urlPattern: /^\/mobile(\/.*)?$/,
            handler: 'NetworkFirst',
            options: {
              cacheName: 'tracora-mobile-shell',
              networkTimeoutSeconds: 3,
              expiration: {
                maxEntries: 5,
                maxAgeSeconds: 86400,
              },
            },
          },
        ],
      },
    }),
    {
      name: 'strip-pwa-from-desktop',
      enforce: 'post',
      generateBundle(_, bundle) {
        if (bundle['index.html']) {
          bundle['index.html'].source = bundle['index.html'].source.replace(
            /<link rel="manifest"[^>]*>/g,
            ''
          )
        }
      },
    },
  ],
  base: command === 'build' ? '/assets/tracora/frontend/' : '/',
  build: {
    outDir: '../tracora/public/frontend',
    emptyOutDir: true,
    rollupOptions: {
      input: {
        main: fileURLToPath(new URL('./index.html', import.meta.url)),
        mobile: fileURLToPath(new URL('./mobile.html', import.meta.url)),
      },
    },
  },
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
    },
  },
  server: {
    port: 5173,
    host: '0.0.0.0',
  },
}))
