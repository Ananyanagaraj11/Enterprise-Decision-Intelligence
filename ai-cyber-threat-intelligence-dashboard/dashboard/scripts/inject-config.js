const fs = require('fs');
const path = require('path');
const apiUrl = process.env.API_URL || process.env.VERCEL_API_URL || 'https://ai-cyber-threat-dashboard-1.onrender.com';
const out = path.join(__dirname, '..', 'js', 'config.js');
const line = apiUrl
  ? `window.ENV_API_BASE = "${apiUrl.replace(/"/g, '\\"')}";`
  : 'window.ENV_API_BASE = null;';
fs.writeFileSync(out, '// Injected at build (Vercel env API_URL)\n' + line + '\n', 'utf8');
console.log('Wrote js/config.js with API_BASE:', apiUrl || 'null');
