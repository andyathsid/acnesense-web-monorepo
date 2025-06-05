const express = require('express');
const path = require('path');
const session = require('express-session');
const db = require('./config/db');
const routes = require('./routes/routes');

const app = express();
const PORT = 3001;

// Middleware untuk parsing
app.use(express.json({ limit: '10mb' }));
app.use(express.urlencoded({ extended: true, limit: '10mb' }));

// Static files configuration
app.use(express.static(path.join(__dirname, 'public')));

// Session configuration
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

// Request logging middleware
app.use((req, res, next) => {
  console.log(`${new Date().toISOString()} - ${req.method} ${req.url} - Session ID: ${req.session.id || 'none'}`);
  next();
});

// Routes
app.use('/', routes);

// Error handler untuk 500
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

// Start server
const server = app.listen(PORT, () => {
  console.log(`===========================================`);
  console.log(`🚀 AcneSense Server Running`);
  console.log(`📍 URL: http://localhost:${PORT}`);
  console.log(`⏰ Started at: ${new Date().toLocaleString('id-ID')}`);
  console.log(`🖼️  Static files: ${path.join(__dirname, 'public')}`);
  console.log(`===========================================`);
});