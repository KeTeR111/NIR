import numpy as np 
import sys
import os
import glob
from scipy import optimize
import CoolProp.CoolProp as CP
import pandas as pd
import matplotlib.pyplot as plt
from scipy import interpolate

class DpDz():

    def __init__(self, g, d, ki, thermodinamic_params: dict, value_fb: bool):

        self.g = g   # Ускорение свободного падения
        self.d = d  # Диаметр канала 
        self.ki = ki    # Коэффициент для расчета по Уоллису меняется в зависимости от условия 
        self.s = np.pi * (self.d / 2) ** 2 # Площадь сечения трубы
        
        self.substance = thermodinamic_params['Substance'] 
        self.T = thermodinamic_params.get('Temperature', None)
        self.P = thermodinamic_params.get('Pressure', None) 
        self.liquid_density = thermodinamic_params['Liquid density']
        self.liquid_viscosity = thermodinamic_params['Liquid viscosity']
        self.gas_density = thermodinamic_params['Gas density']
        self.gas_viscosity = thermodinamic_params['Gas viscosity']
        self.delta_density = self.liquid_density - self.gas_density
        self.G = thermodinamic_params.get('G', None)
        self.x = thermodinamic_params.get('x', None)
        self.SV_liquid = thermodinamic_params.get('Liquid velocity', None)
        self.SV_gas = thermodinamic_params.get('Gas velocity', None)
        
        self.check_values()
        self.flg_wb = value_fb

    
    def Re_liquid(self, SV_liquid):   
        return (self.liquid_density * SV_liquid * self.d) / self.liquid_viscosity  
    
  
    def Ec(self, SV_liquid):
        if self.Re_liquid(SV_liquid) <= 2000:
            ec = 64 / self.Re_liquid(SV_liquid)
        else:
            ec =  0.3164 * (self.Re_liquid(SV_liquid)) ** (-0.25)
        return ec 
        

    def check_values(self):
        if self.SV_liquid is None or self.SV_gas is None:
            if self.G is not None and self.x is not None:
                self.SV_liquid, self.SV_gas = self.phase_velocity()
            else:
                print(f"G is None: {self.G is None}, X is None: {self.x is None}")
                raise ValueError("Недостаточно данных для расчета скоростей фаз")

    def phase_velocity(self):
        """
        Расчет расходных скоростей фаз из массовой скорости
        с поддержкой векторных вычислений для меняющегося паросодержания
        
        Parameters:
        G - массовая скорость [kg/m²s] (скаляр или массив)
        x - паросодержание [0-1] (скаляр или массив)
        fluid - рабочее вещество
        P - давление [Pa] (обязательно если не задана T)
        T - температура [K] (обязательно если не задана P)
        """

        # Преобразуем входные данные в массивы numpy для векторных операций
        G_array = np.array(self.G)
        x_array = np.array(self.x)

        #  # Проверка совместимости размеров
        # if G_array.ndim > 0 and x_array.ndim > 0 and G_array.shape != x_array.shape:
        #     # Если оба массива и размеры не совпадают, пытаемся сделать бродкастинг
        #     try:
        #         # Проверяем возможность бродкастинга
        #         np.broadcast_arrays(G_array, x_array)
        #     except ValueError:
        #         raise ValueError("Размеры массивов G и x должны быть совместимы для бродкастинга")

        # Расчет расходных скоростей (векторные операции)
        SV_liquid = np.outer(G_array, 1 - x_array) / self.liquid_density
        # SV_liquid = G_array * (1 - x_array) / self.liquid_density  # Скорость жидкости [m/s]
        SV_gas = np.outer(G_array, x_array) / self.gas_density        # Скорость пара [m/s]
        
        return SV_liquid, SV_gas


    # Диаметр межфазной поверхности 
    def Di(self, B):      
        return  self.d - 2 * B  

    # Истинное объемное паросодержание                                             
    def Fi(self, B):      
        return ((self.d - 2 * B) / self.d) ** 2                                          
        
    # Число Рейнольдса  для газообразной фазы
    def RE0_gas(self, B, SV_gas):    
        return (self.gas_density * SV_gas / self.Fi(B) * self.Di(B)) / self.gas_viscosity 

    def E0(self, B, SV_gas):
        return (0.3164 * (self.RE0_gas(B, SV_gas)) ** (-0.25))

    # Коэффициент межфазного трения Уоллиса 
    def Ei(self, B, SV_gas):
        return  self.E0(B, SV_gas) * (1 + (self.ki * B) / self.d)

    def Tc (self, B, SV_liquid):
        return self.Ec(SV_liquid) * self.liquid_density * (SV_liquid) ** 2 / (8 * (1 - self.Fi(B)) ** 2)

    def wb(self, B, SV_liquid): 
        T_c = self.Tc(B, SV_liquid)
        form = (T_c / self.liquid_density) ** 0.5
        return  (2.5 * np.log((B * form / self.liquid_viscosity)) + 5.5) * form

    def Ti(self, B, SV_gas, SV_liquid): 
        E_i = self.Ei(B, SV_gas)
        if self.flg_wb:
            w_b = self.wb(B, SV_liquid)
        else:
            w_b = 0
        return  E_i * self.gas_density * (SV_gas / self.Fi(B) - w_b) ** 2 /  8 

    # Функция для расчета градиента давления 
    def calcDPDZ(self, B, SV_gas, SV_liquid):
        T_i = self.Ti(B, SV_gas, SV_liquid)
        return 4.0 * T_i / self.Di(B) + self.gas_density * self.g
    
    # Функция по которой считается толщина пленки 
    def equation(self, B, SV_gas, SV_liquid):    
        LHS = self.Tc(B, SV_liquid)
        RHS = self.Ti(B, SV_gas, SV_liquid) + self.delta_density * self.g * B  
        return LHS - RHS
        

    # Функция для расчета толщины пленки 
    def calcOnePoint(self, args):
        sol = optimize.root_scalar(self.equation,
                                args=args,   
                                bracket=[1.0e-13, self.d / 2-1.0e-13], 
                                method='brentq')
        return sol.root
        

    def __calculate_one_point(self, jg, jl):
        params = (jg, jl)
        # Расчет толщины пленки
        B = self.calcOnePoint(params) 
        # Расчет градиента давления
        dpdz = self.calcDPDZ(B, jg, jl)  
        ReG = self.RE0_gas(B, jg)
        if self.flg_wb:
            w_b = self.wb(B, jl)
        else:
            w_b = 0
        Res = [jg, jl, B, dpdz, self.substance, self.Re_liquid(jl), ReG]
        
        return Res
    

    def full_research(self):
        

