"""
Interactive Visualization Module using Plotly
Creates dynamic, responsive charts for recipe analysis
"""
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import json


def create_calorie_chart(breakdown, total_calories):
    """
    Create interactive horizontal bar chart for calorie breakdown
    
    Args:
        breakdown: List of ingredient calorie data
        total_calories: Total calories for the recipe
        
    Returns:
        JSON string of Plotly figure
    """
    if not breakdown or len(breakdown) == 0:
        return None
    
    # Sort by calories and take top 10
    breakdown_sorted = sorted(breakdown, key=lambda x: x['calories'], reverse=True)[:10]
    
    ingredients = [item['ingredient'][:30] for item in breakdown_sorted]
    calories = [item['calories'] for item in breakdown_sorted]
    
    # Create color scale
    colors = px.colors.sequential.Viridis_r[:len(ingredients)]
    
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        y=ingredients,
        x=calories,
        orientation='h',
        marker=dict(
            color=colors,
            line=dict(color='white', width=2)
        ),
        text=calories,
        texttemplate='%{text:.0f} kcal',
        textposition='outside',
        hovertemplate='<b>%{y}</b><br>Calories: %{x:.0f} kcal<extra></extra>'
    ))
    
    fig.update_layout(
        title={
            'text': f'Calorie Breakdown by Ingredient<br><sub>Total: {total_calories} kcal</sub>',
            'x': 0.5,
            'xanchor': 'center',
            'font': {'size': 18, 'color': '#2C3E50'}
        },
        xaxis_title='Calories (kcal)',
        yaxis_title='',
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(family='Arial, sans-serif', size=12),
        height=max(400, len(ingredients) * 40),
        margin=dict(l=150, r=50, t=80, b=50),
        hoverlabel=dict(
            bgcolor='white',
            font_size=12,
            font_family='Arial'
        )
    )
    
    fig.update_xaxes(showgrid=True, gridcolor='rgba(200,200,200,0.2)')
    fig.update_yaxes(showgrid=False)
    
    return json.dumps(fig.to_dict())


def create_analysis_summary_chart(analysis_data):
    """
    Create multi-panel summary dashboard with key metrics
    
    Args:
        analysis_data: Complete analysis dictionary
        
    Returns:
        JSON string of Plotly figure
    """
    # Create subplots
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=(
            'Calories Overview',
            'Difficulty Level',
            'Cooking Time',
            'Diet Type'
        ),
        specs=[
            [{'type': 'indicator'}, {'type': 'indicator'}],
            [{'type': 'indicator'}, {'type': 'indicator'}]
        ],
        vertical_spacing=0.15,
        horizontal_spacing=0.1
    )
    
    # Color scheme
    difficulty_colors = {
        'Beginner': '#10b981',
        'Intermediate': '#f59e0b',
        'Advanced': '#ef4444'
    }
    
    # 1. Total Calories
    fig.add_trace(
        go.Indicator(
            mode='number+delta',
            value=analysis_data['calories']['total'],
            title={'text': 'Total Calories<br><span style="font-size:0.8em">kcal</span>'},
            delta={'reference': 2000, 'relative': False},
            domain={'x': [0, 1], 'y': [0, 1]},
            number={'font': {'size': 40, 'color': '#6366f1'}}
        ),
        row=1, col=1
    )
    
    # 2. Difficulty Level
    difficulty = analysis_data['difficulty']['level']
    diff_color = difficulty_colors.get(difficulty, '#6366f1')
    
    fig.add_trace(
        go.Indicator(
            mode='number+gauge',
            value=analysis_data['difficulty']['score'],
            title={'text': f'Difficulty<br><span style="font-size:0.8em">{difficulty}</span>'},
            gauge={
                'axis': {'range': [0, 10]},
                'bar': {'color': diff_color},
                'bgcolor': 'rgba(200,200,200,0.2)',
                'borderwidth': 2,
                'bordercolor': 'white'
            },
            domain={'x': [0, 1], 'y': [0, 1]}
        ),
        row=1, col=2
    )
    
    # 3. Cooking Time
    fig.add_trace(
        go.Indicator(
            mode='number',
            value=analysis_data['time']['total_minutes'],
            title={'text': f'Cooking Time<br><span style="font-size:0.8em">{analysis_data["time"]["category"]}</span>'},
            number={'suffix': ' min', 'font': {'size': 40, 'color': '#8b5cf6'}},
            domain={'x': [0, 1], 'y': [0, 1]}
        ),
        row=2, col=1
    )
    
    # 4. Per Serving Calories
    fig.add_trace(
        go.Indicator(
            mode='number+delta',
            value=analysis_data['calories']['per_serving'],
            title={'text': 'Per Serving<br><span style="font-size:0.8em">kcal/serving</span>'},
            delta={'reference': 500, 'relative': False},
            number={'font': {'size': 40, 'color': '#ec4899'}},
            domain={'x': [0, 1], 'y': [0, 1]}
        ),
        row=2, col=2
    )
    
    fig.update_layout(
        title={
            'text': 'Recipe Analysis Dashboard',
            'x': 0.5,
            'xanchor': 'center',
            'font': {'size': 20, 'color': '#2C3E50'}
        },
        height=600,
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(family='Arial, sans-serif'),
        margin=dict(t=80, b=40)
    )
    
    return json.dumps(fig.to_dict())


