const fs = require('fs');
const path = require('path');

class ViteHelper {
  constructor() {
    this.isDev = process.env.NODE_ENV !== 'production';
    this.manifest = null;
    
    if (!this.isDev) {
      this.loadManifest();
    }
  }

  loadManifest() {
    try {
      const manifestPath = path.join(__dirname, '../public/dist/manifest.json');
      if (fs.existsSync(manifestPath)) {
        this.manifest = JSON.parse(fs.readFileSync(manifestPath, 'utf-8'));
      }
    } catch (error) {
      console.error('Failed to load Vite manifest:', error);
    }
  }

  getAssetUrl(entrypoint) {
    if (this.isDev) {
      // Development mode - map entry point names to actual file paths
      // Since vite.config.js has root: 'src', files are served relative to src/
      const entryPointMap = {
        'main': 'js/main.js',
        'deteksi': 'js/deteksi.js'
      };
      const filePath = entryPointMap[entrypoint] || entrypoint;
      return `http://localhost:5174/${filePath}`;
    } else {
      // Production mode - use manifest to get hashed filenames
      if (this.manifest && this.manifest[entrypoint]) {
        return `/dist/${this.manifest[entrypoint].file}`;
      }
      // Fallback
      return `/dist/${entrypoint}`;
    }
  }

  getCSSUrl(entrypoint) {
    if (this.isDev) {
      // In dev mode, CSS is injected by Vite
      return null;
    } else {
      // Production mode - use manifest to get CSS files
      if (this.manifest && this.manifest[entrypoint] && this.manifest[entrypoint].css) {
        return this.manifest[entrypoint].css.map(css => `/dist/${css}`);
      }
      return null;
    }
  }

  getScriptTag(entrypoint) {
    const url = this.getAssetUrl(entrypoint);
    if (this.isDev) {
      return `<script type="module" src="${url}"></script>`;
    } else {
      return `<script type="module" src="${url}"></script>`;
    }
  }

  getCSSTag(entrypoint) {
    const cssUrls = this.getCSSUrl(entrypoint);
    if (!cssUrls) return '';
    
    return cssUrls.map(url => `<link rel="stylesheet" href="${url}">`).join('\n');
  }

  getViteClientScript() {
    if (this.isDev) {
      return '<script type="module" src="http://localhost:5174/@vite/client"></script>';
    }
    return '';
  }
}

const viteHelper = new ViteHelper();

module.exports = viteHelper;
