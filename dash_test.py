import dash
from dash import dcc, html, dash_table, Input, Output, callback, State
import pandas as pd
import os
import plotly.express as px
from dash.dash import no_update
import numpy as np
from class_DpDz import DpDz  # Импортируем класс для расчетов
import base64
import datetime
import io

# Инициализация приложения
app = dash.Dash(__name__)

# Отключаем окно с ошибками в режиме разработки
app.config.suppress_callback_exceptions = True

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
    'dropdown_option_hover': '#2d2d4a',
    'tab_background': '#1a1a2e',
    'tab_border': '1px solid rgba(255, 255, 255, 0.1)',
    'tab_selected': '#4facfe',
    'tab_hover': '#252542',
    'button_primary': '#4facfe',
    'button_secondary': '#a020f0',
    'input_background': '#252542'
}

# Стили для интерактивного расчета
CALC_STYLES = {
    'label': {
        'fontWeight': '600', 
        'color': COLORS['text'], 
        'marginBottom': '15px', 
        'textAlign': 'center', 
        'fontSize': '14px',
        'display': 'block'
    },
    'input': {
        'width': '25%',
        'padding': '12px',
        'borderRadius': '8px',
        'border': COLORS['dropdown_border'],
        'backgroundColor': COLORS['input_background'],
        'color': COLORS['text'],
        'fontSize': '14px',
        'textAlign': 'center',
        'margin': '0 auto',
        'display': 'block',
        'height': '42px',
        'boxSizing': 'border-box'
    },
    'dropdown': {
        'width': '25%',
        'margin': '0 auto',
    },
    'dropdown_inner': {
        'border': COLORS['dropdown_border'],
        'borderRadius': '8px',
        'backgroundColor': COLORS['input_background'],
        'color': COLORS['text'],
        'fontSize': '14px',
        'height': '42px',
        'padding': '0px 12px',
    },
    'param_container': {
        'width': '100%', 
        'textAlign': 'center', 
        'marginBottom': '25px'
    },
    'range_label': {
        'fontWeight': '500', 
        'color': COLORS['text_secondary'], 
        'marginBottom': '8px', 
        'textAlign': 'center', 
        'fontSize': '12px',
        'display': 'block'
    },
    'range_input': {
        'width': '90%',
        'padding': '10px',
        'borderRadius': '6px',
        'border': COLORS['dropdown_border'],
        'backgroundColor': COLORS['input_background'],
        'color': COLORS['text'],
        'fontSize': '13px',
        'textAlign': 'center',
        'margin': '0 auto',
        'display': 'block'
    }
}

# Функция для создания параметра с полем ввода
def create_input_param(param_id, label_text, input_type='number', placeholder_text='', value=None):
    """Создает параметр с полем ввода"""
    if input_type == 'dropdown':
        return html.Div([
            html.Label(label_text, style=CALC_STYLES['label']),
            dcc.Dropdown(
                id=param_id,
                options=[{'label': s, 'value': s} for s in get_substances()],
                placeholder=placeholder_text,
                style=CALC_STYLES['dropdown']
            ),
        ], style=CALC_STYLES['param_container'])
    else:
        return html.Div([
            html.Label(label_text, style=CALC_STYLES['label']),
            dcc.Input(
                id=param_id,
                type=input_type,
                placeholder=placeholder_text,
                value=value,
                style=CALC_STYLES['input']
            ),
        ], style=CALC_STYLES['param_container'])

# Функция для создания параметра с диапазоном
def create_range_param(start_id, end_id, main_label, start_label="От", end_label="До"):
    """Создает параметр с диапазоном значений"""
    return html.Div([
        html.Label(main_label, style=CALC_STYLES['label']),
        html.Div([
            html.Div([
                html.Label(start_label, style=CALC_STYLES['range_label']),
                dcc.Input(
                    id=start_id,
                    type='number',
                    placeholder='Начальное значение',
                    style=CALC_STYLES['range_input']
                ),
            ], style={'width': '45%', 'display': 'inline-block', 'textAlign': 'center'}),
            
            html.Div([
                html.Label(end_label, style=CALC_STYLES['range_label']),
                dcc.Input(
                    id=end_id,
                    type='number',
                    placeholder='Конечное значение',
                    style=CALC_STYLES['range_input']
                ),
            ], style={'width': '45%', 'display': 'inline-block', 'textAlign': 'center'}),
        ], style={'width': '50%', 'margin': '0 auto', 'textAlign': 'center'}),
    ], style=CALC_STYLES['param_container'])

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

