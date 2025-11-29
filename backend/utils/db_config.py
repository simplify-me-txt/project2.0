"""
MongoDB Database Configuration - FIXED ObjectId Serialization
Handles recipes with fields: title, ingredients, calories, steps, estimated_time, difficulty, cuisine
Properly converts ObjectId to string for JSON compatibility
"""
from pymongo import MongoClient, ASCENDING, DESCENDING
from pymongo.errors import ConnectionFailure, OperationFailure
from bson import ObjectId
import os


class RecipeDatabase:
    """MongoDB manager for recipe storage and retrieval"""
    
    def __init__(self):
        """Initialize MongoDB connection to LOCAL database"""
        self.mongo_uri = os.getenv('MONGODB_URI', 'mongodb://localhost:27017/')
        self.db_name = 'recipe_analyzer'
        self.collection_name = 'recipes'
        
        try:
            # Connect to MongoDB
            self.client = MongoClient(
                self.mongo_uri,
                serverSelectionTimeoutMS=5000,
                connectTimeoutMS=5000,
                maxPoolSize=50
            )
            
            # Test connection
            self.client.admin.command('ping')
            
            # Get database and collection
            self.db = self.client[self.db_name]
            self.collection = self.db[self.collection_name]
            
            # Check indexes
            self._check_indexes()
            
            # Get stats
            total_docs = self.collection.count_documents({})
            
            print("=" * 60)
            print("✅ MongoDB Connected Successfully")
            print(f"📊 Database: {self.db_name}")
            print(f"🍽️ Collection: {self.collection_name}")
            print(f"📈 Total Recipes: {total_docs:,}")
            print("=" * 60)
            
        except ConnectionFailure as e:
            print(f"❌ MongoDB connection failed: {e}")
            print("💡 Make sure MongoDB is running: mongod")
            self.client = None
            self.db = None
            self.collection = None
        except Exception as e:
            print(f"❌ Database initialization error: {e}")
            self.client = None
            self.db = None
            self.collection = None
    
    def _check_indexes(self):
        """Check existing indexes - don't create new ones to avoid conflicts"""
        if self.collection is None:
            return
        
        try:
            existing_indexes = list(self.collection.list_indexes())
            print(f"🔑 Found {len(existing_indexes)} existing indexes:")
            for idx in existing_indexes:
                print(f"   - {idx.get('name', 'unnamed')}")
            
            # Only create simple indexes if they don't exist
            index_names = [idx['name'] for idx in existing_indexes]
            
            simple_indexes = [
                ('title', 'title_index'),
                ('cuisine', 'cuisine_index'),
                ('difficulty', 'difficulty_index'),
                ('estimated_time', 'time_index'),
                ('calories', 'calories_index')
            ]
            
            for field, name in simple_indexes:
                if name not in index_names:
                    try:
                        self.collection.create_index([(field, ASCENDING)], name=name)
                        print(f"✅ Created index: {name}")
                    except Exception as e:
                        print(f"⚠️  Could not create {name}: {e}")
            
        except Exception as e:
            print(f"⚠️  Index check warning: {e}")
    
    def is_connected(self):
        """Check if database is connected"""
        return self.collection is not None
    
    # ===== HELPER: Convert ObjectId =====
    
    def _convert_objectid(self, doc):
        """
        Recursively convert ObjectId to string for JSON serialization
        This is CRITICAL for preventing JSON serialization errors
        """
        if doc is None:
            return None
        
        if isinstance(doc, ObjectId):
            return str(doc)
        elif isinstance(doc, dict):
            return {key: self._convert_objectid(value) for key, value in doc.items()}
        elif isinstance(doc, list):
            return [self._convert_objectid(item) for item in doc]
        else:
            return doc
    
    # ===== CORE QUERY METHODS =====
    
    def get_all_recipes(self, page=1, limit=20, sort_by='title', sort_order=1):
        """Get paginated recipe list - FIXED ObjectId conversion"""
        if not self.is_connected():
            return self._empty_result(page, limit)
        
        try:
            skip = (page - 1) * limit
            total = self.collection.count_documents({})
            
            projection = {
                '_id': 1,
                'title': 1,
                'cuisine': 1,
                'difficulty': 1,
                'estimated_time': 1,
                'calories': 1,
                'is_veg': 1,
                'rating': 1
            }
            
            cursor = self.collection.find(
                {}, projection
            ).sort(sort_by, sort_order).skip(skip).limit(limit)
            
            # Convert ObjectIds to strings
            recipes = [self._convert_objectid(doc) for doc in cursor]
            pages = (total + limit - 1) // limit
            
            return {
                'recipes': recipes,
                'total': total,
                'page': page,
                'pages': pages,
                'limit': limit
            }
            
        except Exception as e:
            print(f"❌ Get recipes error: {e}")
            import traceback
            traceback.print_exc()
            return self._empty_result(page, limit)
    
    def get_recipe_by_name(self, recipe_name):
        """Get full recipe details by exact name - FIXED ObjectId"""
        if not self.is_connected():
            return None
        
        try:
            recipe = self.collection.find_one({
                'title': {'$regex': f'^{recipe_name}$', '$options': 'i'}
            })
            
            return self._convert_objectid(recipe) if recipe else None
            
        except Exception as e:
            print(f"❌ Get recipe by name error: {e}")
            return None
    
    def get_recipe_by_id(self, recipe_id):
        """Get recipe by MongoDB ObjectId - FIXED ObjectId conversion"""
        if not self.is_connected():
            return None
        
        try:
            if isinstance(recipe_id, str):
                recipe_id = ObjectId(recipe_id)
            
            recipe = self.collection.find_one({'_id': recipe_id})
            return self._convert_objectid(recipe) if recipe else None
            
        except Exception as e:
            print(f"❌ Get recipe by ID error: {e}")
            return None
    
    def search_recipes(self, query, page=1, limit=20):
        """Full-text search using existing text index - FIXED ObjectId"""
        if not self.is_connected():
            return self._empty_result(page, limit)
        
        try:
            skip = (page - 1) * limit
            
            search_filter = {'$text': {'$search': query}}
            
            total = self.collection.count_documents(search_filter)
            cursor = self.collection.find(search_filter).skip(skip).limit(limit)
            
            recipes = [self._convert_objectid(doc) for doc in cursor]
            pages = (total + limit - 1) // limit
            
            return {
                'recipes': recipes,
                'total': total,
                'page': page,
                'pages': pages,
                'limit': limit,
                'query': query
            }
            
        except Exception as e:
            print(f"❌ Search error: {e}")
            return self._regex_search(query, page, limit)
    
    def _regex_search(self, query, page=1, limit=20):
        """Fallback regex search if text index doesn't work - FIXED ObjectId"""
        try:
            skip = (page - 1) * limit
            
            search_filter = {
                '$or': [
                    {'title': {'$regex': query, '$options': 'i'}},
                    {'ingredients': {'$regex': query, '$options': 'i'}}
                ]
            }
            
            total = self.collection.count_documents(search_filter)
            cursor = self.collection.find(search_filter).skip(skip).limit(limit)
            
            recipes = [self._convert_objectid(doc) for doc in cursor]
            pages = (total + limit - 1) // limit
            
            return {
                'recipes': recipes,
                'total': total,
                'page': page,
                'pages': pages,
                'limit': limit,
                'query': query
            }
        except Exception as e:
            print(f"❌ Regex search error: {e}")
            return self._empty_result(page, limit)
    
    def search_by_ingredient(self, ingredient, page=1, limit=20):
        """Search recipes containing specific ingredient - FIXED ObjectId"""
        if not self.is_connected():
            return self._empty_result(page, limit)
        
        try:
            skip = (page - 1) * limit
            
            search_filter = {
                'ingredients': {'$regex': ingredient, '$options': 'i'}
            }
            
            total = self.collection.count_documents(search_filter)
            cursor = self.collection.find(search_filter).skip(skip).limit(limit)
            
            recipes = [self._convert_objectid(doc) for doc in cursor]
            pages = (total + limit - 1) // limit
            
            return {
                'recipes': recipes,
                'total': total,
                'page': page,
                'pages': pages,
                'limit': limit,
                'ingredient': ingredient
            }
            
        except Exception as e:
            print(f"❌ Search by ingredient error: {e}")
            return self._empty_result(page, limit)
    
    def filter_recipes(self, filters, page=1, limit=20):
        """Filter recipes by multiple criteria - FIXED ObjectId"""
        if not self.is_connected():
            return self._empty_result(page, limit)
        
        try:
            skip = (page - 1) * limit
            query = {}
            
            if filters.get('difficulty'):
                query['difficulty'] = filters['difficulty']
            
            if filters.get('cuisine'):
                query['cuisine'] = {'$regex': filters['cuisine'], '$options': 'i'}
            
            if filters.get('max_time'):
                query['estimated_time'] = {'$lte': int(filters['max_time'])}
            
            if filters.get('max_calories') or filters.get('min_calories'):
                cal_query = {}
                if filters.get('max_calories'):
                    cal_query['$lte'] = int(filters['max_calories'])
                if filters.get('min_calories'):
                    cal_query['$gte'] = int(filters['min_calories'])
                query['calories'] = cal_query
            
            total = self.collection.count_documents(query)
            cursor = self.collection.find(query).skip(skip).limit(limit)
            
            recipes = [self._convert_objectid(doc) for doc in cursor]
            pages = (total + limit - 1) // limit
            
            return {
                'recipes': recipes,
                'total': total,
                'page': page,
                'pages': pages,
                'limit': limit,
                'filters': filters
            }
            
        except Exception as e:
            print(f"❌ Filter recipes error: {e}")
            import traceback
            traceback.print_exc()
            return self._empty_result(page, limit)
    
    def get_random_recipes(self, count=5):
        """Get random recipes using aggregation - FIXED ObjectId"""
        if not self.is_connected():
            return []
        
        try:
            pipeline = [{'$sample': {'size': count}}]
            recipes = list(self.collection.aggregate(pipeline))
            return [self._convert_objectid(doc) for doc in recipes]
            
        except Exception as e:
            print(f"❌ Get random recipes error: {e}")
            return []
    
    # ===== STATISTICS & AGGREGATIONS =====
    
    def get_statistics(self):
        """Get comprehensive database statistics"""
        if not self.is_connected():
            return self._empty_stats()
        
        try:
            total = self.collection.count_documents({})
            
            # Difficulty distribution
            difficulty_pipeline = [
                {'$group': {'_id': '$difficulty', 'count': {'$sum': 1}}}
            ]
            difficulty_dist = {
                item['_id']: item['count']
                for item in self.collection.aggregate(difficulty_pipeline)
                if item['_id']
            }
            
            # Cuisine distribution (top 10)
            cuisine_pipeline = [
                {'$group': {'_id': '$cuisine', 'count': {'$sum': 1}}},
                {'$sort': {'count': -1}},
                {'$limit': 10}
            ]
            cuisine_dist = {
                item['_id']: item['count']
                for item in self.collection.aggregate(cuisine_pipeline)
                if item['_id']
            }
            
            # Calorie statistics
            calorie_pipeline = [
                {
                    '$group': {
                        '_id': None,
                        'avg_calories': {'$avg': '$calories'},
                        'min_calories': {'$min': '$calories'},
                        'max_calories': {'$max': '$calories'}
                    }
                }
            ]
            cal_stats = list(self.collection.aggregate(calorie_pipeline))
            
            # Time statistics
            time_pipeline = [
                {
                    '$group': {
                        '_id': None,
                        'avg_time': {'$avg': '$estimated_time'},
                        'min_time': {'$min': '$estimated_time'},
                        'max_time': {'$max': '$estimated_time'}
                    }
                }
            ]
            time_stats = list(self.collection.aggregate(time_pipeline))
            
            return {
                'total_recipes': total,
                'difficulty_distribution': difficulty_dist,
                'cuisine_distribution': cuisine_dist,
                'calorie_stats': cal_stats[0] if cal_stats else {},
                'time_stats': time_stats[0] if time_stats else {}
            }
            
        except Exception as e:
            print(f"❌ Get statistics error: {e}")
            import traceback
            traceback.print_exc()
            return self._empty_stats()
    
    def get_cuisines(self):
        """Get all unique cuisines"""
        if not self.is_connected():
            return []
        
        try:
            return sorted(self.collection.distinct('cuisine'))
        except Exception as e:
            print(f"❌ Get cuisines error: {e}")
            return []
    
    def get_difficulties(self):
        """Get all unique difficulty levels"""
        if not self.is_connected():
            return []
        
        try:
            return sorted(self.collection.distinct('difficulty'))
        except Exception as e:
            print(f"❌ Get difficulties error: {e}")
            return []
    
    # ===== HELPER METHODS =====
    
    def _empty_result(self, page, limit):
        """Return empty result structure"""
        return {
            'recipes': [],
            'total': 0,
            'page': page,
            'pages': 0,
            'limit': limit
        }
    
    def _empty_stats(self):
        """Return empty statistics structure"""
        return {
            'total_recipes': 0,
            'difficulty_distribution': {},
            'cuisine_distribution': {},
            'calorie_stats': {},
            'time_stats': {}
        }


# Singleton instance
_db_instance = None

def get_db():
    """Get database instance (singleton pattern)"""
    global _db_instance
    
    if _db_instance is None:
        _db_instance = RecipeDatabase()
    
    return _db_instance


# Test connection when imported
if __name__ == '__main__':
    db = get_db()
    if db.is_connected():
        stats = db.get_statistics()
        print(f"\n📊 Database Stats:")
        print(f"Total Recipes: {stats['total_recipes']:,}")
        print(f"Difficulties: {stats['difficulty_distribution']}")
        print(f"Top Cuisines: {list(stats['cuisine_distribution'].keys())[:5]}")
