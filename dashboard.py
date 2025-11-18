import dash
from dash import dcc, html, dash_table, Input, Output, callback
import pandas as pd
import os
import plotly.express as px
from dash.dash import no_update

# Инициализация приложения
app = dash.Dash(__name__)

# Конфигурация путей
DATA_DIR = 'Results'

# Словарь с размерностями
DIMENSIONS = {
    'jg': 'm/s',
    'jl': 'm/s',
    'B': 'm',
    'DpDz': 'Pa/m',
    'G': 'kg/m²s',
    'T': '°C',
    'Re liquid': '',
    'Re gas': '',
    'x': ''
}

# Словарь с отображаемыми названиями параметров
PARAM_DISPLAY_NAMES = {
    'T': 'T, °C',
    'G': 'G, kg/m²s',
}

# Обновленная цветовая схема для лучшей доступности и удобства
COLORS = {
    'background': '#0f0f1a',
    'card_background': '#1a1a2e',
    'primary': '#4facfe',
    'secondary': '#00c3ff',
    'accent': '#a020f0',
    'text': '#f0f0f0',
    'text_secondary': '#b0b0c0',
    'border': 'rgba(255, 255, 255, 0.15)',
    'header_bg': 'rgba(79, 172, 254, 0.1)',
    'hover': '#252542',
    'grid_lines': 'rgba(255, 255, 255, 0.08)',
    'card_border': '1px solid rgba(255, 255, 255, 0.1)',
    'card_shadow': '0 8px 20px rgba(0, 0, 0, 0.4)',
    'dropdown_bg': '#252542',
    'dropdown_border': '1px solid rgba(255, 255, 255, 0.15)',
    'success': '#00d4aa',
    'warning': '#ffaa00',
    'error': '#ff4757',
    'table_header': '#2d2d4a',
    'table_even': 'rgba(79, 172, 254, 0.03)',
    'table_odd': 'rgba(160, 32, 240, 0.03)',
    'dropdown_menu_bg': '#1a1a2e',
    'dropdown_option_hover': '#2d2d4a'
}

# Функция для получения доступных опций
def get_substances():
    if not os.path.exists(DATA_DIR):
        return []
    
    substances = []
    for item in os.listdir(DATA_DIR):
        if os.path.isdir(os.path.join(DATA_DIR, item)):
            substances.append(item)
    
    substances.sort()
    return substances

# Функция для форматирования названий колонок с размерностями
def format_column_name(col):
    if col in DIMENSIONS and DIMENSIONS[col]:
        return f"{col} ({DIMENSIONS[col]})"
    return col

# Функция для форматирования названий параметров
def format_param_name(param):
    if param in PARAM_DISPLAY_NAMES:
        return PARAM_DISPLAY_NAMES[param]
    elif param in DIMENSIONS and DIMENSIONS[param]:
        return f"{param}, {DIMENSIONS[param]}"
    return param

# Функция для форматирования значения режима с размерностью
def format_mode_value(param, value):
    if param in DIMENSIONS and DIMENSIONS[param]:
        return f"{value} {DIMENSIONS[param]}"
    return str(value)