def create_nutrition_pie_chart(analysis_data):
    """
    Create interactive pie chart for calorie distribution
    
    Args:
        analysis_data: Analysis data dictionary
        
    Returns:
        JSON string of Plotly figure
    """
    per_serving = analysis_data['calories']['per_serving']
    daily_intake = 2000
    remaining = max(0, daily_intake - per_serving)
    
    labels = ['This Recipe', 'Remaining Daily Allowance']
    values = [per_serving, remaining]
    colors = ['#6366f1', '#e5e7eb']
    
    fig = go.Figure(data=[go.Pie(
        labels=labels,
        values=values,
        hole=0.4,
        marker=dict(colors=colors, line=dict(color='white', width=2)),
        textinfo='label+percent',
        textposition='outside',
        hovertemplate='<b>%{label}</b><br>%{value} kcal<br>%{percent}<extra></extra>'
    )])
    
    fig.update_layout(
        title={
            'text': f'Daily Calorie Contribution per Serving<br><sub>Based on 2000 kcal daily intake</sub>',
            'x': 0.5,
            'xanchor': 'center',
            'font': {'size': 16, 'color': '#2C3E50'}
        },
        annotations=[dict(
            text=f'{per_serving}<br>kcal',
            x=0.5, y=0.5,
            font_size=24,
            showarrow=False,
            font=dict(color='#6366f1')
        )],
        height=500,
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(family='Arial, sans-serif'),
        showlegend=True,
        legend=dict(
            orientation='h',
            yanchor='bottom',
            y=-0.1,
            xanchor='center',
            x=0.5
        )
    )
    
    return json.dumps(fig.to_dict())


def create_time_breakdown_chart(analysis_data):
    """
    Create chart showing time distribution by cooking methods
    
    Args:
        analysis_data: Analysis data dictionary
        
    Returns:
        JSON string of Plotly figure
    """
    methods = analysis_data['time'].get('methods_detected', [])
    
    if not methods:
        return None
    
    # Estimate time per method (simplified)
    method_times = {
        'bake': 30, 'roast': 45, 'simmer': 25,
        'fry': 10, 'boil': 15, 'steam': 15,
        'grill': 20, 'sauté': 10, 'marinate': 30
    }
    
    times = [method_times.get(m, 15) for m in methods[:5]]
    
    fig = go.Figure(data=[go.Bar(
        x=methods[:5],
        y=times,
        marker=dict(
            color=times,
            colorscale='Viridis',
            showscale=False,
            line=dict(color='white', width=2)
        ),
        text=times,
        texttemplate='%{text} min',
        textposition='outside'
    )])
    
    fig.update_layout(
        title={
            'text': 'Estimated Time by Cooking Method',
            'x': 0.5,
            'xanchor': 'center',
            'font': {'size': 18, 'color': '#2C3E50'}
        },
        xaxis_title='Cooking Method',
        yaxis_title='Time (minutes)',
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        height=400,
        font=dict(family='Arial, sans-serif')
    )
    
    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(showgrid=True, gridcolor='rgba(200,200,200,0.2)')
    
    return json.dumps(fig.to_dict())


def create_ingredient_stats_chart(breakdown):
    """
    Create treemap showing ingredient contribution
    
    Args:
        breakdown: Ingredient breakdown data
        
    Returns:
        JSON string of Plotly figure
    """
    if not breakdown or len(breakdown) == 0:
        return None
    
    # Take top 15 ingredients
    breakdown_sorted = sorted(breakdown, key=lambda x: x['calories'], reverse=True)[:15]
    
    labels = [item['ingredient'][:25] for item in breakdown_sorted]
    parents = [''] * len(labels)
    values = [item['calories'] for item in breakdown_sorted]
    
    fig = go.Figure(go.Treemap(
        labels=labels,
        parents=parents,
        values=values,
        textinfo='label+value+percent parent',
        marker=dict(
            colorscale='Viridis',
            cmid=sum(values)/len(values)
        ),
        hovertemplate='<b>%{label}</b><br>Calories: %{value:.0f}<br>%{percentParent}<extra></extra>'
    ))
    
    fig.update_layout(
        title={
            'text': 'Calorie Contribution Breakdown',
            'x': 0.5,
            'xanchor': 'center',
            'font': {'size': 18, 'color': '#2C3E50'}
        },
        height=500,
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(family='Arial, sans-serif', size=12)
    )
    
    return json.dumps(fig.to_dict())