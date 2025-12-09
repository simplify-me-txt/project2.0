/**
 * Recipe Explorer - Frontend Application
 * Connects to MongoDB-backed Flask API
 */

// ===== CONFIGURATION =====
const API_BASE = 'http://localhost:5005/api';
const THEME_KEY = 'recipe_theme';
const FAVORITES_KEY = 'recipe_favorites';

// ===== STATE MANAGEMENT =====
const state = {
    currentView: 'explore',
    currentPage: 1,
    totalPages: 1,
    currentRecipes: [],
    favorites: [],
    cuisines: [],
    activeFilters: {},
    charts: {}
};

// ===== DOM ELEMENTS =====
const dom = {
    // Views
    exploreView: document.getElementById('exploreView'),
    analyzeView: document.getElementById('analyzeView'),
    statsView: document.getElementById('statsView'),
    favoritesView: document.getElementById('favoritesView'),

    // Navigation
    navBtns: document.querySelectorAll('.nav-btn'),
    themeToggle: document.getElementById('themeToggle'),

    // Search & Filters
    searchInput: document.getElementById('searchInput'),
    searchBtn: document.getElementById('searchBtn'),
    filterToggle: document.getElementById('filterToggle'),
    filterPanel: document.getElementById('filterPanel'),
    applyFilters: document.getElementById('applyFilters'),
    clearFilters: document.getElementById('clearFilters'),
    randomBtn: document.getElementById('randomBtn'),

    // Recipe Grid
    recipeGrid: document.getElementById('recipeGrid'),
    pagination: document.getElementById('pagination'),

    // Analyze Form (Recipe Studio)
    analyzeForm: document.getElementById('analyzeForm'),
    recipeTitle: document.getElementById('recipeTitle'),
    recipeCuisine: document.getElementById('recipeCuisine'),
    isVegetarian: document.getElementById('isVegetarian'),
    ingredientsInput: document.getElementById('ingredientsInput'),
    stepsInput: document.getElementById('stepsInput'),
    saveRecipeBtn: document.getElementById('saveRecipeBtn'),

    // Analysis Results
    analysisResults: document.getElementById('analysisResults'),

    // Result Tabs & Content
    healthScore: document.getElementById('healthScore'),
    resCalories: document.getElementById('resCalories'),
    resTime: document.getElementById('resTime'),
    resDifficulty: document.getElementById('resDifficulty'),
    allergenBox: document.getElementById('allergenBox'),
    allergenList: document.getElementById('allergenList'),
    chefSuggestions: document.getElementById('chefSuggestions'),
    flavorRadarChart: document.getElementById('flavorRadarChart'),
    comparisonBars: document.getElementById('comparisonBars'),
    similarRecipes: document.getElementById('similarRecipes'),

    // Stats
    statsSummary: document.getElementById('statsSummary'),
    difficultyChart: document.getElementById('difficultyChart'),
    cuisineChart: document.getElementById('cuisineChart'),

    // Favorites
    favoritesGrid: document.getElementById('favoritesGrid'),
    noFavorites: document.getElementById('noFavorites'),

    // Modal
    recipeModal: document.getElementById('recipeModal'),
    recipeDetail: document.getElementById('recipeDetail'),

    // Loading
    loadingOverlay: document.getElementById('loadingOverlay')
};

// ===== INITIALIZATION =====
async function init() {
    console.log('🚀 Initializing Recipe Explorer...');

    // Load theme
    loadTheme();

    // Load favorites from localStorage
    loadFavorites();

    // Load cuisines for filter dropdown
    await loadCuisines();

    // Setup event listeners
    setupEventListeners();

    // Load initial recipes
    await loadRecipes();

    hideLoading();

    console.log('✅ Recipe Explorer ready!');
}

// ===== THEME MANAGEMENT =====
function loadTheme() {
    const theme = localStorage.getItem(THEME_KEY) || 'light';
    if (theme === 'dark') {
        document.body.classList.add('dark-mode');
        dom.themeToggle.querySelector('i').className = 'fas fa-sun';
    }
}

