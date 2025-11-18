import dash
from dash import dcc, html, dash_table, Input, Output, callback
import pandas as pd
import os
import plotly.express as px

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

# Цветовая схема
COLORS = {
   # Основной фон - очень темный серый (почти черный)
    # Выбран потому что:
    # - Меньше нагрузки на глаза
    # - Хороший контраст с белым текстом
    # - Современный вид
    'background': '#1a1a1a',
    
    # Фон карточек - темный серый
    # Выбран потому что:
    # - Создает глубину и отделяет элементы от фона
    # - Достаточно контрастен с основным фоном
    # - Сохраняет темную тему
    'card_background': '#2d2d2d',
    
    # Основной акцентный цвет - яркий голубой
    # Выбран потому что:
    # - Хорошо виден на темном фоне
    # - Ассоциируется с технологиями и данными
    # - Приятен для глаз
    'primary': '#4fc3f7',
    
    # Второстепенный цвет - зеленый
    # Выбран потому что:
    # - Дополняет голубой
    # - Используется для позитивных действий/состояний
    'secondary': '#81c784',
    
    # Акцентный цвет - оранжевый
    # Выбран потому что:
    # - Привлекает внимание к важным элементам
    # - Создает теплый контраст с холодными цветами
    'accent': '#ffb74d',
    
    # Текст - чистый белый
    # Выбран потому что:
    # - Максимальная читаемость на темном фоне
    # - Соответствует стандартам доступности
    'text': '#ffffff',
    
    # Границы - средний серый
    # Выбран потому что:
    # - Достаточно заметен, но не отвлекает
    # - Создает четкие разделения между элементами
    'border': '#555555',
    
    # Фон заголовков таблицы - темно-синий
    # Выбран потому что:
    # - Выделяет заголовки
    # - Сочетается с основной цветовой схемой
    'header_bg': '#1976d2',
    
    # Цвет при наведении - серый
    # Выбран потому что:
    # - Показывает интерактивность
    # - Не слишком яркий, чтобы не отвлекать
    'hover': '#424242',
    
    # Линии сетки - темно-серый
    # Выбран потому что:
    # - Помогает читать график, но не доминирует
    # - Создает subtle направляющие
    'grid_lines': '#444444'
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
        html.H1("Исследование", 
                style={
                    'textAlign': 'center', 
                    'marginBottom': 30,
                    'color': COLORS['text'],
                    'fontWeight': '700',
                    'fontSize': '2.5rem',
                    'textShadow': '0 2px 4px rgba(0,0,0,0.5)'
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
                        'border': f"2px solid {COLORS['border']}",
                        'borderRadius': '8px',
                        'backgroundColor': COLORS['background'],  # Фон селектора как основной фон
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
                        'border': f"2px solid {COLORS['border']}",
                        'borderRadius': '8px',
                        'backgroundColor': COLORS['background'],  # Фон селектора как основной фон
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
                        'border': f"2px solid {COLORS['border']}",
                        'borderRadius': '8px',
                        'backgroundColor': COLORS['background'],  # Фон селектора как основной фон
                    }
                ),
            ], style={'width': '32%', 'display': 'inline-block', 'padding': '15px', 'textAlign': 'center'}),
        ], style={
            'backgroundColor': COLORS['card_background'],
            'borderRadius': '12px',
            'boxShadow': '0 4px 12px rgba(0, 0, 0, 0.5)',
            'marginBottom': '15px',
            'border': f"2px solid {COLORS['border']}",
            'textAlign': 'center'
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
                        'border': f"2px solid {COLORS['border']}",
                        'borderRadius': '8px',
                        'backgroundColor': COLORS['background'],  # Фон селектора как основной фон
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
                        'border': f"2px solid {COLORS['border']}",
                        'borderRadius': '8px',
                        'backgroundColor': COLORS['background'],  # Фон селектора как основной фон
                    }
                ),
            ], style={'width': '48%', 'display': 'inline-block', 'padding': '15px', 'textAlign': 'center'}),
        ], style={
            'backgroundColor': COLORS['card_background'],
            'borderRadius': '12px',
            'boxShadow': '0 4px 12px rgba(0, 0, 0, 0.5)',
            'marginBottom': '25px',
            'border': f"2px solid {COLORS['border']}",
            'textAlign': 'center'
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
                    'boxShadow': '0 4px 12px rgba(0, 0, 0, 0.5)',
                    'padding': '20px',
                    'border': f"2px solid {COLORS['border']}",
                    'height': '720px',
                    'textAlign': 'center'
                })
            ], style={'width': '68%', 'display': 'inline-block', 'verticalAlign': 'top', 'paddingRight': '15px'}),
            
            # Таблица
            html.Div([
                html.Div([
                    html.H3("Исходные данные", 
                           style={
                               'textAlign': 'center', 
                               'marginBottom': '20px',
                               'color': COLORS['text'],
                               'fontWeight': '600',
                               'fontSize': '18px'
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
                            'backgroundColor': COLORS['card_background'],
                            'border': f"2px solid {COLORS['border']}"
                        },
                        style_cell={
                            'textAlign': 'center',
                            'padding': '10px',
                            'minWidth': '80px', 
                            'width': '80px', 
                            'maxWidth': '100px',
                            'whiteSpace': 'normal',
                            'fontSize': '12px',
                            'overflow': 'hidden',
                            'textOverflow': 'ellipsis',
                            'backgroundColor': COLORS['card_background'],
                            'color': COLORS['text'],
                            'border': f"1px solid {COLORS['border']}",
                            'fontWeight': '500'
                        },
                        style_header={
                            'backgroundColor': COLORS['header_bg'],
                            'color': COLORS['text'],
                            'fontWeight': '700',
                            'fontSize': '13px',
                            'padding': '12px',
                            'border': f"2px solid {COLORS['border']}",
                            'textAlign': 'center'
                        },
                        style_data={
                            'border': f"1px solid {COLORS['border']}",
                            'color': COLORS['text']
                        },
                        style_data_conditional=[
                            {
                                'if': {'state': 'selected'},
                                'backgroundColor': COLORS['hover'],
                                'border': f"2px solid {COLORS['primary']}"
                            }
                        ],
                    )
                ], style={
                    'backgroundColor': COLORS['card_background'],
                    'borderRadius': '12px',
                    'boxShadow': '0 4px 12px rgba(0, 0, 0, 0.5)',
                    'padding': '20px',
                    'border': f"2px solid {COLORS['border']}",
                    'height': '720px',
                    'textAlign': 'center'
                })
            ], style={'width': '30%', 'display': 'inline-block', 'verticalAlign': 'top'})
        ])
    ], style={
        'backgroundColor': COLORS['background'],
        'minHeight': '100vh',
        'padding': '30px',
        'fontFamily': '"Segoe UI", "Inter", -apple-system, BlinkMacSystemFont, sans-serif'
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
    
    file_path = get_file_path(selected_substance, selected_param, selected_mode)
    
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
        
        # Стилизация графика для темной темы с лучшей читаемостью
        fig.update_layout(
            xaxis_title=x_axis_formatted,
            yaxis_title=y_axis_formatted,
            title_x=0.5,
            height=650,
            margin=dict(l=50, r=50, t=100, b=50),
            plot_bgcolor=COLORS['card_background'],
            paper_bgcolor=COLORS['card_background'],
            font=dict(color=COLORS['text'], size=14),
            title_font_size=18,
            title_font_color=COLORS['text'],
            xaxis=dict(
                gridcolor=COLORS['grid_lines'],
                linecolor=COLORS['border'],
                zerolinecolor=COLORS['border'],
                title_font=dict(size=14, color=COLORS['text']),
                tickfont=dict(size=12, color=COLORS['text'])
            ),
            yaxis=dict(
                gridcolor=COLORS['grid_lines'],
                linecolor=COLORS['border'],
                zerolinecolor=COLORS['border'],
                title_font=dict(size=14, color=COLORS['text']),
                tickfont=dict(size=12, color=COLORS['text'])
            )
        )
        
        # Стилизация линий графика - БЕЗ ТОЧЕК
        fig.update_traces(
            mode='lines',  # Только линии, без маркеров
            line=dict(width=4, color=COLORS['primary'])  # Цвет и толщина линии
            # Убраны маркеры (точки)
        )
        
    except Exception as e:
        print(f"Error creating plot: {e}")
        fig = px.line(title="Ошибка построения графика")
    
    # Создаем колонки для таблицы с форматированными названиями
    columns = [{"name": "№", "id": "№"}] + [{"name": format_column_name(col), "id": col} for col in df.columns]
    
    # Создаем стили для выделения выбранных колонок
    style_conditional = [
        {
            'if': {'column_id': x_axis},
            'backgroundColor': 'rgba(79, 195, 247, 0.3)',
            'fontWeight': '700',
            'color': COLORS['text']
        },
        {
            'if': {'column_id': y_axis},
            'backgroundColor': 'rgba(255, 183, 77, 0.3)',
            'fontWeight': '700',
            'color': COLORS['text']
        }
    ]
    
    return fig, df_with_index.to_dict('records'), columns, style_conditional

if __name__ == '__main__':
    app.run(debug=True)