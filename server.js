require('dotenv').config();

const express = require('express');
const path = require('path');
const cookieParser = require('cookie-parser');
const routes = require('./routes/routes');
const { supabase } = require('./config/db');
const viteHelper = require('./config/vite');

const app = express();
const PORT = process.env.PORT || 3000;

// Middleware untuk parsing
app.use(express.json({ limit: '50mb' }));
app.use(express.urlencoded({ extended: true, limit: '50mb' }));

// Static file serving with environment-aware logic
if (process.env.NODE_ENV === 'production') {
  console.log('INFO: Serving static files from web/dist');
  app.use(express.static(path.join(__dirname, 'dist')));
} else {
  console.log('INFO: Serving static files from web/public');
  app.use(express.static(path.join(__dirname, 'public')));
}

app.use(cookieParser());

// Custom auth middleware instead of express-session
app.use(async (req, res, next) => {
  const token = req.headers.authorization?.replace('Bearer ', '') || 
                req.cookies?.access_token;
  
  if (token) {
    try {
      const { data: { user }, error } = await supabase.auth.getUser(token);
      if (!error && user) {
        req.user = user;
        req.accessToken = token;
      }
    } catch (err) {
      console.error('Auth error:', err);
    }
  }
  next();
});

// View engine
app.set('view engine', 'ejs');
app.set('views', path.join(__dirname, 'views'));

// Make Vite helper available to all templates
app.use((req, res, next) => {
  res.locals.vite = viteHelper;
  next();
});

// Routes
app.use('/', routes);

// Error handling middleware
app.use((err, req, res, next) => {
  console.error('Server error:', err);
  res.status(500).json({ 
    success: false, 
    message: 'Internal server error' 
  });
});

app.listen(PORT, () => {
  console.log(`Server running on port http://localhost:${PORT}`);
});