function toggleTheme() {
    document.body.classList.toggle('dark-mode');
    const isDark = document.body.classList.contains('dark-mode');
    dom.themeToggle.querySelector('i').className = isDark ? 'fas fa-sun' : 'fas fa-moon';
    localStorage.setItem(THEME_KEY, isDark ? 'dark' : 'light');
}

// ===== FAVORITES MANAGEMENT =====
function loadFavorites() {
    const saved = localStorage.getItem(FAVORITES_KEY);
    state.favorites = saved ? JSON.parse(saved) : [];
}

function saveFavorites() {
    localStorage.setItem(FAVORITES_KEY, JSON.stringify(state.favorites));
}

function toggleFavorite(recipeId, recipeName) {
    const index = state.favorites.findIndex(f => f.id === recipeId);

    if (index > -1) {
        state.favorites.splice(index, 1);
        showToast('Removed from favorites');
    } else {
        state.favorites.push({ id: recipeId, name: recipeName });
        showToast('Added to favorites ❤️');
    }

    saveFavorites();

    // Update UI if in favorites view
    if (state.currentView === 'favorites') {
        displayFavorites();
    }
}

function isFavorite(recipeId) {
    return state.favorites.some(f => f.id === recipeId);
}

// ===== EVENT LISTENERS =====
function setupEventListeners() {
    // Navigation
    dom.navBtns.forEach(btn => {
        btn.addEventListener('click', () => switchView(btn.dataset.view));
    });

    // Theme toggle
    dom.themeToggle.addEventListener('click', toggleTheme);

    // Search
    dom.searchBtn.addEventListener('click', handleSearch);
    dom.searchInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') handleSearch();
    });

    // Filters
    dom.filterToggle.addEventListener('click', () => {
        dom.filterPanel.style.display =
            dom.filterPanel.style.display === 'none' ? 'block' : 'none';
    });

    dom.applyFilters.addEventListener('click', handleApplyFilters);
    dom.clearFilters.addEventListener('click', handleClearFilters);

    // Random recipe
    dom.randomBtn.addEventListener('click', loadRandomRecipe);

    // Analyze form
    dom.analyzeForm.addEventListener('submit', handleAnalyze);

    // Save Recipe Button
    if (dom.saveRecipeBtn) {
        dom.saveRecipeBtn.addEventListener('click', saveRecipe);
    }

    // Result Tabs
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
            document.querySelectorAll('.result-content').forEach(c => c.classList.remove('active'));

            btn.classList.add('active');
            document.getElementById(`tab-${btn.dataset.tab}`).classList.add('active');
        });
    });

    // Modal close
    const modalClose = document.querySelector('.modal-close');
    if (modalClose) {
        modalClose.addEventListener('click', closeModal);
    }

    dom.recipeModal.addEventListener('click', (e) => {
        if (e.target === dom.recipeModal) closeModal();
    });
}

// ===== VIEW SWITCHING =====
function switchView(viewName) {
    state.currentView = viewName;

    // Update nav buttons
    dom.navBtns.forEach(btn => {
        btn.classList.toggle('active', btn.dataset.view === viewName);
    });

    // Hide all views
    document.querySelectorAll('.view').forEach(view => {
        view.classList.remove('active');
    });

    // Show selected view
    const viewMap = {
        explore: dom.exploreView,
        analyze: dom.analyzeView,
        stats: dom.statsView,
        favorites: dom.favoritesView
    };

    viewMap[viewName]?.classList.add('active');

    // Load data for view
    switch (viewName) {
        case 'explore':
            if (state.currentRecipes.length === 0) loadRecipes();
            break;
        case 'stats':
            loadStatistics();
            break;
        case 'favorites':
            displayFavorites();
            break;
    }
}

