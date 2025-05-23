const mysql = require('mysql2');

const connection = mysql.createConnection({
  host: 'localhost',
  user: 'root',
  password: '', // Ganti dengan password MySQL Anda
  database: 'acne_sense'
});

connection.connect((err) => {
  if (err) {
    console.error('Error koneksi ke database:', err);
    return;
  }
  console.log('Terhubung ke database MySQL');
});

module.exports = connection;