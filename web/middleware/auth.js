const { supabase } = require('../config/db');
const User = require('../models/User');

const requireAuth = async (req, res, next) => {
    try {
        const token = req.headers.authorization?.replace('Bearer ', '') || 
                      req.cookies?.access_token;

        if (!token) {
            return res.redirect('/login');
        }

        // Verify the token with Supabase
        const { data: { user }, error } = await supabase.auth.getUser(token);
        
        if (error || !user) {
            // Clear invalid token
            res.clearCookie('access_token');
            return res.redirect('/login');
        }

        // Get updated user profile
        try {
            const profile = await User.findById(user.id);
            if (!profile) {
                res.clearCookie('access_token');
                return res.redirect('/login');
            }

            // Add user data to request
            req.user = user;
            req.userProfile = profile;
            req.accessToken = token;
            
            next();
        } catch (profileError) {
            console.error('Profile fetch error:', profileError);
            res.clearCookie('access_token');
            return res.redirect('/login');
        }
    } catch (error) {
        console.error('Auth middleware error:', error);
        res.clearCookie('access_token');
        res.redirect('/login');
    }
};

const requireGuest = (req, res, next) => {
    const token = req.headers.authorization?.replace('Bearer ', '') || 
                  req.cookies?.access_token;
    
    if (token && req.user) {
        return res.redirect('/dashboard');
    }
    next();
};

module.exports = { requireAuth, requireGuest };