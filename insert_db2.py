"""
MongoDB Bulk Insert Script - REPLACE MODE
Efficiently imports 100k+ Indian recipes into MongoDB
AUTOMATICALLY REPLACES existing database
"""

import json
from pymongo import MongoClient, ASCENDING, DESCENDING
from pymongo.errors import BulkWriteError
from datetime import datetime
import time
import os

# ==========================================
# CONFIGURATION
# ==========================================

# MongoDB connection
MONGODB_URI = os.getenv('MONGODB_URI', 'mongodb://localhost:27017/')
DATABASE_NAME = 'recipe_analyzer'
COLLECTION_NAME = 'recipes'

# Import settings
JSON_FILE = 'recipes.json'
BATCH_SIZE = 1000  # Insert 1000 documents at a time

# ==========================================
# MONGODB CONNECTION & SETUP
# ==========================================

def connect_mongodb():
    """Connect to MongoDB and return database instance"""
    print("🔌 Connecting to MongoDB...")
    
    client = MongoClient(
        MONGODB_URI,
        serverSelectionTimeoutMS=5000,
        maxPoolSize=50
    )
    
    # Test connection
    try:
        client.admin.command('ping')
        print("✅ MongoDB connection successful!")
    except Exception as e:
        print(f"❌ MongoDB connection failed: {e}")
        raise
    
    db = client[DATABASE_NAME]
    collection = db[COLLECTION_NAME]
    
    return client, db, collection


def drop_and_recreate_collection(collection):
    """
    Drop existing collection and recreate it
    This ensures a clean slate for the new data
    """
    collection_name = collection.name
    db = collection.database
    
    existing_count = collection.count_documents({})
    
    if existing_count > 0:
        print(f"\n🗑️  Found {existing_count:,} existing documents in '{collection_name}'")
        print("🔄 Dropping collection to replace with new data...")
        
        # Drop the collection
        collection.drop()
        print(f"✅ Collection '{collection_name}' dropped successfully!")
        
        # Recreate the collection (MongoDB does this automatically on first insert)
        # But we'll get a fresh reference
        collection = db[collection_name]
        print(f"✅ Collection '{collection_name}' recreated!")
    else:
        print(f"\n📝 Collection '{collection_name}' is empty. Proceeding with insert...")
    
    return collection


def create_indexes(collection):
    """
    Create performance indexes for 100k+ documents
    Optimized for Indian recipe queries
    """
    print("\n📊 Creating performance indexes...")
    
    try:
        # 1. Compound index for sorting by date and title
        collection.create_index([
            ('created_at', DESCENDING),
            ('title', ASCENDING)
        ], name='created_at_title_idx')
        print("  ✅ Created: created_at + title index")
        
        # 2. Text index for full-text search (Indian dishes)
        collection.create_index([
            ('title', 'text'),
            ('ingredients', 'text'),
            ('cuisine', 'text'),
            ('tags', 'text')
        ], name='text_search_idx', 
           default_language='english',
           weights={'title': 10, 'ingredients': 5, 'cuisine': 3, 'tags': 2})
        print("  ✅ Created: text search index")
        
        # 3. Single field indexes for filtering
        collection.create_index('cuisine', name='cuisine_idx')
        print("  ✅ Created: cuisine index")
        
        collection.create_index('difficulty', name='difficulty_idx')
        print("  ✅ Created: difficulty index")
        
        collection.create_index('is_veg', name='is_veg_idx')
        print("  ✅ Created: is_veg index")
        
        collection.create_index('calories', name='calories_idx')
        print("  ✅ Created: calories index")
        
        collection.create_index('rating', name='rating_idx')
        print("  ✅ Created: rating index")
        
        collection.create_index('estimated_time', name='time_idx')
        print("  ✅ Created: estimated_time index")
        
        # 4. Compound index for common filter combinations
        collection.create_index([
            ('cuisine', ASCENDING),
            ('is_veg', ASCENDING),
            ('difficulty', ASCENDING)
        ], name='filter_combo_idx')
        print("  ✅ Created: cuisine + is_veg + difficulty index")
        
        # 5. Compound index for vegetarian + calorie searches
        collection.create_index([
            ('is_veg', ASCENDING),
            ('calories', ASCENDING)
        ], name='veg_calories_idx')
        print("  ✅ Created: is_veg + calories index")
        
        # 6. Compound index for quick meal searches
        collection.create_index([
            ('estimated_time', ASCENDING),
            ('difficulty', ASCENDING)
        ], name='time_difficulty_idx')
        print("  ✅ Created: estimated_time + difficulty index")
        
        print("✅ All indexes created successfully!")
        
    except Exception as e:
        print(f"⚠️ Warning: Could not create indexes: {e}")


# ==========================================
# BULK INSERT FUNCTIONS
# ==========================================

