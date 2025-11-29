"""
Flask Backend for Cooking Recipe Analyzer - FIXED JSON SERIALIZATION
MongoDB-driven API for 100,000+ recipes
Field mappings: title -> RecipeName, ingredients -> Ingredients, etc.
"""
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import sys
import os
from functools import wraps
import time
from bson import ObjectId
import json

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import utilities
try:
    from utils.db_config import get_db
    from utils.calorie_estimator import CalorieEstimator
    from utils.difficulty_analyzer import DifficultyAnalyzer
    from utils.time_predictor import TimePredictor
    from utils.suggestion_generator import SuggestionGenerator
except ImportError as e:
    print(f"❌ Import Error: {e}")
    print("Make sure all utility files are in the utils directory")
    sys.exit(1)


# ===== JSON ENCODER FOR MONGODB =====
class MongoJSONEncoder(json.JSONEncoder):
    """Custom JSON encoder to handle MongoDB ObjectId"""
    def default(self, obj):
        if isinstance(obj, ObjectId):
            return str(obj)
        return super().default(obj)


# Initialize Flask app
app = Flask(__name__, static_folder='../frontend', static_url_path='')
app.json_encoder = MongoJSONEncoder  # Use custom encoder
CORS(app, resources={r"/api/*": {"origins": "*"}})

# Configure
app.config['JSON_SORT_KEYS'] = False
app.config['RESTFUL_JSON'] = {'cls': MongoJSONEncoder}

# Get database instance
try:
    db = get_db()
    if not db.is_connected():
        print("⚠️ WARNING: Database not connected! Starting anyway...")
except Exception as e:
    print(f"❌ Database initialization error: {e}")
    db = None