# Базовая структура приложения
app.layout = html.Div([
    html.Div([
        html.H1("Исследование гидродинамических характеристик", 
                style={
                    'textAlign': 'center', 
                    'marginBottom': 30,
                    'color': COLORS['text'],
                    'fontWeight': '600',
                    'fontSize': '2.2rem',
                    'padding': '15px 0',
                    'borderBottom': f"1px solid {COLORS['border']}",
                    'textShadow': '0 2px 10px rgba(0, 0, 0, 0.3)',
                }),
        
        # Первая строка - вещество, параметр, режим
        html.Div([
            html.Div([
                html.Label("Выберите вещество", 
                          style={'fontWeight': '600', 'color': COLORS['text'], 'marginBottom': '8px', 'textAlign': 'center', 'fontSize': '14px'}),
                dcc.Dropdown(
                    id='substance-dropdown',
                    options=[{'label': s, 'value': s} for s in get_substances()],
                    value=get_substances()[0] if get_substances() else None,
                    clearable=False,
                    style={
                        'border': COLORS['dropdown_border'],
                        'borderRadius': '10px',
                        'backgroundColor': COLORS['dropdown_bg'],
                        'color': COLORS['text'],
                        'padding': '8px',
                        'fontSize': '14px',
                    }
                ),
            ], style={'width': '32%', 'display': 'inline-block', 'padding': '15px', 'textAlign': 'center'}),
            
            html.Div([
                html.Label("Параметр", 
                          style={'fontWeight': '600', 'color': COLORS['text'], 'marginBottom': '8px', 'textAlign': 'center', 'fontSize': '14px'}),
                dcc.Dropdown(
                    id='param-dropdown',
                    clearable=False,
                    style={
                        'border': COLORS['dropdown_border'],
                        'borderRadius': '10px',
                        'backgroundColor': COLORS['dropdown_bg'],
                        'color': COLORS['text'],
                        'padding': '8px',
                        'fontSize': '14px',
                    }
                ),
            ], style={'width': '32%', 'display': 'inline-block', 'padding': '15px', 'textAlign': 'center'}),
            
            html.Div([
                html.Label("Режим", 
                          style={'fontWeight': '600', 'color': COLORS['text'], 'marginBottom': '8px', 'textAlign': 'center', 'fontSize': '14px'}),
                dcc.Dropdown(
                    id='mode-dropdown',
                    clearable=False,
                    style={
                        'border': COLORS['dropdown_border'],
                        'borderRadius': '10px',
                        'backgroundColor': COLORS['dropdown_bg'],
                        'color': COLORS['text'],
                        'padding': '8px',
                        'fontSize': '14px',
                    }
                ),
            ], style={'width': '32%', 'display': 'inline-block', 'padding': '15px', 'textAlign': 'center'}),
        ], style={
            'backgroundColor': COLORS['card_background'],
            'borderRadius': '12px',
            'boxShadow': COLORS['card_shadow'],
            'marginBottom': '20px',
            'border': COLORS['card_border'],
            'textAlign': 'center',
            'padding': '20px',
        }),
        
        # Вторая строка - оси X и Y
        html.Div([
            html.Div([
                html.Label("Ось X", 
                          style={'fontWeight': '600', 'color': COLORS['text'], 'marginBottom': '8px', 'textAlign': 'center', 'fontSize': '14px'}),
                dcc.Dropdown(
                    id='x-axis-dropdown',
                    clearable=False,
                    style={
                        'border': COLORS['dropdown_border'],
                        'borderRadius': '10px',
                        'backgroundColor': COLORS['dropdown_bg'],
                        'color': COLORS['text'],
                        'padding': '8px',
                        'fontSize': '14px',
                    }
                ),
            ], style={'width': '48%', 'display': 'inline-block', 'padding': '15px', 'textAlign': 'center'}),
            
            html.Div([
                html.Label("Ось Y", 
                          style={'fontWeight': '600', 'color': COLORS['text'], 'marginBottom': '8px', 'textAlign': 'center', 'fontSize': '14px'}),
                dcc.Dropdown(
                    id='y-axis-dropdown',
                    clearable=False,
                    style={
                        'border': COLORS['dropdown_border'],
                        'borderRadius': '10px',
                        'backgroundColor': COLORS['dropdown_bg'],
                        'color': COLORS['text'],
                        'padding': '8px',
                        'fontSize': '14px',
                    }
                ),
            ], style={'width': '48%', 'display': 'inline-block', 'padding': '15px', 'textAlign': 'center'}),
        ], style={
            'backgroundColor': COLORS['card_background'],
            'borderRadius': '12px',
            'boxShadow': COLORS['card_shadow'],
            'marginBottom': '30px',
            'border': COLORS['card_border'],
            'textAlign': 'center',
            'padding': '20px',
        }),
        
        # Основной контент - график и таблица с одинаковой высотой
        html.Div([
            # График
            html.Div([
                html.Div([
                    dcc.Graph(id='data-plot', style={'height': '680px'})
                ], style={
                    'backgroundColor': COLORS['card_background'],
                    'borderRadius': '12px',
                    'boxShadow': COLORS['card_shadow'],
                    'padding': '25px',
                    'border': COLORS['card_border'],
                    'height': '720px',
                    'textAlign': 'center',
                })
            ], style={'width': '68%', 'display': 'inline-block', 'verticalAlign': 'top', 'paddingRight': '20px'}),
            
            # Таблица
            html.Div([
                html.Div([
                    html.H3("Исходные данные", 
                           style={
                               'textAlign': 'center', 
                               'marginBottom': '20px',
                               'color': COLORS['text'],
                               'fontWeight': '600',
                               'fontSize': '1.3rem',
                               'padding': '10px 0',
                               'borderBottom': f"1px solid {COLORS['border']}"
                           }),
                    dash_table.DataTable(
                        id='data-table',
                        page_action='none',
                        style_table={
                            'overflowX': 'auto', 
                            'height': '650px',
                            'overflowY': 'auto',
                            'fontSize': '13px',
                            'width': '100%',
                            'borderRadius': '8px',
                            'backgroundColor': 'transparent',
                            'border': 'none'
                        },
                        style_cell={
                            'textAlign': 'center',
                            'padding': '12px',
                            'minWidth': '80px', 
                            'width': '80px', 
                            'maxWidth': '100px',
                            'whiteSpace': 'normal',
                            'fontSize': '12px',
                            'overflow': 'hidden',
                            'textOverflow': 'ellipsis',
                            'backgroundColor': 'transparent',
                            'color': COLORS['text'],
                            'border': 'none',
                            'fontWeight': '500',
                            'transition': 'all 0.3s ease'
                        },
                        style_header={
                            'backgroundColor': COLORS['table_header'],
                            'color': COLORS['text'],
                            'fontWeight': '600',
                            'fontSize': '13px',
                            'padding': '12px',
                            'border': 'none',
                            'textAlign': 'center',
                            'borderBottom': f"1px solid {COLORS['border']}"
                        },
                        style_data={
                            'border': 'none',
                            'color': COLORS['text'],
                            'borderBottom': '1px solid rgba(255, 255, 255, 0.05)'
                        },
                        style_data_conditional=[
                            {
                                'if': {'state': 'selected'},
                                'backgroundColor': COLORS['hover'],
                                'border': f"2px solid {COLORS['primary']}"
                            },
                            {
                                'if': {'column_id': '№'},
                                'fontWeight': '600',
                                'color': COLORS['primary'],
                                'backgroundColor': COLORS['table_header']
                            }
                        ],
                        style_as_list_view=True
                    )
                ], style={
                    'backgroundColor': COLORS['card_background'],
                    'borderRadius': '12px',
                    'boxShadow': COLORS['card_shadow'],
                    'padding': '25px',
                    'border': COLORS['card_border'],
                    'height': '720px',
                    'textAlign': 'center',
                })
            ], style={'width': '30%', 'display': 'inline-block', 'verticalAlign': 'top'})
        ])
    ], style={
        'backgroundColor': COLORS['background'],
        'minHeight': '100vh',
        'padding': '30px',
        'fontFamily': '"Segoe UI", "Inter", -apple-system, BlinkMacSystemFont, sans-serif',
        'backgroundImage': 'radial-gradient(circle at 10% 20%, rgba(15, 15, 26, 0.8) 0%, rgba(10, 10, 20, 1) 100%)',
        'color': COLORS['text']
    })
])

