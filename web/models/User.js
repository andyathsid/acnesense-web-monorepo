const { supabase, supabaseAdmin } = require('../config/db');

class User {
    static async create(userData) {
        const { nama, email, password, tanggal_lahir } = userData;
        
        // Calculate age
        const birthDate = new Date(tanggal_lahir);
        const today = new Date();
        let age = today.getFullYear() - birthDate.getFullYear();
        const monthDiff = today.getMonth() - birthDate.getMonth();
        if (monthDiff < 0 || (monthDiff === 0 && today.getDate() < birthDate.getDate())) {
            age--;
        }

        try {
            // Create auth user
            const { data: authData, error: authError } = await supabaseAdmin.auth.admin.createUser({
                email,
                password,
                user_metadata: { nama },
                email_confirm: true
            });

            if (authError) {
                throw new Error(authError.message);
            }

            // Update profile with additional data
            const { data: profileData, error: profileError } = await supabaseAdmin
                .from('profiles')
                .update({
                    nama,
                    email,
                    tanggal_lahir,
                    umur: age,
                    status: 'baru',
                    foto_profile: '/image/foto_profile/default.png'
                })
                .eq('id', authData.user.id)
                .select()
                .single();

            if (profileError) {
                throw new Error(profileError.message);
            }

            return { user: authData.user, profile: profileData };
        } catch (error) {
            console.error('User creation error:', error);
            throw error;
        }
    }

    static async findByEmail(email) {
        try {
            const { data, error } = await supabaseAdmin
                .from('profiles')
                .select('*')
                .eq('email', email.toLowerCase().trim())
                .single();

            if (error && error.code !== 'PGRST116') {
                throw new Error(error.message);
            }

            return data;
        } catch (error) {
            console.error('Find by email error:', error);
            return null;
        }
    }

    static async findById(id) {
        try {
            const { data, error } = await supabaseAdmin
                .from('profiles')
                .select('*')
                .eq('id', id)
                .single();

            if (error && error.code !== 'PGRST116') {
                throw new Error(error.message);
            }

            return data;
        } catch (error) {
            console.error('Find by ID error:', error);
            return null;
        }
    }

static async updateProfile(id, updates) {
    try {
        const { data, error } = await supabaseAdmin
            .from('profiles')
            .update(updates)
            .eq('id', id)
            .select(); // Hanya gunakan .select() tanpa .single()
        
        // Cek apakah ada error
        if (error) {
            throw new Error(error.message);
        }

        // Periksa apakah tidak ada baris yang ditemukan
        if (!data || data.length === 0) {
            throw new Error('No profile found with the given ID.');
        }

        // Mengembalikan objek profil yang diperbarui (data[0] karena mengembalikan array)
        return data[0]; // Kembali hanya objek pertama
    } catch (error) {
        console.error('Profile update error:', error);
        throw error; // Mengoper error ke lapisan atas
    }
}

    static async signIn(email, password) {
        try {
            const { data, error } = await supabase.auth.signInWithPassword({
                email: email.toLowerCase().trim(),
                password
            });

            if (error) {
                throw new Error(error.message);
            }

            return data;
        } catch (error) {
            console.error('Sign in error:', error);
            throw error;
        }
    }

    static async signOut() {
        try {
            const { error } = await supabase.auth.signOut();
            if (error) {
                throw new Error(error.message);
            }
        } catch (error) {
            console.error('Sign out error:', error);
            throw error;
        }
    }

    static async refreshSession(refreshToken) {
        try {
            const { data, error } = await supabase.auth.refreshSession({
                refresh_token: refreshToken
            });
            
            if (error) {
                throw new Error(error.message);
            }
            
            return data;
        } catch (error) {
            console.error('Refresh session error:', error);
            throw error;
        }
    }

    static async verifyToken(token) {
        try {
            const { data: { user }, error } = await supabase.auth.getUser(token);
            
            if (error) {
                throw new Error(error.message);
            }
            
            return user;
        } catch (error) {
            console.error('Token verification error:', error);
            return null;
        }
    }

    static async verifyPassword(email, password) {
        try {
            const { data, error } = await supabase.auth.signInWithPassword({
                email: email.toLowerCase().trim(),
                password
            });

            if (error) {
                return false;
            }

            // Sign out immediately after verification
            await supabase.auth.signOut();
            return true;
        } catch (error) {
            console.error('Password verification error:', error);
            return false;
        }
    }
    static async updateProfile(id, updates) {
    try {
        const { data, error } = await supabaseAdmin
            .from('profiles')
            .update(updates)
            .eq('id', id)
            .select()
            .single();

        if (error) {
            throw new Error(error.message);
        }

        return data;
    } catch (error) {
        console.error('Profile update error:', error);
        throw error;
    }
}
}

module.exports = User;