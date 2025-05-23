
const express = require('express');
const path = require('path');
const session = require('express-session');
const db = require('./config/db');
const routes = require('./routes/routes');

const app = express();
const PORT = 3000;

// Middleware untuk parsing
app.use(express.json({ limit: '10mb' }));
app.use(express.urlencoded({ extended: true, limit: '10mb' }));

// Static files configuration - PERBAIKAN DI SINI
// Serve static files from public directory
app.use(express.static(path.join(__dirname, 'public')));

// Alternative static route (opsional, untuk akses explicit dengan /public)
app.use('/public', express.static(path.join(__dirname, 'public')));

// Session configuration dengan keamanan yang lebih baik
app.use(session({
  secret: 'acnesense_secret_key_2024_very_secure_random_string',
  resave: false,
  saveUninitialized: false,
  name: 'acnesense_session',
  cookie: { 
    secure: false,
    httpOnly: true,
    maxAge: 24 * 60 * 60 * 1000,
    sameSite: 'lax'
  },
  rolling: true
}));

// Security headers middleware
app.use((req, res, next) => {
  res.setHeader('X-Content-Type-Options', 'nosniff');
  res.setHeader('X-Frame-Options', 'DENY');
  res.setHeader('X-XSS-Protection', '1; mode=block');
  next();
});

// Set view engine
app.set('view engine', 'ejs');
app.set('views', path.join(__dirname, 'views'));

// Request logging middleware (development)
app.use((req, res, next) => {
  console.log(`${new Date().toISOString()} - ${req.method} ${req.url} - Session ID: ${req.session.id || 'none'}`);
  next();
});

// Debug middleware untuk static files (opsional, untuk debugging)
app.use((req, res, next) => {
  if (req.url.includes('/image/') || req.url.includes('/css/') || req.url.includes('/js/')) {
    console.log(`Static file request: ${req.url}`);
  }
  next();
});

// Routes
app.use('/', routes);

// 404 handler
app.use((req, res) => {
  res.status(404).send(`
    <!DOCTYPE html>
    <html>
    <head>
      <title>404 - Halaman Tidak Ditemukan</title>
      <script src="https://cdn.tailwindcss.com"></script>
    </head>
    <body class="bg-gray-100 flex items-center justify-center min-h-screen">
      <div class="text-center">
        <h1 class="text-6xl font-bold text-gray-800 mb-4">404</h1>
        <p class="text-xl text-gray-600 mb-8">Halaman yang Anda cari tidak ditemukan</p>
        <a href="/login" class="bg-blue-500 hover:bg-blue-600 text-white px-6 py-3 rounded-lg transition-colors">
          Kembali ke Login
        </a>
      </div>
    </body>
    </html>
  `);
});

// Error handler
app.use((err, req, res, next) => {
  console.error('Error:', err);
  res.status(500).send(`
    <!DOCTYPE html>
    <html>
    <head>
      <title>500 - Server Error</title>
      <script src="https://cdn.tailwindcss.com"></script>
    </head>
    <body class="bg-gray-100 flex items-center justify-center min-h-screen">
      <div class="text-center">
        <h1 class="text-6xl font-bold text-red-600 mb-4">500</h1>
        <p class="text-xl text-gray-600 mb-8">Terjadi kesalahan pada server</p>
        <a href="/login" class="bg-blue-500 hover:bg-blue-600 text-white px-6 py-3 rounded-lg transition-colors">
          Kembali ke Login
        </a>
      </div>
    </body>
    </html>
  `);
});

// Graceful shutdown
process.on('SIGTERM', () => {
  console.log('SIGTERM signal received: closing HTTP server');
  server.close(() => {
    console.log('HTTP server closed');
    db.end(() => {
      console.log('Database connection closed');
      process.exit(0);
    });
  });
});

// Start server
const server = app.listen(PORT, () => {
  console.log(`===========================================`);
  console.log(`🚀 AcneSense Server Running`);
  console.log(`📍 URL: http://localhost:${PORT}`);
  console.log(`⏰ Started at: ${new Date().toLocaleString('id-ID')}`);
  console.log(`🖼️  Static files: ${path.join(__dirname, 'public')}`);
  console.log(`===========================================`);
});