def read_json_lines(filename, batch_size):
    """
    Generator that yields batches of documents from JSON Lines file
    Memory-efficient: doesn't load entire file at once
    """
    batch = []
    
    with open(filename, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                document = json.loads(line)
                
                # Convert ISO date string to datetime object
                if 'created_at' in document:
                    document['created_at'] = datetime.fromisoformat(document['created_at'])
                
                batch.append(document)
                
                if len(batch) >= batch_size:
                    yield batch
                    batch = []
        
        # Yield remaining documents
        if batch:
            yield batch


def bulk_insert_recipes(collection, json_file, batch_size=BATCH_SIZE):
    """
    Bulk insert recipes with progress tracking
    Uses ordered=False for maximum performance
    """
    print(f"\n🔥 Starting bulk insert from {json_file}...")
    print(f"📦 Batch size: {batch_size:,}")
    
    total_inserted = 0
    total_batches = 0
    start_time = time.time()
    
    try:
        for batch_num, batch in enumerate(read_json_lines(json_file, batch_size), 1):
            try:
                # Use unordered bulk insert for maximum performance
                result = collection.insert_many(batch, ordered=False)
                
                inserted_count = len(result.inserted_ids)
                total_inserted += inserted_count
                total_batches = batch_num
                
                # Progress update every 10 batches
                if batch_num % 10 == 0:
                    elapsed = time.time() - start_time
                    rate = total_inserted / elapsed if elapsed > 0 else 0
                    print(f"  ⏳ Batch {batch_num}: {total_inserted:,} documents inserted ({rate:.0f} docs/sec)")
            
            except BulkWriteError as e:
                # Handle partial failures
                inserted_count = e.details.get('nInserted', 0)
                total_inserted += inserted_count
                print(f"  ⚠️ Batch {batch_num}: {inserted_count} inserted, {len(e.details.get('writeErrors', []))} failed")
        
        elapsed_time = time.time() - start_time
        avg_rate = total_inserted / elapsed_time if elapsed_time > 0 else 0
        
        print(f"\n✅ Bulk insert complete!")
        print(f"  📊 Total documents inserted: {total_inserted:,}")
        print(f"  📦 Total batches: {total_batches:,}")
        print(f"  ⏱️  Time taken: {elapsed_time:.2f} seconds")
        print(f"  ⚡ Average rate: {avg_rate:.0f} documents/second")
        
        return total_inserted
    
    except FileNotFoundError:
        print(f"❌ Error: File '{json_file}' not found!")
        print(f"   Please run the Indian recipe generator first")
        return 0
    except Exception as e:
        print(f"❌ Bulk insert error: {e}")
        return total_inserted


# ==========================================
# VERIFICATION & STATISTICS
# ==========================================

def verify_import(collection, expected_count):
    """Verify that import was successful"""
    print("\n🔍 Verifying import...")
    
    actual_count = collection.count_documents({})
    
    print(f"  Expected: {expected_count:,}")
    print(f"  Actual:   {actual_count:,}")
    
    if actual_count >= expected_count:
        print("  ✅ Import verified successfully!")
        return True
    else:
        print(f"  ⚠️ Warning: {expected_count - actual_count:,} documents missing")
        return False


def show_statistics(collection):
    """Display collection statistics for Indian recipes"""
    print("\n📊 Collection Statistics:")
    
    total = collection.count_documents({})
    print(f"  Total documents: {total:,}")
    
    # Cuisine distribution
    print("\n  🍛 Cuisine Distribution:")
    pipeline = [
        {'$group': {'_id': '$cuisine', 'count': {'$sum': 1}}},
        {'$sort': {'count': -1}}
    ]
    for doc in collection.aggregate(pipeline):
        percentage = (doc['count'] / total) * 100
        print(f"    {doc['_id']}: {doc['count']:,} ({percentage:.1f}%)")
    
    # Difficulty distribution
    print("\n  🎯 Difficulty Distribution:")
    pipeline = [
        {'$group': {'_id': '$difficulty', 'count': {'$sum': 1}}},
        {'$sort': {'count': -1}}
    ]
    for doc in collection.aggregate(pipeline):
        percentage = (doc['count'] / total) * 100
        print(f"    {doc['_id']}: {doc['count']:,} ({percentage:.1f}%)")
    
    # Vegetarian stats
    veg_count = collection.count_documents({'is_veg': True})
    non_veg_count = collection.count_documents({'is_veg': False})
    print(f"\n  🥗 Vegetarian: {veg_count:,} ({(veg_count/total)*100:.1f}%)")
    print(f"  🍖 Non-Vegetarian: {non_veg_count:,} ({(non_veg_count/total)*100:.1f}%)")
    
    # Average calories and time
    pipeline = [
        {
            '$group': {
                '_id': None,
                'avg_calories': {'$avg': '$calories'},
                'avg_time': {'$avg': '$estimated_time'},
                'avg_rating': {'$avg': '$rating'}
            }
        }
    ]
    result = list(collection.aggregate(pipeline))
    if result:
        stats = result[0]
        print(f"\n  📈 Averages:")
        print(f"    Calories: {stats['avg_calories']:.0f} kcal")
        print(f"    Cooking Time: {stats['avg_time']:.0f} minutes")
        print(f"    Rating: {stats['avg_rating']:.1f}/5.0")
    
    # Top 10 most common ingredients
    print("\n  🥘 Top 10 Most Common Ingredients:")
    pipeline = [
        {'$unwind': '$ingredients'},
        {'$group': {'_id': '$ingredients', 'count': {'$sum': 1}}},
        {'$sort': {'count': -1}},
        {'$limit': 10}
    ]
    for i, doc in enumerate(collection.aggregate(pipeline), 1):
        print(f"    {i}. {doc['_id']}: {doc['count']:,} recipes")


def sample_queries(collection):
    """Run sample queries to test performance"""
    print("\n🔍 Testing Query Performance:")
    
    # Query 1: Find all North Indian vegetarian recipes
    start = time.time()
    count = collection.count_documents({'cuisine': 'North Indian', 'is_veg': True})
    elapsed = (time.time() - start) * 1000
    print(f"  Query 1 (North Indian Veg): {count:,} results in {elapsed:.2f}ms")
    
    # Query 2: Find beginner recipes under 30 minutes
    start = time.time()
    count = collection.count_documents({'difficulty': 'Beginner', 'estimated_time': {'$lt': 30}})
    elapsed = (time.time() - start) * 1000
    print(f"  Query 2 (Quick Beginner): {count:,} results in {elapsed:.2f}ms")
    
    # Query 3: Text search for "paneer"
    start = time.time()
    count = collection.count_documents({'$text': {'$search': 'paneer'}})
    elapsed = (time.time() - start) * 1000
    print(f"  Query 3 (Paneer Dishes): {count:,} results in {elapsed:.2f}ms")
    
    # Query 4: Low-calorie vegetarian recipes
    start = time.time()
    count = collection.count_documents({'calories': {'$lt': 400}, 'is_veg': True})
    elapsed = (time.time() - start) * 1000
    print(f"  Query 4 (Low-cal Veg): {count:,} results in {elapsed:.2f}ms")
    
    # Query 5: South Indian breakfast items
    start = time.time()
    count = collection.count_documents({
        'cuisine': 'South Indian',
        'tags': 'breakfast'
    })
    elapsed = (time.time() - start) * 1000
    print(f"  Query 5 (South Indian Breakfast): {count:,} results in {elapsed:.2f}ms")
    
    # Sample documents
    print("\n  📋 Sample Documents (3 random recipes):")
    for i, doc in enumerate(collection.aggregate([{'$sample': {'size': 3}}]), 1):
        print(f"\n    {i}. {doc['title']}")
        print(f"       Cuisine: {doc['cuisine']} | Veg: {doc['is_veg']} | {doc['estimated_time']}min")
        print(f"       Ingredients: {', '.join(doc['ingredients'][:5])}...")


# ==========================================
# MAIN EXECUTION
# ==========================================

def main():
    """Main execution function - REPLACE MODE"""
    print("=" * 60)
    print("🗄️  MongoDB Bulk Insert - Indian Recipe Dataset")
    print("🔄 MODE: REPLACE EXISTING DATABASE")
    print("=" * 60)
    
    # Check if JSON file exists
    if not os.path.exists(JSON_FILE):
        print(f"\n❌ Error: {JSON_FILE} not found!")
        print("   Please run the Indian recipe generator first:")
        print("   python generator.py")
        return
    
    # Connect to MongoDB
    client, db, collection = connect_mongodb()
    
    # AUTOMATICALLY drop and recreate collection (no user prompt)
    print("\n⚠️  This will REPLACE all existing data in the database!")
    print(f"   Database: {DATABASE_NAME}")
    print(f"   Collection: {COLLECTION_NAME}")
    
    collection = drop_and_recreate_collection(collection)
    
    # Create indexes BEFORE inserting data for better performance
    create_indexes(collection)
    
    # Bulk insert data
    total_inserted = bulk_insert_recipes(collection, JSON_FILE, BATCH_SIZE)
    
    if total_inserted > 0:
        # Verify import
        verify_import(collection, total_inserted)
        
        # Show statistics
        show_statistics(collection)
        
        # Test query performance
        sample_queries(collection)
    
    # Close connection
    client.close()
    
    print("\n" + "=" * 60)
    print("✅ Database replacement complete!")
    print(f"   Database: {DATABASE_NAME}")
    print(f"   Collection: {COLLECTION_NAME}")
    print(f"   Total Records: {total_inserted:,}")
    print("=" * 60)


if __name__ == '__main__':
    main()