# Callback для обновления параметров
@callback(
    [Output('param-dropdown', 'options'),
     Output('param-dropdown', 'value')],
    Input('substance-dropdown', 'value')
)
def update_param_options(selected_substance):
    if not selected_substance:
        return [], None
        
    substance_path = os.path.join(DATA_DIR, selected_substance)
    if not os.path.exists(substance_path):
        return [], None
        
    params = []
    for item in os.listdir(substance_path):
        if os.path.isdir(os.path.join(substance_path, item)):
            params.append(item)
    
    params.sort()
    options = [{'label': format_param_name(p), 'value': p} for p in params]
    value = params[0] if params else None
    return options, value

# Callback для обновления режимов
@callback(
    [Output('mode-dropdown', 'options'),
     Output('mode-dropdown', 'value')],
    [Input('substance-dropdown', 'value'),
     Input('param-dropdown', 'value')]
)
def update_mode_options(selected_substance, selected_param):
    if not selected_substance or not selected_param:
        return [], None
        
    param_path = os.path.join(DATA_DIR, selected_substance, selected_param)
    if not os.path.exists(param_path):
        return [], None
    
    modes = []
    for file in os.listdir(param_path):
        if file.endswith('.csv'):
            mode_name = file.replace('.csv', '')
            try:
                modes.append(float(mode_name))
            except ValueError:
                modes.append(mode_name)
    
    modes.sort()
    param_display_name = format_param_name(selected_param)
    options = [{'label': f"{param_display_name} = {format_mode_value(selected_param, m)}", 'value': m} for m in modes]
    value = modes[0] if modes else None
    return options, value

