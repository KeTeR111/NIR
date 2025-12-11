import numpy as np
from scipy import optimize
import CoolProp.CoolProp as CP
import pandas as pd
import matplotlib.pyplot as plt
from typing import Optional, Union, Tuple, List, Dict

def check_and_calculate_phase_velocities(G, x, substance, T=None, P=None):
    """
    Проверка и расчет расходных скоростей фаз
    """
    # Получаем свойства из CoolProp
    liquid_density = CP.PropsSI('D', 'T', T + 273, 'Q', 0, substance)
    liquid_viscosity = CP.PropsSI('VISCOSITY', 'T', T + 273, 'Q', 0, substance)
    
    gas_density = CP.PropsSI('D', 'T', T + 273, 'Q', 1, substance)
    gas_viscosity = CP.PropsSI('VISCOSITY', 'T', T + 273, 'Q', 1, substance)
            
   # Преобразуем входные данные в массивы numpy
    G_array = np.atleast_1d(G)
    x_array = np.atleast_1d(x)

    # Создаем сетку для комбинаций G и x
    # Для каждого G используем все x (как в оригинальном коде)
    G_grid, x_grid = np.meshgrid(G_array, x_array, indexing='ij')

    # Расчет скоростей фаз
    SV_liquid = G_grid * (1 - x_grid) / liquid_density
    SV_gas = G_grid * x_grid / gas_density

    delta_density = liquid_density - gas_density
    
    return SV_liquid, SV_gas, liquid_density, liquid_viscosity, gas_density, gas_viscosity, delta_density

def Re_liquid(jl, d, liquid_density, liquid_viscosity):
    """Число Рейнольдса для жидкости"""
    return (liquid_density * jl * d) / liquid_viscosity

def Ec(jl, d, liquid_density, liquid_viscosity):
    """Коэффициент трения для жидкости"""
    Re = Re_liquid(jl, d, liquid_density, liquid_viscosity)
    if Re <= 2000:
        ec = 64 / Re
    else:
        ec = (1.82 * np.log10(Re) - 1.64) ** (-2)
    return ec

def Fi(B, d):
    """Коэффициент Fi"""
    return ((d - 2 * B) / d) ** 2

def Di(B, d):
    """Внутренний диаметр пленки"""
    return d - 2 * B

def RE0_gas(B, SV_gas, d, gas_density, gas_viscosity):
    """Число Рейнольдса для газа"""
    return (gas_density * SV_gas / Fi(B, d) * Di(B, d)) / gas_viscosity

def E0(B, SV_gas, d, gas_density, gas_viscosity):
    """Коэффициент трения для газа по формуле Филонко"""
    Re_gas = RE0_gas(B, SV_gas, d, gas_density, gas_viscosity)
    return (1.82 * np.log10(Re_gas) - 1.64) ** (-2)

def Ei(B, SV_gas, d, gas_density, gas_viscosity, liquid_density, ki=None):
    """Коэффициент трения для газа с учетом влияния жидкости"""
    e0 = E0(B, SV_gas, d, gas_density, gas_viscosity)
    if ki is None:
        return e0 * (1 + (24 * (liquid_density / gas_density) ** (1 / 3) * B) / d)
    else:
        return e0 * (1 + (ki * B) / d)

def Tc(B, jl, d, liquid_density, liquid_viscosity):
    """Касательное напряжение в пленке жидкости"""
    ec = Ec(jl, d, liquid_density, liquid_viscosity)
    return ec * liquid_density * jl ** 2 / (8 * (1 - Fi(B, d)) ** 2)

def wb(B, jl, d, liquid_density, liquid_viscosity, flg_wb):
    """Скорость на границе раздела фаз"""
    if not flg_wb:
        return 0
    
    T_c = Tc(B, jl, d, liquid_density, liquid_viscosity)
    form = (T_c / liquid_density) ** 0.5
    # return (2.5 * np.log((B * form / liquid_viscosity)) + 5.5) * form
    return 0

