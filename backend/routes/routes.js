const express = require('express');
const bcrypt = require('bcrypt');
const db = require('../config/db');
const router = express.Router();
const fs = require('fs'); 

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
  res.render('index');
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

// Route untuk ke halaman deteksi
router.get('/deteksi', requireAuth, (req, res) => {
  const user = {
    id_user: req.session.userId,
    foto_profile: req.session.userPhoto,
  };
  res.render('deteksi', { user });
});

// Route untuk ke halaman preview
// Route untuk ke halaman preview
router.get('/preview', requireAuth, (req, res) => {
    const userId = req.session.userId;

    // Ambil data user terbaru dari database
    const query = 'SELECT umur, Jenis_kulit, skin_tone, foto_profile FROM user WHERE id_user = ?';
    db.query(query, [userId], (err, results) => {
        if (err || results.length === 0) {
            console.error('Database error:', err);
            return res.redirect('/login'); // Redirect jika ada kesalahan
        }

        // Ambil data user
        const user = {
            id_user: userId,
            foto_profile: results[0].foto_profile,
            umur: results[0].umur,
            jenis_kulit: results[0].Jenis_kulit,
            skin_tone: results[0].skin_tone,
        };

        const imageUrl = req.query.image || ''; // Ambil gambar dari query

        // Kirim data user dan gambar ke preview.ejs
        res.render('preview', { user, imageUrl });
    });
});

// Route untuk mengakses halaman chatbot
router.get('/chatbot', requireAuth, (req, res) => {
    const user = {
    id_user: req.session.userId,
    foto_profile: req.session.userPhoto,
  };
  res.render('chatbot', { user });
});

// Tambahkan route untuk menampilkan riwayat
router.get('/riwayat', requireAuth, (req, res) => {
    const userId = req.session.userId;

    // Ambil data riwayat berdasarkan id_user
    const query = `SELECT id_riwayat, judul_penyakit, gambar, overview, created_at 
                   FROM riwayat 
                   WHERE id_user = ? 
                   ORDER BY created_at DESC`; // Mengambil riwayat sesuai id_user dan urutkan

    db.query(query, [userId], (err, results) => {
        if (err) {
            console.error('Database error:', err);
            return res.redirect('/login'); // Redirect jika ada kesalahan
        }

        // Truncate overview untuk setiap item
        const truncatedResults = results.map(item => {
            return {
                ...item,
                overview: truncateOverview(item.overview,20) // Memanggil fungsi truncateOverview
            };
        });

        // Render riwayat.ejs dengan data yang diambil
        res.render('riwayat', {
            user: {
                id_user: req.session.userId,
                foto_profile: req.session.userPhoto,
            },
            riwayat: truncatedResults // Mengirimkan data riwayat yang sudah dipotong ke view
        });
    });
});

// Fungsi untuk memotong overview
function truncateOverview(overview, wordLimit) {
    const words = overview.split(' ');
    return words.length > wordLimit ? words.slice(0, wordLimit).join(' ') + '...' : overview;
}

// Route untuk mengambil data riwayat berdasarkan id_riwayat


// Setelah redirection, pada route hasil, ambil data yang terbaru
router.get('/hasil/:id_riwayat', requireAuth, (req, res) => {
    const idRiwayat = req.params.id_riwayat; // Get id_riwayat from the URL
   // Ambil informasi pengguna dari sesi
    const user = {
        id_user: req.session.userId,
        foto_profile: req.session.userPhoto,
    };
    // SQL Query to get disease history data
    const query = `
        SELECT 
            r.judul_penyakit, 
            r.gambar AS image_asli, 
            r.overview, 
            r.recommendations, 
            r.skincare_tips, 
            r.important_notes, 
            rd.acne_types, 
            rd.jumlah_klasifikasi, 
            rd.gambar_detail AS image_klas
        FROM 
            riwayat AS r
        LEFT JOIN 
            riwayat_detail AS rd ON r.id_riwayat = rd.id_riwayat
        WHERE 
            r.id_riwayat = ?
    `;

    db.query(query, [idRiwayat], (err, results) => {
        if (err || results.length === 0) {
            console.error('Database error:', err);
            return res.redirect('/login'); // Redirect if there's an error or no data found
        }

        // Extract unique acne types
        const acneTypes = results.map(row => row.acne_types).filter(type => type);
        const uniqueAcneTypes = [...new Set(acneTypes.join(', ').split(','))];

        // Use the first result for rendering overview, recommendations, etc.
        const firstResult = results[0];

        // Format image_klas to match the specified structure
        const imageKlas = results.map(item => {
            return item.image_klas ? `data:image/jpeg;base64,${item.image_klas}` : null;
        }).filter(image => image); // Filter out nulls

        // Render the hasil.ejs page with the collected data
        res.render('hasil', {
            user, // Mengirimkan objek user ke template
            jumlah_deteksi: results.length, // Total number of results
            klas_deteksi: uniqueAcneTypes, // Unique acne types
            image_asli: firstResult.image_asli, // Original image
            image_klas: imageKlas, // Formatted image_klas
            overview: firstResult.overview, // Overview from the first result
            recommendations: firstResult.recommendations, // Recommendations from first result
            skincare_tips: firstResult.skincare_tips, // Skincare tips from first result
            important_notes: firstResult.important_notes // Important notes from first result
        });
    });
});