# Callback для обновления доступных колонок для осей
@callback(
    [Output('x-axis-dropdown', 'options'),
     Output('x-axis-dropdown', 'value'),
     Output('y-axis-dropdown', 'options'),
     Output('y-axis-dropdown', 'value')],
    [Input('substance-dropdown', 'value'),
     Input('param-dropdown', 'value'),
     Input('mode-dropdown', 'value')]
)
def update_axis_options(selected_substance, selected_param, selected_mode):
    if not all([selected_substance, selected_param, selected_mode]):
        return [], None, [], None
    
    file_path = os.path.join(DATA_DIR, selected_substance, selected_param, f"{selected_mode}.csv")
    
    try:
        df = pd.read_csv(file_path)
        if 'Substance' in df.columns:
            df = df.drop('Substance', axis=1)
        df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
        
        columns = df.columns.tolist()
        
        options = [{'label': format_column_name(col), 'value': col} for col in columns]
        
        x_value = columns[0] if len(columns) > 0 else None
        y_value = columns[1] if len(columns) > 1 else None
        
        return options, x_value, options, y_value
        
    except Exception as e:
        print(f"Error reading file: {e}")
        return [], None, [], None

# Функция для получения пути к файлу
def get_file_path(selected_substance, selected_param, selected_mode):
    return os.path.join(DATA_DIR, selected_substance, selected_param, f"{selected_mode}.csv")

# Основной callback для обновления графика и таблицы
@callback(
    [Output('data-plot', 'figure'),
     Output('data-table', 'data'),
     Output('data-table', 'columns'),
     Output('data-table', 'style_data_conditional')],
    [Input('substance-dropdown', 'value'),
     Input('param-dropdown', 'value'),
     Input('mode-dropdown', 'value'),
     Input('x-axis-dropdown', 'value'),
     Input('y-axis-dropdown', 'value')]
)
def update_content(selected_substance, selected_param, selected_mode, x_axis, y_axis):
    if not all([selected_substance, selected_param, selected_mode, x_axis, y_axis]):
        return {}, [], [], []
    
    file_path = get_file_path(selected_substance, selected_param, selected_mode)
    
    try:
        df = pd.read_csv(file_path)
        if 'Substance' in df.columns:
            df = df.drop('Substance', axis=1)
        df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
        
        df_with_index = df.copy()
        df_with_index.insert(0, '№', range(1, len(df_with_index) + 1))
        
    except Exception as e:
        print(f"Error reading file: {e}")
        return {}, [], [], []
    
    # Строим график с выбранными осями
    try:
        x_axis_formatted = format_column_name(x_axis)
        y_axis_formatted = format_column_name(y_axis)
        
        param_display_name = format_param_name(selected_param)
        mode_display_value = format_mode_value(selected_param, selected_mode)
        
        fig = px.line(df, x=x_axis, y=y_axis, 
                     title=f"{y_axis_formatted} vs {x_axis_formatted}<br>{selected_substance} ({param_display_name} = {mode_display_value})")
        
        # Стилизация графика для темной темы с улучшенной контрастностью
        fig.update_layout(
            xaxis_title=x_axis_formatted,
            yaxis_title=y_axis_formatted,
            title_x=0.5,
            height=650,
            margin=dict(l=60, r=40, t=80, b=60),
            plot_bgcolor=COLORS['card_background'],
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color=COLORS['text'], size=13),
            title_font_size=16,
            title_font_color=COLORS['text'],
            xaxis=dict(
                gridcolor=COLORS['grid_lines'],
                linecolor=COLORS['border'],
                zerolinecolor=COLORS['border'],
                title_font=dict(size=14, color=COLORS['text'], weight=500),
                tickfont=dict(size=12, color=COLORS['text_secondary']),
                showgrid=True,
                gridwidth=1,
                linewidth=1
            ),
            yaxis=dict(
                gridcolor=COLORS['grid_lines'],
                linecolor=COLORS['border'],
                zerolinecolor=COLORS['border'],
                title_font=dict(size=14, color=COLORS['text'], weight=500),
                tickfont=dict(size=12, color=COLORS['text_secondary']),
                showgrid=True,
                gridwidth=1,
                linewidth=1
            ),
            hoverlabel=dict(
                bgcolor=COLORS['dropdown_bg'],
                font_size=12,
                font_family="Arial",
                font_color=COLORS['text']
            ),
            hovermode="x unified"
        )
        
        # Стилизация линий графика с улучшенной видимостью
        fig.update_traces(
            mode='lines+markers',
            line=dict(width=2.5, color=COLORS['primary']),
            marker=dict(size=4, color=COLORS['accent']),
            hovertemplate="<b>%{x}:</b> %{y}<extra></extra>"
        )
        
    except Exception as e:
        print(f"Error creating plot: {e}")
        fig = px.line(title="Ошибка построения графика")
    
    # Создаем колонки для таблицы с форматированными названиями
    columns = [{"name": "№", "id": "№"}] + [{"name": format_column_name(col), "id": col} for col in df.columns]
    
    # Создаем стили для выделения выбранных колонок и чередования строк
    style_conditional = [
        {
            'if': {'state': 'selected'},
            'backgroundColor': COLORS['hover'],
            'border': f"2px solid {COLORS['primary']}"
        },
        {
            'if': {'column_id': '№'},
            'fontWeight': '600',
            'color': COLORS['primary'],
            'backgroundColor': COLORS['table_header']
        },
        {
            'if': {'row_index': 'odd'},
            'backgroundColor': COLORS['table_odd']
        },
        {
            'if': {'row_index': 'even'},
            'backgroundColor': COLORS['table_even']
        },
        {
            'if': {'column_id': x_axis},
            'borderLeft': f"3px solid {COLORS['primary']}",
            'backgroundColor': 'rgba(79, 172, 254, 0.2)'
        },
        {
            'if': {'column_id': y_axis},
            'borderLeft': f"3px solid {COLORS['accent']}",
            'backgroundColor': 'rgba(160, 32, 240, 0.2)'
        }
    ]
    
    return fig, df_with_index.to_dict('records'), columns, style_conditional