// ===== API CALLS =====
async function apiCall(endpoint, options = {}) {
    try {
        const response = await fetch(`${API_BASE}${endpoint}`, options);
        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.message || 'API request failed');
        }

        return data;
    } catch (error) {
        console.error('API Error:', error);
        showToast('Error: ' + error.message, 'error');
        throw error;
    }
}

// ===== LOAD RECIPES =====
async function loadRecipes(page = 1) {
    showLoading();

    try {
        const data = await apiCall(`/recipes?page=${page}&limit=20`);

        state.currentRecipes = data.recipes;
        state.currentPage = data.page;
        state.totalPages = data.pages;

        displayRecipes(data.recipes);
        displayPagination(data.page, data.pages);

    } catch (error) {
        dom.recipeGrid.innerHTML = '<p class="error">Failed to load recipes</p>';
    } finally {
        hideLoading();
    }
}

// ===== SEARCH =====
async function handleSearch() {
    const query = dom.searchInput.value.trim();

    if (!query) {
        loadRecipes();
        return;
    }

    showLoading();

    try {
        const data = await apiCall(`/search?q=${encodeURIComponent(query)}&limit=20`);

        state.currentRecipes = data.recipes;
        state.currentPage = data.page;
        state.totalPages = data.pages;

        displayRecipes(data.recipes);
        displayPagination(data.page, data.pages);

        showToast(`Found ${data.total} recipes`);

    } catch (error) {
        dom.recipeGrid.innerHTML = '<p class="error">Search failed</p>';
    } finally {
        hideLoading();
    }
}

// ===== FILTERS =====
// ===== FILTERS & INPUTS =====
async function loadCuisines() {
    try {
        const data = await apiCall('/cuisines');
        state.cuisines = data.cuisines;

        // Populate Filter Dropdown
        const filterSelect = document.getElementById('filterCuisine');
        if (filterSelect) {
            filterSelect.innerHTML = '<option value="">All Cuisines</option>';
            data.cuisines.forEach(cuisine => {
                filterSelect.innerHTML += `<option value="${cuisine}">${cuisine}</option>`;
            });
        }

        // Populate Input Datalist (Recipe Studio)
        const dataList = document.getElementById('cuisineList');
        if (dataList) {
            dataList.innerHTML = '';
            data.cuisines.forEach(cuisine => {
                dataList.innerHTML += `<option value="${cuisine}">`;
            });
        }

    } catch (error) {
        console.error('Failed to load cuisines');
    }
}

async function handleApplyFilters() {
    const filters = {
        difficulty: document.getElementById('filterDifficulty').value,
        cuisine: document.getElementById('filterCuisine').value,
        max_time: document.getElementById('filterMaxTime').value,
        max_calories: document.getElementById('filterMaxCalories').value
    };

    // Remove empty filters
    Object.keys(filters).forEach(key => {
        if (!filters[key]) delete filters[key];
    });

    state.activeFilters = filters;

    if (Object.keys(filters).length === 0) {
        loadRecipes();
        return;
    }

    showLoading();

    try {
        const params = new URLSearchParams(filters);
        const data = await apiCall(`/recipes/filter?${params}&limit=20`);

        state.currentRecipes = data.recipes;
        state.currentPage = data.page;
        state.totalPages = data.pages;

        displayRecipes(data.recipes);
        displayPagination(data.page, data.pages);

        showToast(`Found ${data.total} recipes`);

    } catch (error) {
        dom.recipeGrid.innerHTML = '<p class="error">Filter failed</p>';
    } finally {
        hideLoading();
    }
}

function handleClearFilters() {
    document.getElementById('filterDifficulty').value = '';
    document.getElementById('filterCuisine').value = '';
    document.getElementById('filterMaxTime').value = '';
    document.getElementById('filterMaxCalories').value = '';

    state.activeFilters = {};
    loadRecipes();
}