# Функция для генерации имени файла с временной меткой
def generate_filename(substance, timestamp=None):
    if timestamp is None:
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"results_{substance}_{timestamp}.csv"

# Базовая структура приложения
app.layout = html.Div([
    # Скрытый компонент для хранения данных расчета
    dcc.Store(id='calculation-data-store'),
    
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
        
        # Вкладки для переключения между страницами
        dcc.Tabs(id="app-tabs", value='tab-analysis', children=[
            dcc.Tab(
                label='Анализ данных',
                value='tab-analysis',
                style={
                    'backgroundColor': COLORS['tab_background'],
                    'color': COLORS['text_secondary'],
                    'border': COLORS['tab_border'],
                    'padding': '12px 24px',
                    'fontWeight': '500',
                    'borderRadius': '8px 8px 0 0',
                    'marginRight': '5px'
                },
                selected_style={
                    'backgroundColor': COLORS['card_background'],
                    'color': COLORS['text'],
                    'borderBottom': f"3px solid {COLORS['tab_selected']}",
                    'padding': '12px 24px',
                    'fontWeight': '600',
                    'borderRadius': '8px 8px 0 0',
                    'marginRight': '5px'
                }
            ),
            dcc.Tab(
                label='Интерактивный расчет',
                value='tab-calculator',
                style={
                    'backgroundColor': COLORS['tab_background'],
                    'color': COLORS['text_secondary'],
                    'border': COLORS['tab_border'],
                    'padding': '12px 24px',
                    'fontWeight': '500',
                    'borderRadius': '8px 8px 0 0',
                    'marginLeft': '5px'
                },
                selected_style={
                    'backgroundColor': COLORS['card_background'],
                    'color': COLORS['text'],
                    'borderBottom': f"3px solid {COLORS['tab_selected']}",
                    'padding': '12px 24px',
                    'fontWeight': '600',
                    'borderRadius': '8px 8px 0 0',
                    'marginLeft': '5px'
                }
            ),
        ], style={
            'marginBottom': '30px',
            'borderBottom': 'none'
        }),
        
        # Контент вкладок
        html.Div(id='tab-content')
    ], style={
        'backgroundColor': COLORS['background'],
        'minHeight': '100vh',
        'padding': '30px',
        'fontFamily': '"Segoe UI", "Inter", -apple-system, BlinkMacSystemFont, sans-serif',
        'backgroundImage': 'radial-gradient(circle at 10% 20%, rgba(15, 15, 26, 0.8) 0%, rgba(10, 10, 20, 1) 100%)',
        'color': COLORS['text'],
        'margin': '0',
        'width': '100%'
    })
], style={
    'margin': '0',
    'padding': '0',
    'width': '100%',
    'backgroundColor': COLORS['background']
})

