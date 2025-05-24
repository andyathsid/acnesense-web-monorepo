
const express = require('express');
const bcrypt = require('bcrypt');
const db = require('../config/db');
const router = express.Router();

// Middleware untuk mengecek apakah user sudah login
const requireAuth = (req, res, next) => {
  if (!req.session.userId) {
    return res.redirect('/login');
  }
  next();
};

// Middleware untuk mengecek apakah user sudah login (redirect ke dashboard jika sudah login)
const requireGuest = (req, res, next) => {
  if (req.session.userId) {
    return res.redirect('/dashboard');
  }
  next();
};

// Fungsi untuk menghitung umur yang diperbaiki
function calculateAge(birthDate) {
  const today = new Date();
  const birth = new Date(birthDate);
  
  // Pastikan tanggal valid
  if (isNaN(birth.getTime())) {
    return 0;
  }
  
  let age = today.getFullYear() - birth.getFullYear();
  const monthDiff = today.getMonth() - birth.getMonth();
  
  // Jika bulan lahir belum terjadi di tahun ini, atau
  // Jika bulan lahir sama tapi tanggal lahir belum terjadi
  if (monthDiff < 0 || (monthDiff === 0 && today.getDate() < birth.getDate())) {
    age--;
  }
  
  // Pastikan umur tidak negatif
  return age < 0 ? 0 : age;
}

// Route untuk halaman login (dengan middleware guest)
router.get('/', requireGuest, (req, res) => {
  res.render('login');
});

router.get('/login', requireGuest, (req, res) => {
  res.render('login');
});

// Route untuk halaman registrasi (dengan middleware guest)
router.get('/register', requireGuest, (req, res) => {
  res.render('registrasi');
});

// Route untuk proses registrasi
router.post('/register', async (req, res) => {
  try {
    const { fullname, email, birthdate, password, confirmPassword } = req.body;

    // Validasi input
    if (!fullname || !email || !birthdate || !password || !confirmPassword) {
      return res.json({
        success: false,
        message: 'Semua field harus diisi!'
      });
    }

    // Validasi nama (minimal 2 karakter)
    if (fullname.trim().length < 2) {
      return res.json({
        success: false,
        message: 'Nama minimal 2 karakter!'
      });
    }

    // Validasi email format
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(email)) {
      return res.json({
        success: false,
        message: 'Format email tidak valid!'
      });
    }

    // Validasi tanggal lahir
    const birthDateObj = new Date(birthdate);
    const today = new Date();
    
    if (isNaN(birthDateObj.getTime())) {
      return res.json({
        success: false,
        message: 'Tanggal lahir tidak valid!'
      });
    }

    if (birthDateObj >= today) {
      return res.json({
        success: false,
        message: 'Tanggal lahir harus sebelum hari ini!'
      });
    }

    // Validasi umur
    const age = calculateAge(birthdate);
    if (age > 120) {
      return res.json({
        success: false,
        message: 'Tanggal lahir tidak valid!'
      });
    }

    // Validasi password
    if (password !== confirmPassword) {
      return res.json({
        success: false,
        message: 'Password dan konfirmasi password tidak cocok!'
      });
    }

    if (password.length < 6) {
      return res.json({
        success: false,
        message: 'Password minimal 6 karakter!'
      });
    }

    // Cek apakah email sudah terdaftar
    const checkEmailQuery = 'SELECT * FROM user WHERE email = ?';
    db.query(checkEmailQuery, [email.toLowerCase().trim()], async (err, results) => {
      if (err) {
        console.error('Database error:', err);
        return res.json({
          success: false,
          message: 'Terjadi kesalahan pada server!'
        });
      }

      if (results.length > 0) {
        return res.json({
          success: false,
          message: 'Email sudah terdaftar!'
        });
      }

      try {
        // Hash password
        const saltRounds = 12;
        const hashedPassword = await bcrypt.hash(password, saltRounds);

        // Hitung umur
        const calculatedAge = calculateAge(birthdate);

        // Insert user baru dengan status default 'baru'
        const insertQuery = `
          INSERT INTO user (nama, email, password, foto_profile, tanggal_lahir, umur, status) 
          VALUES (?, ?, ?, ?, ?, ?, ?)
        `;
        
        const defaultPhoto = '/image/foto_profile/default.png';
        
        db.query(insertQuery, [
          fullname.trim(), 
          email.toLowerCase().trim(), 
          hashedPassword, 
          defaultPhoto, 
          birthdate, 
          calculatedAge, 
          'baru'  // Default status adalah 'baru'
        ], (err, result) => {
          if (err) {
            console.error('Database error:', err);
            return res.json({
              success: false,
              message: 'Gagal mendaftarkan user!'
            });
          }

          console.log(`User registered successfully: ${email}, Age: ${calculatedAge}`);
          res.json({
            success: true,
            message: 'Registrasi berhasil! Silakan login dengan akun Anda.'
          });
        });

      } catch (hashError) {
        console.error('Hash error:', hashError);
        return res.json({
          success: false,
          message: 'Terjadi kesalahan pada server!'
        });
      }
    });

  } catch (error) {
    console.error('Registration error:', error);
    res.json({
      success: false,
      message: 'Terjadi kesalahan pada server!'
    });
  }
});

