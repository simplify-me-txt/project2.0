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
    activeFilters: {}
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
    
    // Analyze Form
    analyzeForm: document.getElementById('analyzeForm'),
    ingredientsInput: document.getElementById('ingredientsInput'),
    stepsInput: document.getElementById('stepsInput'),
    analysisResults: document.getElementById('analysisResults'),
    
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
    switch(viewName) {
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
async function loadCuisines() {
    try {
        const data = await apiCall('/cuisines');
        state.cuisines = data.cuisines;
        
        const select = document.getElementById('filterCuisine');
        select.innerHTML = '<option value="">All Cuisines</option>';
        
        data.cuisines.forEach(cuisine => {
            select.innerHTML += `<option value="${cuisine}">${cuisine}</option>`;
        });
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
function displayRecipes(recipes) {
    if (!recipes || recipes.length === 0) {
        dom.recipeGrid.innerHTML = `
            <div class="empty-state">
                <i class="fas fa-search"></i>
                <p>No recipes found</p>
            </div>
        `;
        return;
    }
    
    dom.recipeGrid.innerHTML = recipes.map(recipe => `
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
async function handleAnalyze(e) {
    e.preventDefault();
    
    const ingredientsText = dom.ingredientsInput.value.trim();
    const steps = dom.stepsInput.value.trim();
    
    if (!ingredientsText || !steps) {
        showToast('Please fill in both ingredients and steps', 'error');
        return;
    }
    
    const ingredients = ingredientsText.split('\n').filter(line => line.trim());
    
    showLoading();
    
    try {
        // Call analysis APIs
        const [calorieData, difficultyData, timeData] = await Promise.all([
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
            })
        ]);
        
        const suggestionsData = await apiCall('/suggestions', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                ingredients,
                steps,
                difficulty: difficultyData.analysis.difficulty,
                total_calories: calorieData.analysis.total_calories,
                servings: calorieData.analysis.servings_estimate
            })
        });
        
        displayAnalysisResults({
            calories: calorieData.analysis,
            difficulty: difficultyData.analysis,
            time: timeData.analysis,
            suggestions: suggestionsData.suggestions
        });
        
    } catch (error) {
        showToast('Analysis failed', 'error');
    } finally {
        hideLoading();
    }
}

function displayAnalysisResults(analysis) {
    dom.analysisResults.innerHTML = `
        <h3>📊 Analysis Results</h3>
        
        <div class="stat-grid">
            <div class="stat-box">
                <div class="stat-label">Total Calories</div>
                <div class="stat-value">${analysis.calories.total_calories} <span class="stat-unit">kcal</span></div>
            </div>
            <div class="stat-box">
                <div class="stat-label">Difficulty</div>
                <div class="stat-value">
                    <span class="badge badge-${analysis.difficulty.difficulty.toLowerCase()}">${analysis.difficulty.difficulty}</span>
                </div>
            </div>
            <div class="stat-box">
                <div class="stat-label">Cooking Time</div>
                <div class="stat-value">${analysis.time.time_display}</div>
            </div>
            <div class="stat-box">
                <div class="stat-label">Servings</div>
                <div class="stat-value">${analysis.calories.servings_estimate}</div>
            </div>
        </div>
        
        <div class="analysis-section">
            <h4>🔥 Calorie Breakdown</h4>
            <div class="breakdown-table">
                <table>
                    <thead>
                        <tr>
                            <th>Ingredient</th>
                            <th>Grams</th>
                            <th>Calories</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${analysis.calories.breakdown.map(item => `
                            <tr>
                                <td>${item.ingredient}</td>
                                <td>${item.estimated_grams}g</td>
                                <td>${item.calories} kcal</td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            </div>
        </div>
        
        <div class="analysis-section">
            <h4>🎯 Difficulty Analysis</h4>
            <p>${analysis.difficulty.description}</p>
            <ul class="info-list">
                ${analysis.difficulty.factors.map(f => `<li>${f}</li>`).join('')}
            </ul>
        </div>
        
        <div class="analysis-section">
            <h4>💡 Suggestions</h4>
            <p><strong>Diet Type:</strong> ${analysis.suggestions.diet_type}</p>
            <p><strong>Meal Type:</strong> ${analysis.suggestions.meal_type}</p>
            
            ${analysis.suggestions.healthy_alternatives.length > 0 ? `
                <div class="suggestion-box">
                    <h5>Healthy Alternatives:</h5>
                    <ul>
                        ${analysis.suggestions.healthy_alternatives.map(alt => `<li>${alt}</li>`).join('')}
                    </ul>
                </div>
            ` : ''}
            
            <div class="suggestion-box">
                <h5>Serving Tips:</h5>
                <ul>
                    ${analysis.suggestions.serving_tips.map(tip => `<li>${tip}</li>`).join('')}
                </ul>
            </div>
        </div>
    `;
    
    dom.analysisResults.style.display = 'block';
    dom.analysisResults.scrollIntoView({ behavior: 'smooth' });
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
        new Chart(dom.difficultyChart, {
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
        new Chart(dom.cuisineChart, {
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
        displayRecipes(validRecipes);
        
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