// ===== RANDOM RECIPE =====
async function loadRandomRecipe() {
    showLoading();

    try {
        const data = await apiCall('/recipes/random?count=1');

        if (data.recipes && data.recipes.length > 0) {
            showRecipeDetail(data.recipes[0]._id);
        }
    } catch (error) {
        showToast('Failed to load random recipe', 'error');
    } finally {
        hideLoading();
    }
}

// ===== DISPLAY RECIPES =====
function displayRecipes(recipes, container = dom.recipeGrid) {
    if (!recipes || recipes.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <i class="fas fa-search"></i>
                <p>No recipes found</p>
            </div>
        `;
        return;
    }

    container.innerHTML = recipes.map(recipe => `
        <div class="recipe-card" onclick="showRecipeDetail('${recipe._id}')">
            <div class="recipe-card-header">
                <h3 class="recipe-title">${recipe.RecipeName}</h3>
                <button class="favorite-btn ${isFavorite(recipe._id) ? 'active' : ''}" 
                        onclick="event.stopPropagation(); toggleFavorite('${recipe._id}', '${recipe.RecipeName.replace(/'/g, "\\'")}')">
                    <i class="fas fa-heart"></i>
                </button>
            </div>
            
            <div class="recipe-meta">
                <span class="meta-item">
                    <i class="fas fa-globe"></i> ${recipe.Cuisine || 'N/A'}
                </span>
                <span class="meta-item">
                    <i class="fas fa-clock"></i> ${recipe.TotalTimeInMins || 'N/A'} min
                </span>
            </div>
            
            <div class="recipe-stats">
                <div class="stat-small">
                    <span class="stat-label">Difficulty</span>
                    <span class="badge badge-${(recipe.Difficulty || 'medium').toLowerCase()}">
                        ${recipe.Difficulty || 'N/A'}
                    </span>
                </div>
                <div class="stat-small">
                    <span class="stat-label">Calories</span>
                    <span class="stat-value">${recipe.Calories || 'N/A'}</span>
                </div>
            </div>
        </div>
    `).join('');
}

// ===== PAGINATION =====
function displayPagination(current, total) {
    if (total <= 1) {
        dom.pagination.innerHTML = '';
        return;
    }

    let html = '';

    // Previous button
    if (current > 1) {
        html += `<button class="page-btn" onclick="loadRecipes(${current - 1})">
            <i class="fas fa-chevron-left"></i>
        </button>`;
    }

    // Page numbers
    const maxButtons = 7;
    let startPage = Math.max(1, current - Math.floor(maxButtons / 2));
    let endPage = Math.min(total, startPage + maxButtons - 1);

    if (endPage - startPage < maxButtons - 1) {
        startPage = Math.max(1, endPage - maxButtons + 1);
    }

    if (startPage > 1) {
        html += `<button class="page-btn" onclick="loadRecipes(1)">1</button>`;
        if (startPage > 2) html += `<span class="page-ellipsis">...</span>`;
    }

    for (let i = startPage; i <= endPage; i++) {
        html += `<button class="page-btn ${i === current ? 'active' : ''}" 
                         onclick="loadRecipes(${i})">${i}</button>`;
    }

    if (endPage < total) {
        if (endPage < total - 1) html += `<span class="page-ellipsis">...</span>`;
        html += `<button class="page-btn" onclick="loadRecipes(${total})">${total}</button>`;
    }

    // Next button
    if (current < total) {
        html += `<button class="page-btn" onclick="loadRecipes(${current + 1})">
            <i class="fas fa-chevron-right"></i>
        </button>`;
    }

    dom.pagination.innerHTML = html;
}

// ===== RECIPE DETAIL =====
async function showRecipeDetail(recipeId) {
    showLoading();

    try {
        const data = await apiCall(`/recipe/id/${recipeId}`);
        const recipe = data.recipe;

        const ingredients = Array.isArray(recipe.Ingredients)
            ? recipe.Ingredients
            : recipe.Ingredients?.split('\n') || [];

        const steps = recipe.TranslatedInstructions || recipe.Instructions || 'No instructions available';

        dom.recipeDetail.innerHTML = `
            <div class="recipe-detail-header">
                <h2>${recipe.RecipeName}</h2>
                <button class="favorite-btn ${isFavorite(recipe._id) ? 'active' : ''}" 
                        onclick="toggleFavorite('${recipe._id}', '${recipe.RecipeName.replace(/'/g, "\\'")}')">
                    <i class="fas fa-heart"></i>
                </button>
            </div>
            
            <div class="recipe-detail-meta">
                <span><i class="fas fa-globe"></i> ${recipe.Cuisine || 'N/A'}</span>
                <span><i class="fas fa-clock"></i> ${recipe.TotalTimeInMins || 'N/A'} min</span>
                <span><i class="fas fa-fire"></i> ${recipe.Calories || 'N/A'} kcal</span>
                <span class="badge badge-${(recipe.Difficulty || 'medium').toLowerCase()}">
                    ${recipe.Difficulty || 'N/A'}
                </span>
            </div>
            
            <div class="recipe-detail-content">
                <div class="recipe-section">
                    <h3><i class="fas fa-list"></i> Ingredients</h3>
                    <ul class="ingredients-list">
                        ${ingredients.map(ing => `<li>${ing}</li>`).join('')}
                    </ul>
                </div>
                
                <div class="recipe-section">
                    <h3><i class="fas fa-tasks"></i> Instructions</h3>
                    <div class="instructions-text">${steps.replace(/\n/g, '<br>')}</div>
                </div>
                
                ${recipe.TranslatedIngredients ? `
                <div class="recipe-section">
                    <h3><i class="fas fa-language"></i> Ingredients (Translated)</h3>
                    <p class="translated-text">${recipe.TranslatedIngredients}</p>
                </div>
                ` : ''}
            </div>
        `;

        dom.recipeModal.style.display = 'flex';

    } catch (error) {
        showToast('Failed to load recipe details', 'error');
    } finally {
        hideLoading();
    }
}

function closeModal() {
    dom.recipeModal.style.display = 'none';
}

// ===== ANALYZE RECIPE =====
// ===== ANALYZE RECIPE (RECIPE STUDIO) =====
async function handleAnalyze(e) {
    e.preventDefault();

    const title = dom.recipeTitle.value.trim();
    const cuisine = dom.recipeCuisine.value.trim();
    const isVeg = dom.isVegetarian.checked;
    const ingredientsText = dom.ingredientsInput.value.trim();
    const steps = dom.stepsInput.value.trim();

    if (!ingredientsText || !steps || !title) {
        showToast('Please fill in title, ingredients and steps', 'warning');
        return;
    }

    const ingredients = ingredientsText.split('\n').filter(line => line.trim());

    showLoading();

    try {
        // 1. Core Analysis (Parallel)
        const [calorieData, difficultyData, timeData, flavorData] = await Promise.all([
            apiCall('/analysis/calories', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ ingredients })
            }),
            apiCall('/analysis/difficulty', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ ingredients, steps })
            }),
            apiCall('/analysis/time', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ steps })
            }),
            apiCall('/analysis/flavor', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ ingredients })
            })
        ]);

        // 2. Suggestions & Comparison (Dependent on core analysis)
        const totalCalories = calorieData.analysis.total_calories;
        const estimatedTime = timeData.analysis.minutes;

        const [suggestionsData, comparisonData] = await Promise.all([
            apiCall('/suggestions', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    ingredients,
                    steps,
                    difficulty: difficultyData.analysis.difficulty,
                    total_calories: totalCalories,
                    servings: calorieData.analysis.servings_estimate
                })
            }),
            apiCall('/analysis/compare', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    cuisine: cuisine,
                    calories: totalCalories,
                    time: estimatedTime
                })
            })
        ]);

        // 3. Display Results
        displayStudioResults({
            calories: totalCalories,
            time: estimatedTime,
            difficulty: difficultyData.analysis.difficulty,
            flavor: flavorData.flavor_profile,
            comparison: comparisonData.comparison,
            suggestions: suggestionsData.suggestions,
            ingredients: ingredients
        });

        // Show Save Button
        dom.saveRecipeBtn.style.display = 'inline-flex';

        // Store current analysis for saving
        state.lastAnalysis = {
            title, cuisine, isVeg, ingredients, steps,
            calories: totalCalories,
            time: estimatedTime,
            difficulty: difficultyData.analysis.difficulty
        };

    } catch (error) {
        console.error(error);
        showToast('Analysis failed: ' + error.message, 'error');
    } finally {
        hideLoading();
    }
}

function displayStudioResults(data) {
    dom.analysisResults.style.display = 'block';

    // Overview
    dom.healthScore.innerText = calculateHealthScore(data.calories, data.ingredients.length);
    dom.resCalories.innerText = data.calories;
    dom.resTime.innerText = data.time;
    dom.resDifficulty.innerText = data.difficulty;

    // Allergens
    const allergens = detectAllergens(data.ingredients);
    if (allergens.length > 0) {
        dom.allergenList.innerHTML = allergens.map(a => `<li>${a}</li>`).join('');
        dom.allergenBox.style.display = 'block';
    } else {
        dom.allergenBox.style.display = 'none';
    }

    // Suggestions
    dom.chefSuggestions.innerHTML = `
        <ul class="info-list">
            ${data.suggestions.serving_tips.slice(0, 3).map(tip => `<li>${tip}</li>`).join('')}
        </ul>
    `;

    // Flavor Radar
    displayFlavorRadar(data.flavor);

    // Comparison
    displayComparison(data.comparison);

    // Scroll to results
    dom.analysisResults.scrollIntoView({ behavior: 'smooth' });
}

// Helper: Calculate mock health score
function calculateHealthScore(calories, ingredientCount) {
    // Simple heuristic: 
    // - High calories = lower score
    // - More ingredients (often implies more whole foods in this context) = higher score
    let score = 100;
    if (calories > 800) score -= 20;
    if (calories > 1200) score -= 20;
    score += Math.min(10, ingredientCount); // Bonus for variety
    return Math.min(100, Math.max(1, score));
}

// Helper: Detect common allergens
function detectAllergens(ingredients) {
    const common = ['peanut', 'nut', 'milk', 'cheese', 'yogurt', 'curd', 'wheat', 'flour', 'soy', 'egg', 'fish', 'prawn', 'shrimp'];
    const found = new Set();
    const text = ingredients.join(' ').toLowerCase();

    common.forEach(alg => {
        if (text.includes(alg)) found.add(alg.charAt(0).toUpperCase() + alg.slice(1));
    });
    return Array.from(found);
}

// Chart: Flavor Radar
function displayFlavorRadar(profile) {
    if (state.charts.flavor) state.charts.flavor.destroy();

    state.charts.flavor = new Chart(dom.flavorRadarChart, {
        type: 'radar',
        data: {
            labels: Object.keys(profile),
            datasets: [{
                label: 'Flavor Profile',
                data: Object.values(profile),
                fill: true,
                backgroundColor: 'rgba(99, 102, 241, 0.2)',
                borderColor: 'rgb(99, 102, 241)',
                pointBackgroundColor: 'rgb(99, 102, 241)',
                pointBorderColor: '#fff',
                pointHoverBackgroundColor: '#fff',
                pointHoverBorderColor: 'rgb(99, 102, 241)'
            }]
        },
        options: {
            elements: { line: { borderWidth: 3 } },
            scales: {
                r: {
                    angleLines: { display: false },
                    suggestedMin: 0,
                    suggestedMax: 10
                }
            }
        }
    });
}

// Comparison Visualization
function displayComparison(comp) {
    // 1. Bar Comparison
    const drawBar = (label, userVal, avgVal, unit) => {
        const max = Math.max(userVal, avgVal) * 1.2;
        const userPct = (userVal / max) * 100;
        const avgPct = (avgVal / max) * 100;

        return `
            <div class="comp-bar-group">
                <label>${label}</label>
                <div class="comp-track mb-2">
                    <div class="comp-fill" style="width: ${userPct}%; background: var(--primary);"></div>
                    <div class="comp-marker" style="left: ${avgPct}%;"></div>
                </div>
                <div class="comp-legend">
                    <span>You: ${userVal} ${unit}</span>
                    <span>Avg: ${avgVal} ${unit}</span>
                </div>
            </div>
        `;
    };

    dom.comparisonBars.innerHTML =
        drawBar('Calories', comp.user.calories, comp.global_avg.calories, 'kcal') +
        drawBar('Cooking Time', comp.user.time, comp.global_avg.time, 'min');

    // 2. Similar Recipes
    dom.similarRecipes.innerHTML = comp.similar_recipes.map(r => `
        <div class="sim-recipe-card">
            <div class="sim-info">
                <h5>${r.name}</h5>
                <div class="sim-meta">
                    <span><i class="fas fa-fire"></i> ${r.calories}</span>
                    <span class="ml-2"><i class="fas fa-clock"></i> ${r.time}m</span>
                </div>
            </div>
            <span class="badge badge-${(r.difficulty || 'medium').toLowerCase()}">${r.difficulty}</span>
        </div>
    `).join('');
}

// ===== SAVE RECIPE =====
async function saveRecipe() {
    if (!state.lastAnalysis) return;

    const recipeData = {
        RecipeName: state.lastAnalysis.title,
        Cuisine: state.lastAnalysis.cuisine,
        IsVegetarian: state.lastAnalysis.isVeg,
        Ingredients: state.lastAnalysis.ingredients,
        Instructions: state.lastAnalysis.steps, // raw string is needed? No, backend expects raw
        Calories: state.lastAnalysis.calories,
        TotalTimeInMins: state.lastAnalysis.time,
        Difficulty: state.lastAnalysis.difficulty
    };

    // Fix: backend expects 'Instructions' as string if it splits it, 
    // Use the raw input from the form since state.lastAnalysis.steps is the array split from form
    // Let's grab raw directly from DOM to be safe
    recipeData.Instructions = dom.stepsInput.value;

    showLoading();
    try {
        await apiCall('/recipes', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(recipeData)
        });

        showToast('Recipe Published Successfully! 🎉', 'success');
        dom.saveRecipeBtn.style.display = 'none'; // Prevent double save

        // Clear form
        dom.analyzeForm.reset();
        dom.analysisResults.style.display = 'none';

    } catch (error) {
        showToast(error.message, 'error');
    } finally {
        hideLoading();
    }
}

// ===== STATISTICS =====
async function loadStatistics() {
    showLoading();

    try {
        const [statsData, vizData] = await Promise.all([
            apiCall('/statistics'),
            apiCall('/visualization/stats')
        ]);

        displayStatsSummary(statsData.statistics);
        displayCharts(vizData.visualization);

    } catch (error) {
        showToast('Failed to load statistics', 'error');
    } finally {
        hideLoading();
    }
}

function displayStatsSummary(stats) {
    dom.statsSummary.innerHTML = `
        <div class="stat-card">
            <i class="fas fa-book"></i>
            <h3>${stats.total_recipes.toLocaleString()}</h3>
            <p>Total Recipes</p>
        </div>
        <div class="stat-card">
            <i class="fas fa-fire"></i>
            <h3>${Math.round(stats.calorie_stats.avg_calories || 0)}</h3>
            <p>Avg Calories</p>
        </div>
        <div class="stat-card">
            <i class="fas fa-clock"></i>
            <h3>${Math.round(stats.time_stats.avg_time || 0)} min</h3>
            <p>Avg Time</p>
        </div>
        <div class="stat-card">
            <i class="fas fa-globe"></i>
            <h3>${Object.keys(stats.cuisine_distribution).length}</h3>
            <p>Cuisines</p>
        </div>
    `;
}

function displayCharts(vizData) {
    // Difficulty Chart
    if (vizData.difficulty && dom.difficultyChart) {
        // Destroy existing chart if it exists
        if (state.charts.difficulty) {
            state.charts.difficulty.destroy();
        }

        state.charts.difficulty = new Chart(dom.difficultyChart, {
            type: 'bar',
            data: {
                labels: vizData.difficulty.labels,
                datasets: [{
                    label: 'Recipes by Difficulty',
                    data: vizData.difficulty.data,
                    backgroundColor: [
                        'rgba(16, 185, 129, 0.7)',
                        'rgba(245, 158, 11, 0.7)',
                        'rgba(239, 68, 68, 0.7)'
                    ],
                    borderColor: [
                        'rgb(16, 185, 129)',
                        'rgb(245, 158, 11)',
                        'rgb(239, 68, 68)'
                    ],
                    borderWidth: 2
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false }
                }
            }
        });
    }

    // Cuisine Chart
    if (vizData.cuisine && dom.cuisineChart) {
        // Destroy existing chart if it exists
        if (state.charts.cuisine) {
            state.charts.cuisine.destroy();
        }

        state.charts.cuisine = new Chart(dom.cuisineChart, {
            type: 'doughnut',
            data: {
                labels: vizData.cuisine.labels,
                datasets: [{
                    label: 'Recipes by Cuisine',
                    data: vizData.cuisine.data,
                    backgroundColor: [
                        'rgba(99, 102, 241, 0.7)',
                        'rgba(139, 92, 246, 0.7)',
                        'rgba(236, 72, 153, 0.7)',
                        'rgba(16, 185, 129, 0.7)',
                        'rgba(245, 158, 11, 0.7)',
                        'rgba(239, 68, 68, 0.7)',
                        'rgba(59, 130, 246, 0.7)',
                        'rgba(168, 85, 247, 0.7)',
                        'rgba(251, 146, 60, 0.7)',
                        'rgba(34, 197, 94, 0.7)'
                    ],
                    borderWidth: 2,
                    borderColor: '#fff'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false
            }
        });
    }
}

// ===== FAVORITES =====
async function displayFavorites() {
    if (state.favorites.length === 0) {
        dom.favoritesGrid.innerHTML = '';
        dom.noFavorites.style.display = 'block';
        return;
    }

    dom.noFavorites.style.display = 'none';
    showLoading();

    try {
        const recipes = await Promise.all(
            state.favorites.map(fav =>
                apiCall(`/recipe/id/${fav.id}`).then(data => data.recipe).catch(() => null)
            )
        );

        const validRecipes = recipes.filter(r => r !== null);
        displayRecipes(validRecipes, dom.favoritesGrid);

    } catch (error) {
        dom.favoritesGrid.innerHTML = '<p class="error">Failed to load favorites</p>';
    } finally {
        hideLoading();
    }
}

// ===== UI HELPERS =====
function showLoading() {
    dom.loadingOverlay.style.display = 'flex';
}

function hideLoading() {
    dom.loadingOverlay.style.display = 'none';
}

function showToast(message, type = 'success') {
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.textContent = message;

    document.body.appendChild(toast);

    setTimeout(() => toast.classList.add('show'), 100);

    setTimeout(() => {
        toast.classList.remove('show');
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

// ===== START APPLICATION =====
document.addEventListener('DOMContentLoaded', init);

// Expose functions globally for inline onclick handlers
window.loadRecipes = loadRecipes;
window.showRecipeDetail = showRecipeDetail;
window.toggleFavorite = toggleFavorite;
