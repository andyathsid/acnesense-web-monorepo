const { createClient } = require('@supabase/supabase-js');
const { Pool } = require('pg');
require('dotenv').config();

const supabaseUrl = process.env.SUPABASE_URL;
const supabaseAnonKey = process.env.SUPABASE_ANON_KEY;
const supabaseServiceKey = process.env.SUPABASE_SERVICE_ROLE_KEY;
const supabasePgConnectionString = process.env.SUPABASE_PG_CONNECTION_STRING;

if (!supabaseUrl || !supabaseAnonKey || !supabaseServiceKey) {
  throw new Error('Missing Supabase JS client environment variables');
}

if (!supabasePgConnectionString) {
  throw new Error('Missing Supabase PostgreSQL connection string environment variable (SUPABASE_PG_CONNECTION_STRING)');
}

// Client for regular operations
const supabase = createClient(supabaseUrl, supabaseAnonKey);

// Admin client for server-side operations
const supabaseAdmin = createClient(supabaseUrl, supabaseServiceKey, {
  auth: {
    autoRefreshToken: false,
    persistSession: false
  }
});

// PostgreSQL client pool for raw SQL queries
const pgPool = new Pool({
  connectionString: supabasePgConnectionString,
  ssl: {
    rejectUnauthorized: false
  }
});

// Test Supabase JS client connection
const testSupabaseConnection = async () => {
  try {
    const { data, error } = await supabase.from('profiles').select('count').limit(1);
    if (error) throw error;
    console.log('✅ Supabase JS client connection established');
  } catch (error) {
    console.error('❌ Supabase JS client connection failed:', error.message);
  }
};

// Test PostgreSQL connection
const testPgConnection = async () => {
  try {
    const client = await pgPool.connect();
    console.log('✅ PostgreSQL (node-postgres) connection established');
    client.release();
  } catch (error) {
    console.error('❌ PostgreSQL (node-postgres) connection failed:', error.message);
  }
};

// Function to execute raw SQL queries
const executeRawQuery = async (queryText, params = []) => {
  const client = await pgPool.connect();
  try {
    const res = await client.query(queryText, params);
    return res.rows;
  } finally {
    client.release();
  }
};

// Test connections on startup
testSupabaseConnection();
testPgConnection();

module.exports = {
  supabase,
  supabaseAdmin,
  pgPool,
  executeRawQuery
};
