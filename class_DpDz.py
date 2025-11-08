import numpy as np 
import sys
import os
import glob
from pathlib import Path
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

    
    def Re_liquid(self, jl):   
        return (self.liquid_density * jl * self.d) / self.liquid_viscosity  
    
  
    def Ec(self, jl):
        if self.Re_liquid(jl) <= 2000:
            ec = 64 / self.Re_liquid(jl)
        else:
            ec =  0.3164 * (self.Re_liquid(jl)) ** (-0.25)
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

        # Расчет расходных скоростей (векторные операции)
        SV_liquid = np.outer(G_array, 1 - x_array) / self.liquid_density # Скорость жидкости [m/s]
        SV_gas = np.outer(G_array, x_array) / self.gas_density        # Скорость пара [m/s]

        SV_liquid = []
        SV_gas = []
        for G in G_array:
            liq = G * (1 - x_array) / self.liquid_density 
            gas = G * x_array / self.gas_density 
            SV_liquid.append(liq)
            SV_gas.append(gas)

        SV_gas = np.array(SV_gas)
        SV_liquid = np.array(SV_liquid)

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

    def Tc (self, B, jl):
        return self.Ec(jl) * self.liquid_density * (jl) ** 2 / (8 * (1 - self.Fi(B)) ** 2)

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
        

    def calculate_one_point(self, jg, jl):
        params = (jg, jl)
        # Расчет толщины пленки
        B = self.calcOnePoint(params) 
        
        # Расчет градиента давления
        dpdz = self.calcDPDZ(B, jg, jl) 
        ReL = self.Re_liquid(jl)
        ReG = self.RE0_gas(B, jg)

        
        if self.flg_wb:
            w_b = self.wb(B, jl)
        else:
            w_b = 0
        
        Res = [jg, jl, B, dpdz, self.substance, ReL, ReG]
        
        return Res
    
    def calculate(self):
        ndim_gas = self.SV_gas.ndim
        ndim_liquid = self.SV_liquid.ndim
        Res = []
        if ndim_gas > 1 or ndim_liquid > 1:
            
            for arr1, arr2 in zip(self.SV_gas, self.SV_liquid):
                res = []
                for jg, jl in zip(arr1, arr2):
                    res.append(self.calculate_one_point(jg, jl))
                Res.append(res)
            return(Res)

        else:
            for jl in self.SV_liquid:
                for jg in self.SV_gas:
                    Res.append(self.calculate_one_point(jg, jl))
            return Res
        
    
param1 = {

    'Substance': 'CO2',
    'Liquid density': 1125,
    'Liquid viscosity': 0.00012, 
    'Gas density': 22.5, 
    'Gas viscosity': 0.000013,
    'x': np.linspace(0.1, 0.9, 9),
    'G': np.array([300, 400, 500, 600])

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

first = DpDz(g=9.8155, ki=350, d=0.005, value_fb=False, thermodinamic_params=param1)
second = DpDz(g=9.8155, ki=300, d=0.005, value_fb=False, thermodinamic_params=param2)


data = []
for i in first.calculate():
    df = pd.DataFrame(i,columns=['jg', 'jl', 'B', 'dpdz', 'substance', 'Re liquid', 'Re gas'])
    df = df.sort_values(['jg'], ignore_index=True)
    print(df)
    data.append(df)
    

path = Path("/Users/andrey/Desktop/NIR/Datasets/Graph9")
fl = []

for file_path in path.rglob('*'):
    if file_path.is_file():
        try:
            fl.append(pd.read_csv(file_path, sep='\t', decimal='.'))
        except Exception as e:
            print(f"Ошибка: {e}")

    

fig, ax = plt.subplots(nrows=4, ncols=1, figsize=(8, 16))

for i in range(len(data)):
    ax[i].plot(param1['x'], data[i]['dpdz'])
    ax[i].plot(param1['x'], 0.7 * data[i]['dpdz'], color='red', linestyle='--')
    ax[i].plot(param1['x'], 1.3 * data[i]['dpdz'], color='red', linestyle='--')
    ax[i].plot(fl[i]['X'], fl[i]['Y'] * 1000, marker='o', linestyle='')
    ax[i].set_title(f'G = {param1["G"][i]}' )
    

plt.show()