# Callback для переключения между вкладками
@app.callback(
    Output('tab-content', 'children'),
    Input('app-tabs', 'value')
)
def render_tab_content(tab):
    if tab == 'tab-analysis':
        return html.Div([
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
                ], style={'width': '68%', 'display': 'inline-block', 'verticalAlign': 'top', 'paddingRight': '10px'}),
                
                # Таблица - ИСПРАВЛЕНА: теперь не выходит за границы
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
                        html.Div([
                            dash_table.DataTable(
                                id='data-table',
                                page_action='none',
                                style_table={
                                    'overflowX': 'auto', 
                                    'height': '650px',
                                    'overflowY': 'auto',
                                    'fontSize': '12px',
                                    'width': '100%',
                                    'borderRadius': '8px',
                                    'backgroundColor': 'transparent',
                                    'border': 'none',
                                    'minWidth': '100%'
                                },
                                style_cell={
                                    'textAlign': 'center',
                                    'padding': '10px',
                                    'minWidth': '70px', 
                                    'width': '70px', 
                                    'maxWidth': '90px',
                                    'whiteSpace': 'normal',
                                    'fontSize': '11px',
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
                                    'fontSize': '12px',
                                    'padding': '10px',
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
                                    },
                                    {
                                        'if': {'row_index': 'odd'},
                                        'backgroundColor': COLORS['table_odd']
                                    },
                                    {
                                        'if': {'row_index': 'even'},
                                        'backgroundColor': COLORS['table_even']
                                    }
                                ],
                                style_as_list_view=True
                            )
                        ], style={
                            'width': '100%',
                            'height': '100%',
                            'overflow': 'hidden'
                        })
                    ], style={
                        'backgroundColor': COLORS['card_background'],
                        'borderRadius': '12px',
                        'boxShadow': COLORS['card_shadow'],
                        'padding': '25px',
                        'border': COLORS['card_border'],
                        'height': '720px',
                        'textAlign': 'center',
                        'display': 'flex',
                        'flexDirection': 'column'
                    })
                ], style={'width': '30%', 'display': 'inline-block', 'verticalAlign': 'top'})
            ], style={'width': '100%', 'display': 'flex', 'justifyContent': 'space-between'})
        ])
    
    elif tab == 'tab-calculator':
        return html.Div([
            html.Div([
                html.H2("Интерактивный расчет", 
                       style={
                           'textAlign': 'center', 
                           'marginBottom': '30px',
                           'color': COLORS['text'],
                           'fontWeight': '600',
                           'fontSize': '1.8rem',
                           'padding': '15px 0',
                           'borderBottom': f"1px solid {COLORS['border']}"
                       }),
                
                # Обязательные параметры
                html.Div([
                    html.H3("Основные параметры", 
                           style={
                               'textAlign': 'center', 
                               'marginBottom': '20px',
                               'color': COLORS['text'],
                               'fontWeight': '600',
                               'fontSize': '1.3rem'
                           }),
                    
                    html.Div([
                        # Вещество
                        create_input_param(
                            'substance-calc-dropdown',
                            'Вещество',
                            'dropdown',
                            'Выберите вещество'
                        ),
                        
                        # Диаметр
                        create_input_param(
                            'd-input',
                            'Диаметр (d), м',
                            'number',
                            'Введите диаметр'
                        ),
                        
                        # Массовый расход
                        create_input_param(
                            'G-input',
                            'Массовый расход (G), кг/м²с',
                            'number',
                            'Введите расход'
                        ),
                        
                        # Температура
                        create_input_param(
                            'T-input',
                            'Температура (T), °C',
                            'number',
                            'Введите температуру'
                        ),
                        
                        # Ускорение свободного падения (теперь обязательный параметр)
                        create_input_param(
                            'g-input',
                            'Ускорение свободного падения (g), м/с²',
                            'number',
                            'Введите ускорение',
                            9.81
                        ),
                        
                        # Количество точек расчета (новый обязательный параметр)
                        create_input_param(
                            'num-points-input',
                            'Количество точек расчета',
                            'number',
                            'Введите количество точек',
                            50
                        ),
                        
                        # Паросодержание (диапазон)
                        create_range_param(
                            'x-start-input',
                            'x-end-input',
                            'Паросодержание (x) - диапазон',
                            'От',
                            'До'
                        ),
                    ]),
                ], style={
                    'backgroundColor': COLORS['card_background'],
                    'borderRadius': '12px',
                    'boxShadow': COLORS['card_shadow'],
                    'border': COLORS['card_border'],
                    'padding': '25px',
                    'marginBottom': '20px'
                }),
                
                # Кнопка для показа дополнительных параметров
                html.Div([
                    html.Button(
                        'Дополнительные параметры',
                        id='toggle-advanced-button',
                        n_clicks=0,
                        style={
                            'width': '25%',
                            'padding': '12px',
                            'borderRadius': '8px',
                            'border': 'none',
                            'backgroundColor': COLORS['button_secondary'],
                            'color': COLORS['text'],
                            'fontSize': '14px',
                            'fontWeight': '600',
                            'cursor': 'pointer',
                            'transition': 'all 0.3s ease',
                            'margin': '0 auto',
                            'display': 'block'
                        }
                    )
                ], style={'marginBottom': '20px', 'textAlign': 'center'}),
                
                # Дополнительные параметры (изначально скрыты)
                html.Div([
                    html.H3("Дополнительные параметры", 
                           style={
                               'textAlign': 'center', 
                               'marginBottom': '20px',
                               'color': COLORS['text'],
                               'fontWeight': '600',
                               'fontSize': '1.3rem'
                           }),
                    
                    html.Div([
                        # Давление (теперь дополнительный параметр)
                        create_input_param(
                            'P-input',
                            'Давление (P), Па',
                            'number',
                            'Введите давление'
                        ),
                        
                        # Коэффициент ki
                        create_input_param(
                            'ki-input',
                            'Коэффициент ki',
                            'number',
                            'Введите коэффициент'
                        ),
                        
                        # Плотность жидкости
                        create_input_param(
                            'liquid-density-input',
                            'Плотность жидкости, кг/м³',
                            'number',
                            'Введите плотность'
                        ),
                        
                        # Вязкость жидкости
                        create_input_param(
                            'liquid-viscosity-input',
                            'Вязкость жидкости, Па·с',
                            'number',
                            'Введите вязкость'
                        ),
                        
                        # Плотность газа
                        create_input_param(
                            'gas-density-input',
                            'Плотность газа, кг/м³',
                            'number',
                            'Введите плотность'
                        ),
                        
                        # Вязкость газа
                        create_input_param(
                            'gas-viscosity-input',
                            'Вязкость газа, Па·с',
                            'number',
                            'Введите вязкость'
                        ),
                        
                        # Скорость жидкости
                        create_input_param(
                            'SV-liquid-input',
                            'Скорость жидкости (SV_liquid), м/с',
                            'number',
                            'Введите скорость'
                        ),
                        
                        # Скорость газа
                        create_input_param(
                            'SV-gas-input',
                            'Скорость газа (SV_gas), м/с',
                            'number',
                            'Введите скорость'
                        ),
                    ]),
                ], id='advanced-params', style={
                    'backgroundColor': COLORS['card_background'],
                    'borderRadius': '12px',
                    'boxShadow': COLORS['card_shadow'],
                    'border': COLORS['card_border'],
                    'padding': '25px',
                    'marginBottom': '20px',
                    'display': 'none'  # Изначально скрыто
                }),
                
                # Кнопка расчета
                html.Div([
                    html.Button(
                        'Выполнить расчет',
                        id='calculate-button',
                        n_clicks=0,
                        style={
                            'width': '25%',
                            'padding': '15px',
                            'borderRadius': '8px',
                            'border': 'none',
                            'backgroundColor': COLORS['button_primary'],
                            'color': COLORS['text'],
                            'fontSize': '16px',
                            'fontWeight': '600',
                            'cursor': 'pointer',
                            'transition': 'all 0.3s ease',
                            'margin': '0 auto',
                            'display': 'block'
                        }
                    )
                ], style={'textAlign': 'center'}),
                
                # Область для вывода результатов
                html.Div(id='calculation-results', style={
                    'marginTop': '30px',
                    'padding': '20px',
                    'backgroundColor': COLORS['card_background'],
                    'borderRadius': '12px',
                    'boxShadow': COLORS['card_shadow'],
                    'border': COLORS['card_border'],
                    'minHeight': '100px',
                    'textAlign': 'center'
                })
            ])
        ])

