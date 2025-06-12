const express = require('express');
const { requireAuth, requireGuest } = require('../middleware/auth');
const User = require('../models/User');
const Riwayat = require('../models/Riwayat');
const RiwayatDetail = require('../models/RiwayatDetail');
const router = express.Router();

// Utility function for age calculation
function calculateAge(birthDate) {
  const today = new Date();
  const birth = new Date(birthDate);
  
  if (isNaN(birth.getTime())) {
    return 0;
  }
  
  let age = today.getFullYear() - birth.getFullYear();
  const monthDiff = today.getMonth() - birth.getMonth();
  
  if (monthDiff < 0 || (monthDiff === 0 && today.getDate() < birth.getDate())) {
    age--;
  }
  
  return age < 0 ? 0 : age;
}

// Guest routes
router.get('/', requireGuest, (req, res) => {
  res.render('index');
});

router.get('/login', requireGuest, (req, res) => {
  res.render('login');
});

router.get('/register', requireGuest, (req, res) => {
  res.render('registrasi');
});

// router.get('/profile', requireGuest, (req, res) => {
//   res.render('profile');
// });
// Registration route
router.post('/register', async (req, res) => {
  try {
    const { fullname, email, birthdate, password, confirmPassword } = req.body;

    // Validation
    if (!fullname || !email || !birthdate || !password || !confirmPassword) {
      return res.json({
        success: false,
        message: 'Semua field harus diisi!'
      });
    }

    if (fullname.trim().length < 2) {
      return res.json({
        success: false,
        message: 'Nama minimal 2 karakter!'
      });
    }

    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(email)) {
      return res.json({
        success: false,
        message: 'Format email tidak valid!'
      });
    }

    const birthDateObj = new Date(birthdate);
    const today = new Date();
    
    if (isNaN(birthDateObj.getTime()) || birthDateObj >= today) {
      return res.json({
        success: false,
        message: 'Tanggal lahir tidak valid!'
      });
    }

    const age = calculateAge(birthdate);
    if (age > 120) {
      return res.json({
        success: false,
        message: 'Tanggal lahir tidak valid!'
      });
    }

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

    // Check if email exists
    const existingUser = await User.findByEmail(email);
    if (existingUser) {
      return res.json({
        success: false,
        message: 'Email sudah terdaftar!'
      });
    }

    // Create user
    await User.create({
      nama: fullname.trim(),
      email: email.toLowerCase().trim(),
      password,
      tanggal_lahir: birthdate
    });

    res.json({
      success: true,
      message: 'Registrasi berhasil! Silakan login dengan akun Anda.'
    });

  } catch (error) {
    console.error('Registration error:', error);
    res.json({
      success: false,
      message: error.message || 'Terjadi kesalahan pada server!'
    });
  }
});

// Login route
router.post('/login', async (req, res) => {
  try {
    const { email, password } = req.body;

    if (!email || !password) {
      return res.json({
        success: false,
        message: 'Email dan password harus diisi!'
      });
    }

    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(email)) {
      return res.json({
        success: false,
        message: 'Format email tidak valid!'
      });
    }

    // Sign in with Supabase Auth
    const { user, session } = await User.signIn(email, password);

    if (!user || !session) {
      return res.json({
        success: false,
        message: 'Email atau password salah!'
      });
    }

    // Get user profile
    const profile = await User.findById(user.id);
    if (!profile) {
      return res.json({
        success: false,
        message: 'Profil pengguna tidak ditemukan!'
      });
    }

    // Set HTTP-only cookie for token
    res.cookie('access_token', session.access_token, {
      httpOnly: true,
      secure: process.env.NODE_ENV === 'production',
      sameSite: 'strict',
      maxAge: 24 * 60 * 60 * 1000 // 24 hours
    });

    console.log(`User logged in: ${user.email} at ${new Date()}`);
    
    res.json({
      success: true,
      message: 'Login berhasil!',
      user: {
        id: user.id,
        name: profile.nama,
        email: user.email,
        age: profile.umur
      },
      token: session.access_token
    });

  } catch (error) {
    console.error('Login error:', error);
    res.json({
      success: false,
      message: 'Email atau password salah!'
    });
  }
});

