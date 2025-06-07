const { supabaseAdmin } = require('../config/db');

class Riwayat {
    static async create(userId, riwayatData) {
        try {
            const { data, error } = await supabaseAdmin
                .from('riwayat')
                .insert({
                    id_user: userId,
                    ...riwayatData,
                    created_at: new Date().toISOString()
                })
                .select()
                .single();

            if (error) {
                throw new Error(error.message);
            }

            return data;
        } catch (error) {
            console.error('Riwayat creation error:', error);
            throw error;
        }
    }

    static async findByUserId(userId, limit = null) {
        try {
            let query = supabaseAdmin
                .from('riwayat')
                .select('*')
                .eq('id_user', userId)
                .order('created_at', { ascending: false });

            if (limit) {
                query = query.limit(limit);
            }

            const { data, error } = await query;

            if (error) {
                throw new Error(error.message);
            }

            return data || [];
        } catch (error) {
            console.error('Find riwayat by user error:', error);
            throw error;
        }
    }

    static async findById(id) {
        try {
            const { data, error } = await supabaseAdmin
                .from('riwayat')
                .select(`
                    *,
                    riwayat_detail (*)
                `)
                .eq('id_riwayat', id)
                .single();

            if (error && error.code !== 'PGRST116') {
                throw new Error(error.message);
            }

            return data;
        } catch (error) {
            console.error('Find riwayat by ID error:', error);
            throw error;
        }
    }

    static async update(id, updates) {
        try {
            const { data, error } = await supabaseAdmin
                .from('riwayat')
                .update(updates)
                .eq('id_riwayat', id)
                .select()
                .single();

            if (error) {
                throw new Error(error.message);
            }

            return data;
        } catch (error) {
            console.error('Riwayat update error:', error);
            throw error;
        }
    }

    static async delete(id) {
        try {
            const { error } = await supabaseAdmin
                .from('riwayat')
                .delete()
                .eq('id_riwayat', id);

            if (error) {
                throw new Error(error.message);
            }
        } catch (error) {
            console.error('Riwayat delete error:', error);
            throw error;
        }
    }
}

module.exports = Riwayat;