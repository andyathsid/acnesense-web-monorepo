# Panduan Penggunaan Acne Sense

Selamat datang di proyek **Acne Sense**. Berikut adalah langkah-langkah untuk menjalankan aplikasi ini.

## Prerequisites

Pastikan Anda telah menginstal Node.js dan npm di sistem Anda.

## Langkah-langkah

1. **Instal Dependensi**
   Jalankan perintah berikut untuk menginstal dependensi yang dibutuhkan:
   ```bash
   npm install
   ```

2. **Impor Database**
   - Masukkan file database yang ada di dalam folder **database**.
   - Buat database baru dengan nama **acne_sense**.

3. **Jalankan Aplikasi**
   Setelah semua instalasi selesai, jalankan perintah berikut:
   ```bash
   npm run start
   ```

## Akun Demo

Berikut adalah akun yang dapat Anda gunakan untuk masuk:

- **Email:** user123@gmail.com
- **Password:** 123123

Selamat menggunakan aplikasi Acne Sense! Jika Anda memiliki pertanyaan, jangan ragu untuk menghubungi kami.

# AcneSense Web Application

A comprehensive web application for acne detection and analysis using AI technology, powered by Supabase.

## Features

- 🔐 Secure authentication with Supabase Auth
- 📷 Real-time acne detection using camera or image upload
- 📊 Detection history and analytics
- 🤖 AI-powered chatbot for skincare guidance
- 📱 Progressive Web App (PWA) support
- 💾 Cloud database with Supabase PostgreSQL

## Tech Stack

- **Frontend**: EJS, Tailwind CSS, JavaScript
- **Backend**: Node.js, Express.js
- **Database**: Supabase PostgreSQL
- **Authentication**: Supabase Auth
- **AI Integration**: Custom AI service
- **PWA**: Service Worker, Web App Manifest

## Prerequisites

- Node.js (v14 or higher)
- Supabase account and project
- AI detection service running on port 5000

## Installation

1. Clone the repository
```bash
git clone <repository-url>
cd acne-sense/dev/dev-upstream/web
```

2. Install dependencies
```bash
npm install
```

3. Set up environment variables
```bash
cp .env.example .env
```

Update `.env` with your Supabase credentials:
```
SUPABASE_URL=your_supabase_url
SUPABASE_ANON_KEY=your_supabase_anon_key
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key
JWT_SECRET=your_jwt_secret
```

4. Database Setup
- The application uses Supabase's extended auth.users table
- Tables are created automatically via Supabase migrations
- Required tables: profiles, riwayat, riwayat_detail

5. Start the application
```bash
# Development
npm run dev

# Production
npm start
```

## Database Schema

### profiles (extends auth.users)
- id (UUID, FK to auth.users.id)
- nama (TEXT)
- email (TEXT)
- tanggal_lahir (DATE)
- umur (INTEGER)
- status (TEXT)
- foto_profile (TEXT)
- jenis_kulit (TEXT)
- skin_tone (TEXT)

### riwayat
- id_riwayat (SERIAL, PRIMARY KEY)
- id_user (UUID, FK to profiles.id)
- judul_penyakit (TEXT)
- gambar (TEXT)
- overview (TEXT)
- recommendations (TEXT)
- skincare_tips (TEXT)
- important_notes (TEXT)
- created_at (TIMESTAMP)

### riwayat_detail
- id_riwayat_detail (SERIAL, PRIMARY KEY)
- id_riwayat (INTEGER, FK to riwayat.id_riwayat)
- acne_types (TEXT)
- jumlah_klasifikasi (INTEGER)
- gambar_detail (TEXT)

## API Endpoints

### Authentication
- `POST /register` - User registration
- `POST /login` - User login
- `POST /logout` - User logout

### Main Features
- `GET /dashboard` - User dashboard
- `GET /deteksi` - Detection page
- `GET /preview` - Image preview
- `GET /chatbot` - AI chatbot
- `GET /riwayat` - Detection history
- `GET /hasil/:id` - Detection results
- `POST /save-detection` - Save detection results

### API
- `GET /api/session-status` - Check login status

## Environment Variables

```
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your_anon_key
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key
JWT_SECRET=your_jwt_secret
PORT=3000
```

## Development

1. Start the AI service (port 5000)
2. Run the web application: `npm run dev`
3. Access the application at `http://localhost:3000`

## Security Features

- Supabase Auth for secure authentication
- Session-based authentication with secure cookies
- Input validation and sanitization
- CSRF protection
- SQL injection prevention through Supabase ORM

## PWA Features

- Offline functionality
- Install to home screen
- Service worker for caching
- Responsive design for all devices

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is licensed under the MIT License.
