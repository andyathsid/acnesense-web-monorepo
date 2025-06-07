const { supabaseAdmin } = require('../config/db');

class RiwayatDetail {
    static async create(detailData) {
        try {
            const { data, error } = await supabaseAdmin
                .from('riwayat_detail')
                .insert(detailData)
                .select();

            if (error) {
                throw new Error(error.message);
            }

            return data;
        } catch (error) {
            console.error('RiwayatDetail creation error:', error);
            throw error;
        }
    }

    static async createMultiple(detailsArray) {
        try {
            const { data, error } = await supabaseAdmin
                .from('riwayat_detail')
                .insert(detailsArray)
                .select();

            if (error) {
                throw new Error(error.message);
            }

            return data;
        } catch (error) {
            console.error('RiwayatDetail multiple creation error:', error);
            throw error;
        }
    }

    static async findByRiwayatId(riwayatId) {
        try {
            const { data, error } = await supabaseAdmin
                .from('riwayat_detail')
                .select('*')
                .eq('id_riwayat', riwayatId);

            if (error) {
                throw new Error(error.message);
            }

            return data || [];
        } catch (error) {
            console.error('Find riwayat detail error:', error);
            throw error;
        }
    }

    static async delete(id) {
        try {
            const { error } = await supabaseAdmin
                .from('riwayat_detail')
                .delete()
                .eq('id_riwayat_detail', id);

            if (error) {
                throw new Error(error.message);
            }
        } catch (error) {
            console.error('RiwayatDetail delete error:', error);
            throw error;
        }
    }
}

module.exports = RiwayatDetail;