// Route untuk proses login
router.post('/login', (req, res) => {
  try {
    const { email, password } = req.body;

    // Validasi input
    if (!email || !password) {
      return res.json({
        success: false,
        message: 'Email dan password harus diisi!'
      });
    }

    // Validasi email format
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(email)) {
      return res.json({
        success: false,
        message: 'Format email tidak valid!'
      });
    }

    // Cari user berdasarkan email
    const query = 'SELECT * FROM user WHERE email = ?';
    db.query(query, [email.toLowerCase().trim()], async (err, results) => {
      if (err) {
        console.error('Database error:', err);
        return res.json({
          success: false,
          message: 'Terjadi kesalahan pada server!'
        });
      }

      if (results.length === 0) {
        return res.json({
          success: false,
          message: 'Email tidak terdaftar!'
        });
      }

      const user = results[0];

      try {
        // Verifikasi password
        const passwordMatch = await bcrypt.compare(password, user.password);

        if (!passwordMatch) {
          return res.json({
            success: false,
            message: 'Password salah!'
          });
        }

        // Set session dengan informasi lengkap
        req.session.userId = user.id_user;
        req.session.userEmail = user.email;
        req.session.userName = user.nama;
        req.session.userAge = user.umur;
        req.session.userPhoto = user.foto_profile;
        req.session.loginTime = new Date();

        console.log(`User logged in: ${user.email} at ${new Date()}`);
        
        res.json({
          success: true,
          message: 'Login berhasil!',
          user: {
            id: user.id_user,
            name: user.nama,
            email: user.email,
            age: user.umur
          }
        });

      } catch (compareError) {
        console.error('Password comparison error:', compareError);
        return res.json({
          success: false,
          message: 'Terjadi kesalahan pada server!'
        });
      }
    });

  } catch (error) {
    console.error('Login error:', error);
    res.json({
      success: false,
      message: 'Terjadi kesalahan pada server!'
    });
  }
});

// Route untuk logout
router.post('/logout', requireAuth, (req, res) => {
  const userEmail = req.session.userEmail;
  
  req.session.destroy((err) => {
    if (err) {
      console.error('Session destroy error:', err);
      return res.json({
        success: false,
        message: 'Gagal logout!'
      });
    }
    
    console.log(`User logged out: ${userEmail} at ${new Date()}`);
    res.json({
      success: true,
      message: 'Logout berhasil!'
    });
  });
});

// Route untuk dashboard (dengan middleware auth) - DIPINDAH KE EJS
router.get('/dashboard', requireAuth, (req, res) => {
  // Ambil data user terbaru dari database
  const query = 'SELECT * FROM user WHERE id_user = ?';
  db.query(query, [req.session.userId], (err, results) => {
    if (err) {
      console.error('Database error:', err);
      return res.redirect('/login');
    }

    if (results.length === 0) {
      return res.redirect('/login');
    }

    const user = results[0];
    
    // Render dashboard.ejs dengan data user
    res.render('dashboard', {
      user: user,
      loginTime: req.session.loginTime
    });
  });
});

// Route untuk cek status session (API endpoint)
router.get('/api/session-status', (req, res) => {
  if (req.session.userId) {
    res.json({
      loggedIn: true,
      user: {
        id: req.session.userId,
        name: req.session.userName,
        email: req.session.userEmail
      }
    });
  } else {
    res.json({
      loggedIn: false
    });
  }
});

router.use((req, res) => {
  res.status(404).render('404'); // Mengarahkan ke views/404.ejs
})

module.exports = router;
