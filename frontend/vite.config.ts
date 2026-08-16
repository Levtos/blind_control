import { svelte } from '@sveltejs/vite-plugin-svelte';
import { defineConfig, type Plugin } from 'vite';

function normalizePanelStylesheet(): Plugin {
  return {
    name: 'blind-control-normalize-inline-css',
    enforce: 'pre',
    transform(code, id) {
      const sourceId = (id.split('?', 1)[0] ?? id).replaceAll('\\', '/');
      if (!sourceId.endsWith('/src/app.css')) return null;
      return { code: code.replaceAll('\r\n', '\n'), map: null };
    },
  };
}

export default defineConfig({
  plugins: [normalizePanelStylesheet(), svelte()],
  build: {
    outDir: '../custom_components/blind_control/frontend',
    emptyOutDir: true,
    minify: false,
    rollupOptions: {
      input: 'src/main.ts',
      output: {
        entryFileNames: 'blind-control-panel.js',
        chunkFileNames: 'assets/[name]-[hash].js',
        assetFileNames: 'assets/[name]-[hash][extname]',
      },
    },
  },
});