// Add this route to handle saving detection results
// Add this route to handle saving detection results
// Tambahkan route untuk menyimpan deteksi
// Route untuk menyimpan deteksi
// Route untuk menyimpan deteksi
router.post('/save-detection', requireAuth, (req, res) => {
    const detectionData = req.body;

    // Pastikan semua properti tersedia
    if (!detectionData.acne_types || !detectionData.classification_results || 
        !detectionData.detection_classes || !detectionData.recommendation || 
        !detectionData.captured_image) {
        return res.status(400).json({ success: false, message: 'Data tidak lengkap.' });
    }

    // Ekstrak data yang diperlukan
    const overview = `## OVERVIEW\n${detectionData.recommendation.split('## OVERVIEW')[1].split('## RECOMMENDATIONS')[0].trim()}`;
    const recommendations = `## RECOMMENDATIONS\n\n${detectionData.recommendation.split('## RECOMMENDATIONS')[1].split('## SKINCARE TIPS')[0].trim()}`;
    const skincareTips = `## SKINCARE TIPS\n\n${detectionData.recommendation.split('## SKINCARE TIPS')[1].split('## IMPORTANT NOTES')[0].trim()}`;
    const importantNotes = `## IMPORTANT NOTES\n\n${detectionData.recommendation.split('## IMPORTANT NOTES')[1] || ''}`; // tambah default ke empty string
    const userId = req.session.userId;

    // Mengambil acne_types dari response
    const acneTypes = detectionData.acne_types; // Ambil acne_types dari deteksi
    const judulPenyakit = acneTypes.join(', '); // Menggabungkan acne_types menjadi satu string

    // Mengambil detection_result untuk disimpan dalam kolom gambar
    const detectionResultImage = detectionData.detection_result; // Ambil detection_result dari request

    // Query untuk menyimpan data ke tabel 'riwayat'
    const insertRiwayatQuery = `
        INSERT INTO riwayat (id_user, judul_penyakit, gambar, overview, recommendations, skincare_tips, important_notes)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    `;

    db.query(insertRiwayatQuery, [
        userId,
        judulPenyakit, // Simpan judul penyakit dari acne_types
        detectionResultImage, // Simpan detection_result
        overview,            // Menyimpan overview
        recommendations,     // Menyimpan recommendations
        skincareTips,       // Menyimpan skincare tips
        importantNotes      // Menyimpan important notes
    ], (err, result) => {
        if (err) {
            console.error('Database insert error:', err);
            return res.status(500).json({ success: false, message: 'Gagal menyimpan data deteksi.' });
        }

        const idRiwayat = result.insertId; // Ambil ID riwayat yang baru disimpan
        // Logging ID riwayat yang baru
        console.log(`Data berhasil disimpan di tabel 'riwayat': idRiwayat=${idRiwayat}`);

        // Ambil detection_classes dan classification_results
        const detectionClasses = detectionData.detection_classes || []; // Ambil detection_classes
        const classificationResults = detectionData.classification_results || []; // Ambil classification_results

        // Simpan data ke tabel 'riwayat_detail' untuk setiap kelas
        const detailInsertQueries = []; // Array untuk menyimpan query insert
        const jumlahKlasifikasi = detectionData.detection_count; // Jumlah klasifikasi dari detection_count

        // Loop untuk menyimpan setiap class ke dalam riwayat_detail
        for (let i = 0; i < detectionClasses.length; i++) {
            const acneType = detectionClasses[i]; // Mengambil acne type

            // Mencari gambar detail berdasarkan class
            const classData = classificationResults.find(result => result.class === acneType);
            const gambarDetail = classData ? classData.image : null; // Ambil gambar berdasarkan class
            
            // Hilangkan prefix data:image/jpeg;base64, jika ada
            const gambarDetailCleaned = gambarDetail ? gambarDetail.replace(/^data:image\/jpeg;base64,/, '') : null;

            // Debug: Log kelas dan gambar detail
            console.log(`Inserting into riwayat_detail: id_riwayat=${idRiwayat}, acneType=${acneType}, jumlahKlasifikasi=${jumlahKlasifikasi}, gambarDetail=${gambarDetailCleaned ? gambarDetailCleaned.substring(0, 30) + '...' : 'none'}`);

            detailInsertQueries.push(new Promise((resolve, reject) => {
                const insertDetailQuery = `
                    INSERT INTO riwayat_detail (id_riwayat, acne_types, jumlah_klasifikasi, gambar_detail)
                    VALUES (?, ?, ?, ?)
                `;

                db.query(insertDetailQuery, [
                    idRiwayat,
                    acneType, // Simpan acne type dari detection_classes
                    jumlahKlasifikasi, // Simpan jumlah klasifikasi
                    gambarDetailCleaned // Simpan gambar detail yang sudah dibersihkan
                ], (err) => {
                    if (err) {
                        console.error('Database detail insert error:', err);
                        return reject(err);
                    }
                    resolve();
                });
            }));
        }

        // Tunggu semua insert detail selesai
        Promise.all(detailInsertQueries)
            .then(() => {
                res.status(200).json({ success: true, message: 'Data deteksi dan detail berhasil disimpan.', id_riwayat: idRiwayat });
            })
            .catch(err => {
                console.error('Error saving detail data:', err);
                res.status(500).json({ success: false, message: 'Gagal menyimpan detail data.', error: err });
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



// Route untuk menangani 404
router.use((req, res) => {
  res.status(404).render('404'); // Mengarahkan ke views/404.ejs
})

module.exports = router;