// Logout route
router.post('/logout', requireAuth, async (req, res) => {
  try {
    const userEmail = req.user.email;
    
    // Sign out from Supabase
    await User.signOut();
    
    // Clear the cookie
    res.clearCookie('access_token');
    
    console.log(`User logged out: ${userEmail} at ${new Date()}`);
    res.json({
      success: true,
      message: 'Logout berhasil!'
    });
  } catch (error) {
    console.error('Logout error:', error);
    res.json({
      success: false,
      message: 'Gagal logout!'
    });
  }
});

// Protected routes
router.get('/dashboard', requireAuth, async (req, res) => {
  try {
    const user = await User.findById(req.user.id);
    if (!user) {
      return res.redirect('/login');
    }

    res.render('dashboard', {
      user: user,
      loginTime: new Date() // Since we don't track login time in tokens, use current time
    });
  } catch (error) {
    console.error('Dashboard error:', error);
    res.redirect('/login');
  }
});

router.get('/deteksi', requireAuth, async (req, res) => {
  try {
    const user = await User.findById(req.user.id);
    res.render('deteksi', { user });
  } catch (error) {
    console.error('Deteksi error:', error);
    res.redirect('/login');
  }
});

router.get('/preview', requireAuth, async (req, res) => {
  try {
    const user = await User.findById(req.user.id);
    const imageUrl = req.query.image || '';
    res.render('preview', { user, imageUrl });
  } catch (error) {
    console.error('Preview error:', error);
    res.redirect('/login');
  }
});

router.get('/chatbot', requireAuth, async (req, res) => {
  try {
    const user = await User.findById(req.user.id);
    res.render('chatbot', { user });
  } catch (error) {
    console.error('Chatbot error:', error);
    res.redirect('/login');
  }
});

// router.get('/profile', requireAuth, async (req, res) => {
//   res.render('profile');
// });

router.get('/profile', requireAuth, async (req, res) => {
  try {
    const user = await User.findById(req.user.id);
    if (!user) {
      return res.redirect('/login'); // Redirect jika user tidak ditemukan
    }

    res.render('profile', {
      user // Mengirim data pengguna ke EJS
    });
  } catch (error) {
    console.error('Profile error:', error);
    res.redirect('/login'); // Redirect jika terjadi error
  }
});

router.get('/riwayat', requireAuth, async (req, res) => {
  try {
    const riwayatData = await Riwayat.findByUserId(req.user.id);
    
    const truncatedResults = riwayatData.map(item => ({
      ...item,
      overview: truncateOverview(item.overview, 20)
    }));

    const user = await User.findById(req.user.id);
    res.render('riwayat', {
      user,
      riwayat: truncatedResults
    });
  } catch (error) {
    console.error('Riwayat error:', error);
    res.redirect('/login');
  }
});

// Edit profile route
router.get('/edit-profile', requireAuth, async (req, res) => {
  try {
    const user = await User.findById(req.user.id);
    if (!user) {
      return res.redirect('/login'); // Redirect jika user tidak ditemukan
    }

    // Render halaman edit profile, kirimkan data pengguna ke EJS
    res.render('edit-profile', {
      user // Mengirim data pengguna untuk ditampilkan di form
    });
  } catch (error) {
    console.error('Edit Profile error:', error);
    res.redirect('/login'); // Redirect jika terjadi error
  }
});

// Helper function
function truncateOverview(overview, wordLimit) {
  if (!overview) return '';
  const words = overview.split(' ');
  return words.length > wordLimit ? words.slice(0, wordLimit).join(' ') + '...' : overview;
}

router.get('/hasil/:id_riwayat', requireAuth, async (req, res) => {
  try {
    const idRiwayat = req.params.id_riwayat;
    const user = await User.findById(req.user.id);
    
    // Get riwayat with details
    const riwayatData = await Riwayat.findById(idRiwayat);
    if (!riwayatData) {
      return res.redirect('/riwayat');
    }

    // Get riwayat details
    const riwayatDetails = await RiwayatDetail.findByRiwayatId(idRiwayat);

    // Extract unique acne types
    const acneTypes = riwayatDetails.map(detail => detail.acne_types).filter(type => type);
    const uniqueAcneTypes = [...new Set(acneTypes.join(', ').split(','))];

    // Format image_klas
    const imageKlas = riwayatDetails.map(item => {
      return item.gambar_detail ? `data:image/jpeg;base64,${item.gambar_detail}` : null;
    }).filter(image => image);

    res.render('hasil', {
      user,
      jumlah_deteksi: riwayatDetails.length,
      klas_deteksi: uniqueAcneTypes,
      image_asli: riwayatData.gambar,
      image_klas: imageKlas,
      overview: riwayatData.overview,
      recommendations: riwayatData.recommendations,
      skincare_tips: riwayatData.skincare_tips,
      important_notes: riwayatData.important_notes
    });
  } catch (error) {
    console.error('Hasil error:', error);
    res.redirect('/riwayat');
  }
});