# Callback для показа/скрытия дополнительных параметров
@app.callback(
    Output('advanced-params', 'style'),
    Input('toggle-advanced-button', 'n_clicks'),
    State('advanced-params', 'style')
)
def toggle_advanced_params(n_clicks, current_style):
    if n_clicks % 2 == 1:
        return {**current_style, 'display': 'block'}
    else:
        return {**current_style, 'display': 'none'}

# Callback для выполнения расчета и сохранения данных
@app.callback(
    [Output('calculation-results', 'children'),
     Output('calculation-data-store', 'data')],
    Input('calculate-button', 'n_clicks'),
    [State('substance-calc-dropdown', 'value'),
     State('d-input', 'value'),
     State('G-input', 'value'),
     State('T-input', 'value'),
     State('g-input', 'value'),
     State('num-points-input', 'value'),
     State('x-start-input', 'value'),
     State('x-end-input', 'value'),
     State('P-input', 'value'),
     State('ki-input', 'value'),
     State('liquid-density-input', 'value'),
     State('liquid-viscosity-input', 'value'),
     State('gas-density-input', 'value'),
     State('gas-viscosity-input', 'value'),
     State('SV-liquid-input', 'value'),
     State('SV-gas-input', 'value')]
)
def perform_calculation(n_clicks, substance, d, G, T, g, num_points, x_start, x_end, P, ki, 
                       liquid_density, liquid_viscosity, gas_density, gas_viscosity, 
                       SV_liquid, SV_gas):
    if n_clicks == 0:
        return html.P("Введите параметры и нажмите 'Выполнить расчет'", 
                     style={'textAlign': 'center', 'color': COLORS['text_secondary']}), no_update
    
    # Проверка обязательных полей
    required_fields = {
        'вещество': substance,
        'диаметр': d,
        'расход': G,
        'температура': T,
        'ускорение свободного падения': g,
        'количество точек расчета': num_points
    }
    
    missing_fields = [name for name, value in required_fields.items() if value is None or value == '']
    
    if missing_fields:
        return html.Div([
            html.H4("Ошибка", style={'color': COLORS['error'], 'textAlign': 'center'}),
            html.P(f"Заполните все обязательные параметры: {', '.join(missing_fields)}",
                  style={'textAlign': 'center', 'color': COLORS['text_secondary']})
        ]), no_update
    
    # Проверка количества точек
    if num_points < 2:
        return html.Div([
            html.H4("Ошибка", style={'color': COLORS['error'], 'textAlign': 'center'}),
            html.P("Количество точек расчета должно быть целым числом больше 1",
                  style={'textAlign': 'center', 'color': COLORS['text_secondary']})
        ]), no_update
    
    # Проверка диапазона паросодержания
    if x_start is None or x_end is None:
        return html.Div([
            html.H4("Ошибка", style={'color': COLORS['error'], 'textAlign': 'center'}),
            html.P("Заполните диапазон паросодержания",
                  style={'textAlign': 'center', 'color': COLORS['text_secondary']})
        ]), no_update
    
    try:
        # Создаем диапазон значений x
        x_values = np.linspace(x_start, x_end, num_points)
        
        # Подготавливаем параметры для расчета
        thermodynamic_params = {
            'Substance': substance,
            'Temperature': T,
            'G': G,
            'x': x_values
        }
        
        # Добавляем опциональные параметры, если они заданы
        if P is not None:
            thermodynamic_params['Pressure'] = P
        if liquid_density is not None:
            thermodynamic_params['Liquid density'] = liquid_density
        if liquid_viscosity is not None:
            thermodynamic_params['Liquid viscosity'] = liquid_viscosity
        if gas_density is not None:
            thermodynamic_params['Gas density'] = gas_density
        if gas_viscosity is not None:
            thermodynamic_params['Gas viscosity'] = gas_viscosity
        if SV_liquid is not None:
            thermodynamic_params['Liquid velocity'] = SV_liquid
        if SV_gas is not None:
            thermodynamic_params['Gas velocity'] = SV_gas
        
        # Создаем экземпляр класса DpDz и выполняем расчет
        # value_fb = True - учитывать скорость на границе раздела фаз
        calculator = DpDz(g=g, d=d, ki=ki, thermodinamic_params=thermodynamic_params, value_fb=True)
        results = calculator.calculate()
        
        # Преобразуем результаты в DataFrame
        if isinstance(results, list):
            # Если результат - список словарей
            results_df = pd.DataFrame(results)
        else:
            # Если результат - одиночный словарь
            results_df = pd.DataFrame([results])
        
        # Убеждаемся, что все необходимые колонки присутствуют
        required_columns = ['x', 'DpDz']
        for col in required_columns:
            if col not in results_df.columns:
                results_df[col] = np.nan
        
    except Exception as e:
        return html.Div([
            html.H4("Ошибка расчета", style={'color': COLORS['error'], 'textAlign': 'center'}),
            html.P(f"Произошла ошибка при выполнении расчета: {str(e)}",
                  style={'textAlign': 'center', 'color': COLORS['text_secondary']})
        ]), no_update
    
    # Строим график DpDz от x
    try:
        fig = px.line(results_df, x='x', y='DpDz', 
                     title=f"Зависимость градиента давления от паросодержания<br>{substance} (G={G} кг/м²с, d={d} м, T={T}°C)")
        
        fig.update_layout(
            xaxis_title="Паросодержание, x",
            yaxis_title="Градиент давления, DpDz (Па/м)",
            title_x=0.5,
            height=500,
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
                title_font=dict(size=14, color=COLORS['text']),
                tickfont=dict(size=12, color=COLORS['text_secondary']),
                showgrid=True,
                gridwidth=1,
                linewidth=1
            ),
            yaxis=dict(
                gridcolor=COLORS['grid_lines'],
                linecolor=COLORS['border'],
                zerolinecolor=COLORS['border'],
                title_font=dict(size=14, color=COLORS['text']),
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
            )
        )
        
        # Стилизация линии графика
        fig.update_traces(
            mode='lines+markers',
            line=dict(width=2.5, color=COLORS['primary']),
            marker=dict(size=4, color=COLORS['accent']),
            hovertemplate="<b>x:</b> %{x:.3f}<br><b>DpDz:</b> %{y:.1f} Па/м<extra></extra>"
        )
        
    except Exception as e:
        fig = px.line(title="Ошибка построения графика")
        print(f"Error creating plot: {e}")
    
    # Подготавливаем данные для таблицы
    table_df = results_df.copy()
    table_df.insert(0, '№', range(1, len(table_df) + 1))
    
    # Форматируем числа для таблицы
    display_df = table_df.copy()
    for col in display_df.columns:
        if col != '№' and col != 'Substance':
            if display_df[col].dtype in [np.float64, np.float32]:
                display_df[col] = display_df[col].round(6)
    
    # Создаем колонки для таблицы
    columns = [{"name": "№", "id": "№"}]
    for col in results_df.columns:
        if col in DIMENSIONS and DIMENSIONS[col]:
            columns.append({"name": f"{col} ({DIMENSIONS[col]})", "id": col})
        else:
            columns.append({"name": col, "id": col})
    
    # Стили для таблицы
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
        }
    ]
    
    # Сводная информация о параметрах расчета
    params_info = f"""
    Параметры расчета:
    - Вещество: {substance}
    - Диаметр: {d} м
    - Массовый расход: {G} кг/м²с
    - Температура: {T} °C
    - Ускорение свободного падения: {g} м/с²
    - Количество точек расчета: {num_points}
    - Диапазон паросодержания: от {x_start} до {x_end}
    """
    
    if P:
        params_info += f"\n- Давление: {P} Па"
    if ki:
        params_info += f"\n- Коэффициент ki: {ki}"
    
    # Сохраняем данные для экспорта
    export_data = {
        'results': results_df.to_dict('records'),
        'params': {
            'substance': substance,
            'd': d,
            'G': G,
            'T': T,
            'g': g,
            'num_points': num_points,
            'x_start': x_start,
            'x_end': x_end,
            'P': P,
            'ki': ki,
            'timestamp': datetime.datetime.now().isoformat()
        }
    }
    
    results_content = html.Div([
        html.H4("Результаты расчета", style={
            'color': COLORS['success'], 
            'textAlign': 'center', 
            'marginBottom': '20px',
            'fontSize': '1.5rem'
        }),
        
        # Информация о параметрах
        html.Div([
            html.H5("Параметры расчета", style={
                'color': COLORS['text'], 
                'marginBottom': '15px',
                'textAlign': 'center'
            }),
            html.P(params_info, style={
                'whiteSpace': 'pre-line', 
                'textAlign': 'left', 
                'padding': '15px 20px',
                'backgroundColor': COLORS['card_background'],
                'borderRadius': '8px',
                'border': COLORS['card_border'],
                'marginBottom': '20px'
            })
        ]),
        
        # График и таблица
        html.Div([
            # График
            html.Div([
                html.Div([
                    dcc.Graph(figure=fig, style={'height': '500px'})
                ], style={
                    'backgroundColor': COLORS['card_background'],
                    'borderRadius': '12px',
                    'boxShadow': COLORS['card_shadow'],
                    'padding': '25px',
                    'border': COLORS['card_border'],
                    'height': '580px',
                    'textAlign': 'center',
                })
            ], style={'width': '68%', 'display': 'inline-block', 'verticalAlign': 'top', 'paddingRight': '10px'}),
            
            # Таблица
            html.Div([
                html.Div([
                    html.H3("Результаты расчета", 
                           style={
                               'textAlign': 'center', 
                               'marginBottom': '20px',
                               'color': COLORS['text'],
                               'fontWeight': '600',
                               'fontSize': '1.3rem',
                               'padding': '10px 0',
                               'borderBottom': f"1px solid {COLORS['border']}"
                           }),
                    html.Div([
                        dash_table.DataTable(
                            data=display_df.to_dict('records'),
                            columns=columns,
                            page_action='none',
                            style_table={
                                'overflowX': 'auto', 
                                'height': '520px',
                                'overflowY': 'auto',
                                'fontSize': '12px',
                                'width': '100%',
                                'borderRadius': '8px',
                                'backgroundColor': 'transparent',
                                'border': 'none',
                                'minWidth': '100%'
                            },
                            style_cell={
                                'textAlign': 'center',
                                'padding': '10px',
                                'minWidth': '70px', 
                                'width': '70px', 
                                'maxWidth': '90px',
                                'whiteSpace': 'normal',
                                'fontSize': '11px',
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
                                'fontSize': '12px',
                                'padding': '10px',
                                'border': 'none',
                                'textAlign': 'center',
                                'borderBottom': f"1px solid {COLORS['border']}"
                            },
                            style_data={
                                'border': 'none',
                                'color': COLORS['text'],
                                'borderBottom': '1px solid rgba(255, 255, 255, 0.05)'
                            },
                            style_data_conditional=style_conditional,
                            style_as_list_view=True
                        )
                    ], style={
                        'width': '100%',
                        'height': '100%',
                        'overflow': 'hidden'
                    })
                ], style={
                    'backgroundColor': COLORS['card_background'],
                    'borderRadius': '12px',
                    'boxShadow': COLORS['card_shadow'],
                    'padding': '25px',
                    'border': COLORS['card_border'],
                    'height': '580px',
                    'textAlign': 'center',
                    'display': 'flex',
                    'flexDirection': 'column'
                })
            ], style={'width': '30%', 'display': 'inline-block', 'verticalAlign': 'top'})
        ], style={'width': '100%', 'display': 'flex', 'justifyContent': 'space-between'}),
        
        # Кнопка экспорта результатов
        html.Div([
            html.A(
                html.Button(
                    '📥 Экспорт результатов в CSV',
                    id='export-results-button',
                    n_clicks=0,
                    style={
                        'width': '25%',
                        'padding': '12px',
                        'borderRadius': '8px',
                        'border': 'none',
                        'backgroundColor': COLORS['success'],
                        'color': COLORS['text'],
                        'fontSize': '14px',
                        'fontWeight': '600',
                        'cursor': 'pointer',
                        'transition': 'all 0.3s ease',
                        'margin': '20px auto 0',
                        'display': 'block'
                    }
                ),
                id='download-link',
                href="",
                download="",
                style={'textDecoration': 'none'}
            ),
            html.Div(id='export-status', style={'marginTop': '10px'})
        ], style={'textAlign': 'center'})
    ])
    
    return results_content, export_data

