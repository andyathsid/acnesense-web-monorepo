const { executeRawQuery } = require('./config/db');

async function testCrudOperations() {
  console.log('🧪 Starting CRUD operations test with raw SQL...\n');

  try {
    // 1. CREATE TABLE - Create a test table
    console.log('1. Creating test table...');
    await executeRawQuery(`
      CREATE TABLE IF NOT EXISTS test_items (
        id SERIAL PRIMARY KEY,
        name VARCHAR(255) NOT NULL,
        description TEXT,
        price DECIMAL(10, 2),
        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
      )
    `);
    console.log('✅ Table created successfully\n');

    // 2. CREATE (INSERT) - Add some test data
    console.log('2. Inserting test data...');
    const insertResult1 = await executeRawQuery(`
      INSERT INTO test_items (name, description, price) 
      VALUES ($1, $2, $3) 
      RETURNING *
    `, ['Laptop', 'High-performance gaming laptop', 1299.99]);
    
    const insertResult2 = await executeRawQuery(`
      INSERT INTO test_items (name, description, price) 
      VALUES ($1, $2, $3) 
      RETURNING *
    `, ['Mouse', 'Wireless optical mouse', 29.99]);

    console.log('✅ Inserted items:');
    console.log('  -', insertResult1[0]);
    console.log('  -', insertResult2[0]);
    console.log();

    // 3. READ (SELECT) - Retrieve all items
    console.log('3. Reading all items...');
    const allItems = await executeRawQuery('SELECT * FROM test_items ORDER BY id');
    console.log('✅ All items in table:');
    allItems.forEach(item => {
      console.log(`  - ID: ${item.id}, Name: ${item.name}, Price: $${item.price}`);
    });
    console.log();

    // 4. READ with WHERE clause - Get specific item
    console.log('4. Reading specific item (Laptop)...');
    const laptopItem = await executeRawQuery(
      'SELECT * FROM test_items WHERE name = $1',
      ['Laptop']
    );
    console.log('✅ Found item:', laptopItem[0]);
    console.log();

    // 5. UPDATE - Modify an existing item
    console.log('5. Updating item price...');
    const updateResult = await executeRawQuery(`
      UPDATE test_items 
      SET price = $1, updated_at = NOW() 
      WHERE name = $2 
      RETURNING *
    `, [1199.99, 'Laptop']);
    console.log('✅ Updated item:', updateResult[0]);
    console.log();

    // 6. DELETE - Remove an item
    console.log('6. Deleting an item...');
    const deleteResult = await executeRawQuery(`
      DELETE FROM test_items 
      WHERE name = $1 
      RETURNING *
    `, ['Mouse']);
    console.log('✅ Deleted item:', deleteResult[0]);
    console.log();

    // 7. READ again to verify changes
    console.log('7. Final state of table...');
    const finalItems = await executeRawQuery('SELECT * FROM test_items ORDER BY id');
    console.log('✅ Remaining items:');
    finalItems.forEach(item => {
      console.log(`  - ID: ${item.id}, Name: ${item.name}, Price: $${item.price}, Updated: ${item.updated_at}`);
    });
    console.log();

    // 8. Advanced query - Using aggregate functions
    console.log('8. Running aggregate query...');
    const stats = await executeRawQuery(`
      SELECT 
        COUNT(*) as total_items,
        AVG(price) as average_price,
        MAX(price) as max_price,
        MIN(price) as min_price
      FROM test_items
    `);
    console.log('✅ Table statistics:', stats[0]);
    console.log();

    // 9. Clean up - Drop the test table (optional)
    console.log('9. Cleaning up test table...');
    await executeRawQuery('DROP TABLE IF EXISTS test_items');
    console.log('✅ Test table dropped\n');

    console.log('🎉 All CRUD operations completed successfully!');

  } catch (error) {
    console.error('❌ Error during CRUD operations:', error);
    
    // Cleanup in case of error
    try {
      await executeRawQuery('DROP TABLE IF EXISTS test_items');
      console.log('🧹 Cleaned up test table after error');
    } catch (cleanupError) {
      console.error('Failed to cleanup:', cleanupError);
    }
  }
}

// Run the test
testCrudOperations()
  .then(() => {
    console.log('\n✨ Test completed. You can now use executeRawQuery() in your application!');
    process.exit(0);
  })
  .catch((error) => {
    console.error('Fatal error:', error);
    process.exit(1);
  });
