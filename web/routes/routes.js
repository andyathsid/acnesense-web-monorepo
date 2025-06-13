const express = require('express');
const { requireAuth, requireGuest } = require('../middleware/auth');
const User = require('../models/User');
const Riwayat = require('../models/Riwayat');
const RiwayatDetail = require('../models/RiwayatDetail');
const { marked } = require('marked');
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

// Edit profile route in routes.js
router.get('/edit-profile', requireAuth, async (req, res) => {
    try {
        // Mengambil ID pengguna yang sedang login
        const userId = req.user.id; // Mengambil ID dari objek pengguna yang sudah diotentikasi
        
        // Mendapatkan data pengguna dari database berdasarkan ID
        const user = await User.findById(userId);

        // Cek apakah pengguna ditemukan
        if (!user) {
            return res.redirect('/login'); // Redirect jika pengguna tidak ditemukan
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
// Route to handle profile update
router.post('/edit-profile', async (req, res) => {
    const { id, nama, email, tanggal_lahir, skinTone, skinType } = req.body;

    // Cek dan log untuk memastikan ID dan data yang diterima
    console.log('Received data:', { id, nama, email, tanggal_lahir, skinTone, skinType });

    try {
        const userProfile = await User.updateProfile(id, {
            nama,
            email,
            tanggal_lahir,
            skin_tone: skinTone,
            jenis_kulit: skinType
        });

        res.json({ success: true, message: 'Profile updated successfully!', user: userProfile });
    } catch (error) {
        console.error('Error updating profile:', error);
        res.status(500).json({ success: false, message: error.message });
    }
});
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
// Login route
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
        const { user, session, error } = await User.signIn(email, password);

        if (error || !user || !session) {
            console.error('Sign in error:', error); // Debugging log
            return res.json({
                success: false,
                message: 'Email atau password salah!'
            });
        }

        // Get user profile
        const profile = await User.findById(user.id);
        if (!profile) {
            console.error('Profile not found for user ID:', user.id); // Debugging log
            return res.json({
                success: false,
                message: 'Profil pengguna tidak ditemukan!'
            });
        }

        // Set HTTP-only cookie for the token
        res.cookie('access_token', session.access_token, {
            httpOnly: true,
            secure: process.env.NODE_ENV === 'production',
            sameSite: 'strict',
            maxAge: 24 * 60 * 60 * 1000 // 24 hours
        });

        console.log(`User logged in: ${user.email} at ${new Date()}`);

        // Send user data and redirect URL based on status
        return res.json({
            success: true,
            message: 'Login berhasil!',
            user: { // Send user data
                id: user.id,
                email: user.email,
                name: profile.nama,
                status: profile.status, // Add status here
                age: profile.umur // If necessary
            },
            redirectUrl: profile.status === 'baru' ? '/pengguna-baru' : '/dashboard'
        });

    } catch (error) {
        console.error('Login error:', error); // Debugging log
        res.json({
            success: false,
            message: 'Gagal memproses permintaan login.'
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

router.get('/pengguna-baru', requireAuth, async (req, res) => {
    try {
        // Fetch the user's profile
        const userProfile = await User.findById(req.user.id);

        // Check if there is existing data for jenis_kulit and skin_tone
        if (userProfile && userProfile.jenis_kulit && userProfile.skin_tone) {
            // Redirect to dashboard if data exists
            return res.redirect('/dashboard');
        }

        // Render the pengguna-baru view
        res.render('pengguna-baru', {
            user: req.user // Pass the user information to the view if needed
        });
    } catch (error) {
        console.error('Error fetching user profile:', error);
        res.redirect('/login'); // Redirect in case of an error
    }
});
// Add this route to handle skin info updates
router.post('/update-skin-info', requireAuth, async (req, res) => {
    console.log('Incoming request body:', req.body); // Log the incoming request body
    const { skinType, skinTone } = req.body; // This should now correctly read the values
    console.log('Update skin info:', { skinType, skinTone });

    // Validate the input
    if (!skinType || !skinTone) {
        return res.json({
            success: false,
            message: 'Semua field harus diisi!'
        });
    }

    // Assume update function is implemented correctly
    const updates = {
        jenis_kulit: skinType,
        skin_tone: skinTone,
        status: 'lama' // Update status to 'lama'
    };

    try {
        const updatedProfile = await User.updateProfile(req.user.id, updates);

        if (!updatedProfile) {
            return res.json({
                success: false,
                message: 'Gagal memperbarui informasi pengguna!'
            });
        }

        res.json({
            success: true,
            message: 'Informasi berhasil diperbarui!',
        });
    } catch (error) {
        console.error('Update skin info error:', error);
        res.json({
            success: false,
            message: 'Terjadi kesalahan saat memperbarui informasi!',
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
    res.render('preview', { 
      user, 
      imageUrl,
      API_BASE_URL: process.env.API_BASE_URL || 'http://localhost:5000'
    });
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

    // Convert markdown to HTML for display
    const overviewHtml = riwayatData.overview ? marked.parse(riwayatData.overview) : '';
    const recommendationsHtml = riwayatData.recommendations ? marked.parse(riwayatData.recommendations) : '';
    const skincareTipsHtml = riwayatData.skincare_tips ? marked.parse(riwayatData.skincare_tips) : '';
    const importantNotesHtml = riwayatData.important_notes ? marked.parse(riwayatData.important_notes) : '';

    res.render('hasil', {
      user,
      jumlah_deteksi: riwayatDetails.length,
      klas_deteksi: uniqueAcneTypes,
      image_asli: riwayatData.gambar,
      image_klas: imageKlas,
      overview: overviewHtml,
      recommendations: recommendationsHtml,
      skincare_tips: skincareTipsHtml,
      important_notes: importantNotesHtml
    });
  } catch (error) {
    console.error('Hasil error:', error);
    res.redirect('/riwayat');
  }
});

router.post('/save-detection', requireAuth, async (req, res) => {
  try {
    const detectionData = req.body;

    // Check for required data - now expecting recommendation_sections instead of recommendation
    if (!detectionData.acne_types || !detectionData.classification_results || 
        !detectionData.detection_classes || !detectionData.captured_image) {
      return res.status(400).json({ success: false, message: 'Data tidak lengkap.' });
    }

    // Check for recommendation_sections 
    if (!detectionData.recommendation_sections) {
      return res.status(400).json({ success: false, message: 'Data rekomendasi tidak tersedia.' });
    }

    // Extract sections from structured format
    const sections = detectionData.recommendation_sections;
    const overview = sections.overview ? `${sections.overview}` : '';
    const recommendations = sections.recommendations ? `${sections.recommendations}` : '';
    const skincareTips = sections.skincare_tips ? `${sections.skincare_tips}` : '';
    const importantNotes = sections.important_notes ? `${sections.important_notes}` : '';
    
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

router.get('/forgot-password', requireGuest, (req, res) => {
  res.render('forgot/forgot1'); // Adjust the path based on your views directory structure
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