# Callback для генерации и скачивания CSV файла
@app.callback(
    [Output('download-link', 'href'),
     Output('download-link', 'download'),
     Output('export-status', 'children')],
    [Input('export-results-button', 'n_clicks'),
     Input('calculation-data-store', 'data')],
    prevent_initial_call=True
)
def export_results(n_clicks, stored_data):
    if n_clicks is None or n_clicks == 0 or stored_data is None:
        return "", "", ""
    
    try:
        # Восстанавливаем DataFrame из сохраненных данных
        results_df = pd.DataFrame(stored_data['results'])
        params = stored_data['params']
        
        # Создаем CSV строку
        csv_string = results_df.to_csv(index=False, encoding='utf-8')
        
        # Создаем строку с метаданными
        meta_info = f"# Результаты расчета гидродинамических характеристик\n"
        meta_info += f"# Вещество: {params['substance']}\n"
        meta_info += f"# Диаметр: {params['d']} м\n"
        meta_info += f"# Массовый расход: {params['G']} кг/м²с\n"
        meta_info += f"# Температура: {params['T']} °C\n"
        meta_info += f"# Ускорение свободного падения: {params['g']} м/с²\n"
        meta_info += f"# Количество точек: {params['num_points']}\n"
        meta_info += f"# Диапазон паросодержания: {params['x_start']} - {params['x_end']}\n"
        if params.get('P'):
            meta_info += f"# Давление: {params['P']} Па\n"
        if params.get('ki'):
            meta_info += f"# Коэффициент ki: {params['ki']}\n"
        meta_info += f"# Дата расчета: {params['timestamp']}\n"
        meta_info += f"# \n"
        
        # Объединяем метаданные с данными
        full_csv = meta_info + csv_string
        
        # Кодируем в base64 для скачивания
        csv_base64 = base64.b64encode(full_csv.encode('utf-8')).decode()
        
        # Генерируем имя файла
        filename = generate_filename(params['substance'])
        
        # Создаем href для скачивания
        href = f"data:text/csv;base64,{csv_base64}"
        
        status_message = html.P(
            "✅ Файл готов к скачиванию. Нажмите на кнопку выше.",
            style={'color': COLORS['success'], 'textAlign': 'center'}
        )
        
        return href, filename, status_message
        
    except Exception as e:
        error_message = html.P(
            f"❌ Ошибка при экспорте: {str(e)}",
            style={'color': COLORS['error'], 'textAlign': 'center'}
        )
        return "", "", error_message

