const { supabaseAdmin } = require('../config/db');
const User = require('../models/User');

const requireAuth = async (req, res, next) => {
    try {
        // For session-based auth, check session first
        if (req.session.userId && req.session.accessToken) {
            // Verify the session token is still valid
            const { data: { user }, error } = await supabaseAdmin.auth.getUser(req.session.accessToken);
            
            if (error || !user || user.id !== req.session.userId) {
                req.session.destroy(() => {
                    return res.redirect('/login');
                });
                return;
            }

            // Get updated user profile
            try {
                const profile = await User.findById(user.id);
                if (!profile) {
                    req.session.destroy(() => {
                        return res.redirect('/login');
                    });
                    return;
                }

                // Update session with fresh data
                req.user = user;
                req.userProfile = profile;
                req.session.userEmail = user.email;
                req.session.userName = profile.nama;
                req.session.userPhoto = profile.foto_profile;
                
                next();
            } catch (profileError) {
                console.error('Profile fetch error:', profileError);
                req.session.destroy(() => {
                    return res.redirect('/login');
                });
            }
        } else {
            return res.redirect('/login');
        }
    } catch (error) {
        console.error('Auth middleware error:', error);
        req.session.destroy(() => {
            res.redirect('/login');
        });
    }
};

const requireGuest = (req, res, next) => {
    if (req.session.userId) {
        return res.redirect('/dashboard');
    }
    next();
};

module.exports = { requireAuth, requireGuest };