router.post('/save-detection', requireAuth, async (req, res) => {
  try {
    const detectionData = req.body;

    if (!detectionData.acne_types || !detectionData.classification_results || 
        !detectionData.detection_classes || !detectionData.recommendation || 
        !detectionData.captured_image) {
      return res.status(400).json({ success: false, message: 'Data tidak lengkap.' });
    }

    // Extract recommendation sections
    const overview = `## OVERVIEW\n${detectionData.recommendation.split('## OVERVIEW')[1].split('## RECOMMENDATIONS')[0].trim()}`;
    const recommendations = `## RECOMMENDATIONS\n\n${detectionData.recommendation.split('## RECOMMENDATIONS')[1].split('## SKINCARE TIPS')[0].trim()}`;
    const skincareTips = `## SKINCARE TIPS\n\n${detectionData.recommendation.split('## SKINCARE TIPS')[1].split('## IMPORTANT NOTES')[0].trim()}`;
    const importantNotes = `## IMPORTANT NOTES\n\n${detectionData.recommendation.split('## IMPORTANT NOTES')[1] || ''}`;
    
    const userId = req.user.id;
    const acneTypes = detectionData.acne_types;
    const judulPenyakit = acneTypes.join(', ');
    const detectionResultImage = detectionData.detection_result;

    // Create riwayat
    const riwayat = await Riwayat.create(userId, {
      judul_penyakit: judulPenyakit,
      gambar: detectionResultImage,
      overview,
      recommendations,
      skincare_tips: skincareTips,
      important_notes: importantNotes
    });

    console.log(`Data berhasil disimpan di tabel 'riwayat': idRiwayat=${riwayat.id_riwayat}`);

    // Create riwayat details
    const detectionClasses = detectionData.detection_classes || [];
    const classificationResults = detectionData.classification_results || [];
    const jumlahKlasifikasi = detectionData.detection_count;

    const detailsToInsert = [];
    for (let i = 0; i < detectionClasses.length; i++) {
      const acneType = detectionClasses[i];
      const classData = classificationResults.find(result => result.class === acneType);
      const gambarDetail = classData ? classData.image : null;
      const gambarDetailCleaned = gambarDetail ? gambarDetail.replace(/^data:image\/jpeg;base64,/, '') : null;

      detailsToInsert.push({
        id_riwayat: riwayat.id_riwayat,
        acne_types: acneType,
        jumlah_klasifikasi: jumlahKlasifikasi,
        gambar_detail: gambarDetailCleaned
      });
    }

    await RiwayatDetail.createMultiple(detailsToInsert);

    res.status(200).json({ 
      success: true, 
      message: 'Data deteksi dan detail berhasil disimpan.', 
      id_riwayat: riwayat.id_riwayat 
    });

  } catch (error) {
    console.error('Save detection error:', error);
    res.status(500).json({ 
      success: false, 
      message: 'Gagal menyimpan data deteksi.',
      error: error.message 
    });
  }
});

// Health check endpoint for Docker
router.get('/health', (req, res) => {
  res.status(200).json({ 
    status: 'healthy', 
    timestamp: new Date().toISOString(),
    uptime: process.uptime()
  });
});

// API routes
router.get('/api/session-status', (req, res) => {
  if (req.user) {
    res.json({
      loggedIn: true,
      user: {
        id: req.user.id,
        name: req.userProfile?.nama,
        email: req.user.email
      }
    });
  } else {
    res.json({
      loggedIn: false
    });
  }
});

// 404 handler
router.use((req, res) => {
  res.status(404).render('404');
});

module.exports = router;