def Ti(B, SV_gas, jl, d, gas_density, liquid_density, liquid_viscosity, gas_viscosity, ki=None, flg_wb=False):
    """Касательное напряжение на границе раздела фаз"""
    e_i = Ei(B, SV_gas, d, gas_density, gas_viscosity, liquid_density, ki)
    w_b = wb(B, jl, d, liquid_density, liquid_viscosity, flg_wb)
    return e_i * gas_density * (SV_gas / Fi(B, d) - w_b) ** 2 / 8

def calcDPDZ(B, SV_gas, jl, d, g, gas_density, liquid_density, liquid_viscosity, gas_viscosity, ki=None, flg_wb=False):
    """Расчет градиента давления"""
    T_i = Ti(B, SV_gas, jl, d, gas_density, liquid_density, liquid_viscosity, gas_viscosity, ki, flg_wb)
    return 4.0 * T_i / Di(B, d) + gas_density * g

def equation(B, jg, jl, d, g, delta_density, gas_density, liquid_density, liquid_viscosity, gas_viscosity, ki=None, flg_wb=False):
    """Уравнение для нахождения толщины пленки B"""
    LHS = Tc(B, jl, d, liquid_density, liquid_viscosity)
    RHS = Ti(B, jg, jl, d, gas_density, liquid_density, liquid_viscosity, gas_viscosity, ki, flg_wb) + delta_density * g * B
    return LHS - RHS

def calc_one_point_params(SV_gas, jl, d, g, delta_density, gas_density, liquid_density, liquid_viscosity, gas_viscosity, ki=None, flg_wb=False):
    """Решение уравнения для одной точки"""
    sol = optimize.root_scalar(
        equation,
        args=(SV_gas, jl, d, g, delta_density, gas_density, liquid_density, liquid_viscosity, gas_viscosity, ki, flg_wb),
        bracket=[1.0e-5, d / 2 - 1.0e-5],
        method='brentq'
    )
    return sol.root

def calculate_one_point(jg, jl, x, substance, d, g, 
                       gas_density, liquid_density, liquid_viscosity, gas_viscosity, delta_density,
                       ki=None, flg_wb=False):
    """Расчет всех параметров для одной точки"""
    try:
        # Находим толщину пленки
        B = calc_one_point_params(jg, jl, d, g, delta_density, gas_density, 
                                 liquid_density, liquid_viscosity, gas_viscosity, ki, flg_wb)
        
        # Рассчитываем градиент давления
        dpdz = calcDPDZ(B, jg, jl, d, g, gas_density, liquid_density, 
                       liquid_viscosity, gas_viscosity, ki, flg_wb)
        
        # Расчет чисел Рейнольдса
        ReL = Re_liquid(jl, d, liquid_density, liquid_viscosity)
        ReG = RE0_gas(B, jg, d, gas_density, gas_viscosity)
        
        # Скорость на границе раздела
        w_b = wb(B, jl, d, liquid_density, liquid_viscosity, flg_wb)
        
        # Формируем результат
        result = {
            'jg': jg,
            'jl': jl,
            'B': B,
            'DpDz': dpdz,
            'Substance': substance,
            'Re liquid': ReL,
            'Re gas': ReG,
            'x': x,
            'wb': w_b
        }
        
        return result
    
    except Exception as e:
        print(f"Ошибка в calculate_one_point: {e}")
        return None

def calculate_dpdz(G=None, x=None, 
                  substance=None, T=None, P=None,
                  d=0.01, g=9.81, ki=None, flg_wb=False):

        
    # Проверка и расчет скоростей фаз
    results = check_and_calculate_phase_velocities(
        G, x, substance, T, P, 
    )
    
    SV_liquid, SV_gas, liquid_density, liquid_viscosity, gas_density, gas_viscosity, delta_density = results
    
    Res = calculate_one_point(SV_gas, SV_liquid, x, substance, d, g, 
                       gas_density, liquid_density, liquid_viscosity, gas_viscosity, delta_density,
                       ki=None, flg_wb=False)
    
    return Res

# Пример использования
if __name__ == "__main__":
    # Пример 1: Расчет с использованием CoolProp
    results = calculate_dpdz(
        G=300,  # кг/(м²·с)
        x=0.1,  # паросодержание
        substance='CO2',
        T=-10,  # °C
        d=0.00142,  # м
        g=0,  # м/с²
        ki=None,
        flg_wb=False
    )
    print(results)
    
  