# Все остальные callback'ы остаются без изменений
# Callback для обновления параметров
@app.callback(
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
@app.callback(
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
@app.callback(
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
@app.callback(
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
                title_font=dict(size=14, color=COLORS['text']),
                tickfont=dict(size=12, color=COLORS['text_secondary']),
                showgrid=True,
                gridwidth=1,
                linewidth=1
            ),
            yaxis=dict(
                gridcolor=COLORS['grid_lines'],
                linecolor=COLORS['border'],
                zerolinecolor=COLORS['border'],
                title_font=dict(size=14, color=COLORS['text']),
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

# Добавляем CSS для стилизации выпадающих списков и вкладок
app.index_string = '''
<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>{%title%}</title>
        {%favicon%}
        {%css%}
        <style>
            /* Сброс отступов по умолчанию */
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }
            
            html, body {
                margin: 0;
                padding: 0;
                background-color: ''' + COLORS['background'] + ''' !important;
                color: ''' + COLORS['text'] + ''';
                font-family: "Segoe UI", "Inter", -apple-system, BlinkMacSystemFont, sans-serif;
                overflow-x: hidden;
                width: 100%;
                height: 100%;
            }
            
            #react-entry-point {
                margin: 0;
                padding: 0;
                background-color: ''' + COLORS['background'] + ''';
                min-height: 100vh;
            }
            
            /* Стили для выпадающих списков */
            .Select-control {
                background-color: ''' + COLORS['input_background'] + ''' !important;
                color: ''' + COLORS['text'] + ''' !important;
                border: ''' + COLORS['dropdown_border'] + ''' !important;
                border-radius: 8px !important;
                height: 42px !important;
                font-size: 14px !important;
                width: 100% !important;
            }
            
            .Select-value-label {
                color: ''' + COLORS['text'] + ''' !important;
                font-size: 14px !important;
                line-height: 42px !important;
                padding: 0 12px !important;
            }
            
            .Select-placeholder {
                color: ''' + COLORS['text_secondary'] + ''' !important;
                font-size: 14px !important;
                line-height: 42px !important;
                padding: 0 12px !important;
            }
            
            .Select-input {
                height: 42px !important;
            }
            
            .Select-input > input {
                color: ''' + COLORS['text'] + ''' !important;
                font-size: 14px !important;
                height: 42px !important;
                padding: 0 12px !important;
            }
            
            .Select-menu-outer {
                background-color: ''' + COLORS['dropdown_menu_bg'] + ''' !important;
                border: ''' + COLORS['dropdown_border'] + ''' !important;
                z-index: 1000 !important;
            }
            
            .Select-option {
                background-color: ''' + COLORS['dropdown_menu_bg'] + ''' !important;
                color: ''' + COLORS['text'] + ''' !important;
                font-size: 14px !important;
                padding: 12px !important;
            }
            
            .Select-option.is-focused {
                background-color: ''' + COLORS['dropdown_option_hover'] + ''' !important;
            }
            
            /* Стили для иконки стрелки */
            .Select-arrow-zone .Select-arrow {
                border-top-color: ''' + COLORS['text_secondary'] + ''' !important;
            }
            
            /* Стили для вкладок */
            .tab {
                background-color: ''' + COLORS['tab_background'] + ''' !important;
                color: ''' + COLORS['text_secondary'] + ''' !important;
                border: ''' + COLORS['tab_border'] + ''' !important;
                transition: all 0.3s ease;
            }
            
            .tab:hover {
                background-color: ''' + COLORS['tab_hover'] + ''' !important;
                color: ''' + COLORS['text'] + ''' !important;
            }
            
            .tab--selected {
                background-color: ''' + COLORS['card_background'] + ''' !important;
                color: ''' + COLORS['text'] + ''' !important;
                border-bottom: 3px solid ''' + COLORS['tab_selected'] + ''' !important;
                font-weight: 600;
            }
            
            /* Стили для кнопок при наведении */
            button:hover {
                opacity: 0.9;
                transform: translateY(-2px);
                box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
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
    run_dashboard(debug=False)  # Отключаем debug mode для устранения белого окна с ошибками