param1 = {

    'Substance': 'Nitrogen-95Ethanol',
    'Liquid density': 850,
    'Liquid viscosity': 1420 * 10**(-6), 
    'Gas density': 2.3, 
    'Gas viscosity': 7.7 * 10**(-6),
    'x': np.array([0.5, 0.8, 0.9, 1]),
    'G': np.array([300, 400])

    }

param2 = {

    'Substance': 'Nitrogen-95Ethanol',
    'Liquid density': 850,
    'Liquid viscosity': 1420 * 10**(-6), 
    'Gas density': 2.3, 
    'Gas viscosity': 7.7 * 10**(-6),
    'Liquid velocity': np.array([0.1, 0.5, 0.8]),
    'Gas velocity': np.array([i for i in range(5, 26, 5)])

    }

# first = DpDz(g=9.8155, ki=300, d=0.005, value_fb=False, thermodinamic_params=param1)
second = DpDz(g=9.8155, ki=300, d=0.005, value_fb=False, thermodinamic_params=param1)

# df = pd.DataFrame(second.calculate(), columns=['Gas velocity', 'Liquid velocity', 'b', 'dp/dz', 'Substance', 'Re Liquid', 'Re Gas'])
      
# print(f'Скорость газа: \n {second.SV_gas} \n Скорость жидкости: \n {second.SV_liquid}')
# print(np.stack([second.SV_liquid, second.SV_gas], axis=1))

print(second.calculate(60, 0.7))