# Функция для запуска дашборда
def run_dashboard(port=8050, host='127.0.0.1', open_browser=True, debug=False):
    """Запускает дашборд с указанными параметрами"""
    import webbrowser
    import threading
    import time
    
    def open_browser_delayed():
        """Открывает браузер с задержкой после запуска сервера"""
        time.sleep(3)
        webbrowser.open_new(f"http://{host}:{port}/")
    
    if open_browser:
        # Запускаем браузер в отдельном потоке
        browser_thread = threading.Thread(target=open_browser_delayed)
        browser_thread.daemon = True
        browser_thread.start()
    
    print(f"🚀 Дашборд запущен на http://{host}:{port}")
    print("⏹️  Для остановки нажмите Ctrl+C")
    
    try:
        app.run(debug=debug, port=port, host=host)
    except Exception as e:
        print(f"❌ Ошибка при запуске: {e}")
        return False
    
    return True

# Добавляем CSS для стилизации выпадающих списков
app.index_string = '''
<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>{%title%}</title>
        {%favicon%}
        {%css%}
        <style>
            /* Стили для выпадающих списков */
            .Select-control {
                background-color: ''' + COLORS['dropdown_bg'] + ''' !important;
                color: ''' + COLORS['text'] + ''' !important;
                border: ''' + COLORS['dropdown_border'] + ''' !important;
            }
            
            .Select-value-label {
                color: ''' + COLORS['text'] + ''' !important;
            }
            
            .Select-menu-outer {
                background-color: ''' + COLORS['dropdown_menu_bg'] + ''' !important;
                border: ''' + COLORS['dropdown_border'] + ''' !important;
                z-index: 1000 !important;
            }
            
            .Select-option {
                background-color: ''' + COLORS['dropdown_menu_bg'] + ''' !important;
                color: ''' + COLORS['text'] + ''' !important;
            }
            
            .Select-option.is-focused {
                background-color: ''' + COLORS['dropdown_option_hover'] + ''' !important;
            }
            
            .Select-input > input {
                color: ''' + COLORS['text'] + ''' !important;
            }
            
            /* Стили для плейсхолдера */
            .Select-placeholder {
                color: ''' + COLORS['text_secondary'] + ''' !important;
            }
            
            /* Стили для иконки стрелки */
            .Select-arrow-zone .Select-arrow {
                border-top-color: ''' + COLORS['text_secondary'] + ''' !important;
            }
        </style>
    </head>
    <body>
        {%app_entry%}
        <footer>
            {%config%}
            {%scripts%}
            {%renderer%}
        </footer>
    </body>
</html>
'''

if __name__ == '__main__':
    # Стандартный запуск для разработки
    run_dashboard(debug=True)