# ===== HELPER: Convert ObjectId to String =====
def convert_objectid(obj):
    """Recursively convert ObjectId to string in nested structures"""
    if isinstance(obj, ObjectId):
        return str(obj)
    elif isinstance(obj, dict):
        return {key: convert_objectid(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [convert_objectid(item) for item in obj]
    return obj


# ===== FIELD MAPPING HELPER =====
def map_recipe_fields(recipe):
    """
    Convert your DB schema to expected frontend schema
    Your schema: title, ingredients, calories, steps, estimated_time, difficulty, cuisine
    Expected: RecipeName, Ingredients, Calories, Instructions, TotalTimeInMins, Difficulty, Cuisine
    """
    if not recipe:
        return None
    
    # Convert ObjectId first
    recipe = convert_objectid(recipe)
    
    # Create mapped version
    mapped = {
        '_id': recipe.get('_id'),
        'RecipeName': recipe.get('title', 'Untitled Recipe'),
        'Cuisine': recipe.get('cuisine', 'Unknown'),
        'Difficulty': recipe.get('difficulty', 'Medium'),
        'TotalTimeInMins': recipe.get('estimated_time', 0),
        'PrepTimeInMins': recipe.get('estimated_time', 0) // 2,
        'CookTimeInMins': recipe.get('estimated_time', 0) // 2,
        'Calories': recipe.get('calories', 0),
        'Servings': 4,
        'Ingredients': recipe.get('ingredients', []),
        'IngredientQuantities': recipe.get('ingredient_quantities', {}),
        'Instructions': '\n'.join(recipe.get('steps', [])),
        'TranslatedInstructions': '\n'.join(recipe.get('steps', [])),
        'IsVegetarian': recipe.get('is_veg', False),
        'Tags': recipe.get('tags', []),
        'Rating': recipe.get('rating', 0)
    }
    
    return mapped


# ===== PERFORMANCE MONITORING =====
def monitor_performance(f):
    """Decorator to monitor endpoint performance"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        start_time = time.time()
        result = f(*args, **kwargs)
        end_time = time.time()
        execution_time = (end_time - start_time) * 1000
        print(f"⏱️  {f.__name__} executed in {execution_time:.2f}ms")
        return result
    return decorated_function


# ===== FRONTEND ROUTES =====
@app.route('/')
def serve_frontend():
    """Serve main HTML page"""
    frontend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'frontend'))
    try:
        return send_from_directory(frontend_dir, 'index.html')
    except Exception as e:
        return f"Error serving frontend: {e}", 500


@app.route('/<path:path>')
def serve_static_files(path):
    """Serve static files (CSS, JS, images)"""
    frontend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'frontend'))
    try:
        return send_from_directory(frontend_dir, path)
    except Exception as e:
        return f"Error serving {path}: {e}", 404


# ===== API ROUTES =====

@app.route('/api/health')
def health_check():
    """Health check endpoint"""
    is_connected = db and db.is_connected()
    total_recipes = 0
    
    if is_connected:
        try:
            total_recipes = db.collection.count_documents({})
        except:
            pass
    
    return jsonify({
        'status': 'success',
        'message': 'Recipe Analyzer API is running',
        'version': '3.0.2',
        'database': 'connected' if is_connected else 'disconnected',
        'total_recipes': total_recipes
    })


# ===== RECIPE RETRIEVAL ENDPOINTS =====

@app.route('/api/recipes', methods=['GET'])
@monitor_performance
def get_recipes():
    """Get paginated recipe list with field mapping"""
    if not db or not db.is_connected():
        return jsonify({
            'status': 'error', 
            'message': 'Database not connected. Please check MongoDB is running.'
        }), 503
    
    try:
        page = max(int(request.args.get('page', 1)), 1)
        limit = min(int(request.args.get('limit', 20)), 100)
        sort_by = request.args.get('sort_by', 'title')
        sort_order = int(request.args.get('sort_order', 1))
        
        result = db.get_all_recipes(page, limit, sort_by, sort_order)
        
        # Map recipes to expected format
        mapped_recipes = [map_recipe_fields(recipe) for recipe in result['recipes']]
        
        return jsonify({
            'status': 'success',
            'recipes': mapped_recipes,
            'total': result['total'],
            'page': result['page'],
            'pages': result['pages'],
            'limit': result['limit']
        }), 200
        
    except Exception as e:
        print(f"❌ Get recipes error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/api/recipe/<recipe_name>', methods=['GET'])
@monitor_performance
def get_recipe_by_name(recipe_name):
    """Get full recipe details by name"""
    if not db or not db.is_connected():
        return jsonify({'status': 'error', 'message': 'Database not connected'}), 503
    
    try:
        recipe = db.collection.find_one({
            'title': {'$regex': f'^{recipe_name}$', '$options': 'i'}
        })
        
        if recipe:
            mapped = map_recipe_fields(recipe)
            return jsonify({'status': 'success', 'recipe': mapped}), 200
        else:
            return jsonify({'status': 'error', 'message': 'Recipe not found'}), 404
            
    except Exception as e:
        print(f"❌ Get recipe error: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/api/recipe/id/<recipe_id>', methods=['GET'])
@monitor_performance
def get_recipe_by_id(recipe_id):
    """Get recipe by MongoDB ObjectId - FIXED JSON SERIALIZATION"""
    if not db or not db.is_connected():
        return jsonify({'status': 'error', 'message': 'Database not connected'}), 503
    
    try:
        # Convert string ID to ObjectId
        obj_id = ObjectId(recipe_id)
        recipe = db.collection.find_one({'_id': obj_id})
        
        if recipe:
            # Convert ObjectId before mapping
            mapped = map_recipe_fields(recipe)
            return jsonify({'status': 'success', 'recipe': mapped}), 200
        else:
            return jsonify({'status': 'error', 'message': 'Recipe not found'}), 404
            
    except Exception as e:
        print(f"❌ Get recipe by ID error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/api/recipes/random', methods=['GET'])
@monitor_performance
def get_random_recipes():
    """Get random recipes"""
    if not db or not db.is_connected():
        return jsonify({'status': 'error', 'message': 'Database not connected'}), 503
    
    try:
        count = min(int(request.args.get('count', 5)), 20)
        
        pipeline = [{'$sample': {'size': count}}]
        recipes = list(db.collection.aggregate(pipeline))
        
        # Map to expected format
        mapped_recipes = [map_recipe_fields(recipe) for recipe in recipes]
        
        return jsonify({
            'status': 'success',
            'count': len(mapped_recipes),
            'recipes': mapped_recipes
        }), 200
        
    except Exception as e:
        print(f"❌ Get random recipes error: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500


# ===== SEARCH ENDPOINTS =====

@app.route('/api/search', methods=['GET'])
@monitor_performance
def search_recipes():
    """Full-text search across recipes"""
    if not db or not db.is_connected():
        return jsonify({'status': 'error', 'message': 'Database not connected'}), 503
    
    try:
        query = request.args.get('q', '').strip()
        
        if not query:
            return jsonify({'status': 'error', 'message': 'Search query required'}), 400
        
        page = max(int(request.args.get('page', 1)), 1)
        limit = min(int(request.args.get('limit', 20)), 100)
        skip = (page - 1) * limit
        
        # Use text search on existing index
        search_filter = {'$text': {'$search': query}}
        
        total = db.collection.count_documents(search_filter)
        
        cursor = db.collection.find(search_filter).skip(skip).limit(limit)
        recipes = list(cursor)
        
        # Map to expected format
        mapped_recipes = [map_recipe_fields(recipe) for recipe in recipes]
        
        pages = (total + limit - 1) // limit
        
        return jsonify({
            'status': 'success',
            'recipes': mapped_recipes,
            'total': total,
            'page': page,
            'pages': pages,
            'limit': limit,
            'query': query
        }), 200
        
    except Exception as e:
        print(f"❌ Search error: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/api/search/ingredient/<ingredient>', methods=['GET'])
@monitor_performance
def search_by_ingredient(ingredient):
    """Search recipes by ingredient"""
    if not db or not db.is_connected():
        return jsonify({'status': 'error', 'message': 'Database not connected'}), 503
    
    try:
        page = max(int(request.args.get('page', 1)), 1)
        limit = min(int(request.args.get('limit', 20)), 100)
        skip = (page - 1) * limit
        
        search_filter = {
            'ingredients': {'$regex': ingredient, '$options': 'i'}
        }
        
        total = db.collection.count_documents(search_filter)
        cursor = db.collection.find(search_filter).skip(skip).limit(limit)
        recipes = list(cursor)
        
        # Map to expected format
        mapped_recipes = [map_recipe_fields(recipe) for recipe in recipes]
        
        pages = (total + limit - 1) // limit
        
        return jsonify({
            'status': 'success',
            'recipes': mapped_recipes,
            'total': total,
            'page': page,
            'pages': pages,
            'limit': limit,
            'ingredient': ingredient
        }), 200
        
    except Exception as e:
        print(f"❌ Search by ingredient error: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500


# ===== FILTER ENDPOINTS =====

@app.route('/api/recipes/filter', methods=['GET'])
@monitor_performance
def filter_recipes():
    """Filter recipes by multiple criteria - FIXED JSON SERIALIZATION"""
    if not db or not db.is_connected():
        return jsonify({'status': 'error', 'message': 'Database not connected'}), 503
    
    try:
        page = max(int(request.args.get('page', 1)), 1)
        limit = min(int(request.args.get('limit', 20)), 100)
        skip = (page - 1) * limit
        
        query = {}
        
        # Map filter fields to your schema
        if request.args.get('difficulty'):
            query['difficulty'] = request.args.get('difficulty')
        
        if request.args.get('cuisine'):
            query['cuisine'] = {'$regex': request.args.get('cuisine'), '$options': 'i'}
        
        if request.args.get('max_time'):
            query['estimated_time'] = {'$lte': int(request.args.get('max_time'))}
        
        if request.args.get('max_calories') or request.args.get('min_calories'):
            cal_query = {}
            if request.args.get('max_calories'):
                cal_query['$lte'] = int(request.args.get('max_calories'))
            if request.args.get('min_calories'):
                cal_query['$gte'] = int(request.args.get('min_calories'))
            query['calories'] = cal_query
        
        total = db.collection.count_documents(query)
        cursor = db.collection.find(query).skip(skip).limit(limit)
        recipes = list(cursor)
        
        # Convert ObjectIds and map to expected format
        mapped_recipes = [map_recipe_fields(recipe) for recipe in recipes]
        
        pages = (total + limit - 1) // limit
        
        return jsonify({
            'status': 'success',
            'recipes': mapped_recipes,
            'total': total,
            'page': page,
            'pages': pages,
            'limit': limit
        }), 200
        
    except Exception as e:
        print(f"❌ Filter recipes error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'status': 'error', 'message': str(e)}), 500


# ===== ANALYSIS ENDPOINTS =====

@app.route('/api/analysis/calories', methods=['POST'])
@monitor_performance
def analyze_calories():
    """Analyze calories for custom ingredient list"""
    try:
        data = request.get_json()
        
        if not data or 'ingredients' not in data:
            return jsonify({'status': 'error', 'message': 'Ingredients required'}), 400
        
        ingredients = [i.strip() for i in data['ingredients'] if i.strip()]
        
        if not ingredients:
            return jsonify({'status': 'error', 'message': 'At least one ingredient required'}), 400
        
        calorie_data = CalorieEstimator.estimate_calories(ingredients)
        
        return jsonify({
            'status': 'success',
            'analysis': calorie_data
        }), 200
        
    except Exception as e:
        print(f"❌ Calorie analysis error: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/api/analysis/difficulty', methods=['POST'])
@monitor_performance
def analyze_difficulty():
    """Analyze recipe difficulty"""
    try:
        data = request.get_json()
        
        if not data or 'ingredients' not in data or 'steps' not in data:
            return jsonify({'status': 'error', 'message': 'Ingredients and steps required'}), 400
        
        ingredients = [i.strip() for i in data['ingredients'] if i.strip()]
        steps = data['steps'].strip()
        
        if not ingredients or not steps:
            return jsonify({'status': 'error', 'message': 'Ingredients and steps cannot be empty'}), 400
        
        difficulty_data = DifficultyAnalyzer.analyze_difficulty(ingredients, steps)
        
        return jsonify({
            'status': 'success',
            'analysis': difficulty_data
        }), 200
        
    except Exception as e:
        print(f"❌ Difficulty analysis error: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/api/analysis/time', methods=['POST'])
@monitor_performance
def analyze_time():
    """Predict cooking time"""
    try:
        data = request.get_json()
        
        if not data or 'steps' not in data:
            return jsonify({'status': 'error', 'message': 'Steps required'}), 400
        
        steps = data['steps'].strip()
        step_count = data.get('step_count', len(steps.split('\n')))
        
        if not steps:
            return jsonify({'status': 'error', 'message': 'Steps cannot be empty'}), 400
        
        time_data = TimePredictor.predict_time(steps, step_count)
        
        return jsonify({
            'status': 'success',
            'analysis': time_data
        }), 200
        
    except Exception as e:
        print(f"❌ Time analysis error: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/api/suggestions', methods=['POST'])
@monitor_performance
def get_suggestions():
    """Get cooking suggestions"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'status': 'error', 'message': 'Request data required'}), 400
        
        ingredients = data.get('ingredients', [])
        steps = data.get('steps', '')
        difficulty = data.get('difficulty', 'Medium')
        total_calories = data.get('total_calories', 0)
        servings = data.get('servings', 1)
        
        suggestions = SuggestionGenerator.generate_suggestions(
            ingredients, steps, difficulty, total_calories, servings
        )
        
        return jsonify({
            'status': 'success',
            'suggestions': suggestions
        }), 200
        
    except Exception as e:
        print(f"❌ Suggestions error: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500


# ===== STATISTICS & VISUALIZATION ENDPOINTS =====

@app.route('/api/statistics', methods=['GET'])
@monitor_performance
def get_statistics():
    """Get comprehensive database statistics - FIXED"""
    if not db or not db.is_connected():
        return jsonify({'status': 'error', 'message': 'Database not connected'}), 503
    
    try:
        total = db.collection.count_documents({})
        
        # Difficulty distribution
        difficulty_pipeline = [
            {'$group': {'_id': '$difficulty', 'count': {'$sum': 1}}}
        ]
        difficulty_dist = {
            item['_id']: item['count']
            for item in db.collection.aggregate(difficulty_pipeline)
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
            for item in db.collection.aggregate(cuisine_pipeline)
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
        cal_stats = list(db.collection.aggregate(calorie_pipeline))
        
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
        time_stats = list(db.collection.aggregate(time_pipeline))
        
        stats = {
            'total_recipes': total,
            'difficulty_distribution': difficulty_dist,
            'cuisine_distribution': cuisine_dist,
            'calorie_stats': cal_stats[0] if cal_stats else {},
            'time_stats': time_stats[0] if time_stats else {}
        }
        
        return jsonify({
            'status': 'success',
            'statistics': stats
        }), 200
        
    except Exception as e:
        print(f"❌ Statistics error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/api/cuisines', methods=['GET'])
def get_cuisines():
    """Get all unique cuisines"""
    if not db or not db.is_connected():
        return jsonify({'status': 'error', 'message': 'Database not connected'}), 503
    
    try:
        cuisines = sorted(db.collection.distinct('cuisine'))
        
        return jsonify({
            'status': 'success',
            'count': len(cuisines),
            'cuisines': cuisines
        }), 200
        
    except Exception as e:
        print(f"❌ Get cuisines error: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/api/difficulties', methods=['GET'])
def get_difficulties():
    """Get all unique difficulty levels"""
    if not db or not db.is_connected():
        return jsonify({'status': 'error', 'message': 'Database not connected'}), 503
    
    try:
        difficulties = sorted(db.collection.distinct('difficulty'))
        
        return jsonify({
            'status': 'success',
            'count': len(difficulties),
            'difficulties': difficulties
        }), 200
        
    except Exception as e:
        print(f"❌ Get difficulties error: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/api/visualization/stats', methods=['GET'])
@monitor_performance
def get_visualization_stats():
    """Get data formatted for Chart.js visualization - FIXED"""
    if not db or not db.is_connected():
        return jsonify({'status': 'error', 'message': 'Database not connected'}), 503
    
    try:
        # Get statistics directly instead of calling endpoint
        total = db.collection.count_documents({})
        
        # Difficulty distribution
        difficulty_pipeline = [
            {'$group': {'_id': '$difficulty', 'count': {'$sum': 1}}}
        ]
        difficulty_dist = {
            item['_id']: item['count']
            for item in db.collection.aggregate(difficulty_pipeline)
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
            for item in db.collection.aggregate(cuisine_pipeline)
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
        cal_stats = list(db.collection.aggregate(calorie_pipeline))
        
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
        time_stats = list(db.collection.aggregate(time_pipeline))
        
        # Format for visualization
        viz_data = {
            'difficulty': {
                'labels': list(difficulty_dist.keys()),
                'data': list(difficulty_dist.values())
            },
            'cuisine': {
                'labels': list(cuisine_dist.keys()),
                'data': list(cuisine_dist.values())
            },
            'summary': {
                'total_recipes': total,
                'avg_calories': round(cal_stats[0].get('avg_calories', 0)) if cal_stats else 0,
                'avg_time': round(time_stats[0].get('avg_time', 0)) if time_stats else 0
            }
        }
        
        return jsonify({
            'status': 'success',
            'visualization': viz_data
        }), 200
        
    except Exception as e:
        print(f"❌ Visualization stats error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'status': 'error', 'message': str(e)}), 500


# ===== ERROR HANDLERS =====

@app.errorhandler(404)
def not_found(error):
    return jsonify({'status': 'error', 'message': 'Endpoint not found'}), 404


@app.errorhandler(500)
def internal_error(error):
    return jsonify({'status': 'error', 'message': 'Internal server error'}), 500


@app.errorhandler(400)
def bad_request(error):
    return jsonify({'status': 'error', 'message': 'Bad request'}), 400


# ===== RUN APPLICATION =====
if __name__ == '__main__':
    print("=" * 70)
    print("🍳 Cooking Recipe Analyzer v3.0.2 - JSON FIXES")
    print("=" * 70)
    print(f"🌐 Application running on: http://localhost:5005")
    print(f"📱 Open in browser: http://localhost:5005")
    print(f"📡 API base: http://localhost:5005/api")
    
    if db and db.is_connected():
        try:
            total = db.collection.count_documents({})
            print(f"🗄️  Database: {db.db_name}")
            print(f"📊 Total Recipes: {total:,}")
            
            sample = db.collection.find_one()
            if sample:
                print(f"🔍 Sample recipe fields: {list(sample.keys())[:8]}")
        except Exception as e:
            print(f"⚠️  Database connected but error: {e}")
    else:
        print(f"❌ Database: NOT CONNECTED")
        print(f"💡 Please ensure MongoDB is running: mongod")
    
    print("=" * 70)
    print("✅ Server is ready! Press CTRL+C to stop.")
    print("=" * 70)
    
    app.run(debug=True, host='0.0.0.0', port=5005)
