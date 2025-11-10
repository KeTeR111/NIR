import numpy as np
from scipy import optimize
import CoolProp.CoolProp as CP
import pandas as pd
import matplotlib.pyplot as plt

class DpDz():
    
    def __init__(self, g, d, ki, thermodinamic_params: dict, value_fb: bool):
        self.g = g  # Ускорение свободного падения
        self.d = d  # Диаметр канала 
        self.ki = ki  # Коэффициент для расчета по Уоллису
        self._s = None  # Кэш для площади сечения
        
        # Параметры вещества
        self.substance = thermodinamic_params['Substance']
        self.T = thermodinamic_params.get('Temperature', None)
        self.P = thermodinamic_params.get('Pressure', None)
        
        # Инициализация свойств
        self._init_properties(thermodinamic_params)
        
        self.G = thermodinamic_params.get('G', None)
        self.x = thermodinamic_params.get('x', None)
        self.SV_liquid = thermodinamic_params.get('Liquid velocity', None)
        self.SV_gas = thermodinamic_params.get('Gas velocity', None)
        
        self.check_values()
        self.flg_wb = value_fb

    @property
    def s(self):
        """Ленивое вычисление площади сечения"""
        if self._s is None:
            self._s = np.pi * (self.d / 2) ** 2
        return self._s

    def _init_properties(self, params):
        """Инициализация термодинамических свойств"""
        self.liquid_density = params.get('Liquid density', None)
        self.liquid_viscosity = params.get('Liquid viscosity', None)
        self.gas_density = params.get('Gas density', None)
        self.gas_viscosity = params.get('Gas viscosity', None)
        
        # Если свойства не предоставлены, вычисляем через CoolProp
        if self.T is not None and any(p is None for p in [self.liquid_density, self.gas_density]):
            self._calculate_properties_from_temperature()

        if self.liquid_density is not None and self.gas_density is not None:
            self.delta_density = self.liquid_density - self.gas_density

    def _calculate_properties_from_temperature(self):
        """Вычисление свойств через CoolProp на основе температуры"""
        T_kelvin = self.T + 273  # Конвертация в Кельвины
        
        try:
            if self.liquid_density is None:
                self.liquid_density = CP.PropsSI('D', 'T', T_kelvin, 'Q', 0, self.substance)
            if self.liquid_viscosity is None:
                self.liquid_viscosity = CP.PropsSI('V', 'T', T_kelvin, 'Q', 0, self.substance)
            if self.gas_density is None:
                self.gas_density = CP.PropsSI('D', 'T', T_kelvin, 'Q', 1, self.substance)
            if self.gas_viscosity is None:
                self.gas_viscosity = CP.PropsSI('V', 'T', T_kelvin, 'Q', 1, self.substance)
                
            self.delta_density = self.liquid_density - self.gas_density
            
        except Exception as e:
            raise ValueError(f"Ошибка вычисления свойств вещества: {e}")

    def Re_liquid(self, jl):   
        """Число Рейнольдса для жидкости"""
        return (self.liquid_density * jl * self.d) / self.liquid_viscosity
  
    def Ec(self, jl):
        """Коэффициент трения для жидкости"""
        Re_l = self.Re_liquid(jl)
        return 64 / Re_l if Re_l <= 2000 else 0.3164 * Re_l ** (-0.25)

    def check_values(self):
        """Проверка и вычисление недостающих параметров"""
        if self.SV_liquid is not None and self.SV_gas is not None:
            return  # Скорости уже заданы
            
        if self.G is None or self.x is None:
            raise ValueError("Недостаточно данных для расчета скоростей фаз: "
                           f"G is None: {self.G is None}, X is None: {self.x is None}")

        # Вычисляем скорости фаз
        self.SV_liquid, self.SV_gas = self.phase_velocity_G_x()

    def phase_velocity_G_x(self):
        """
        Расчет расходных скоростей фаз из массовой скорости
        с поддержкой векторных вычислений
        """
        G_array = np.asarray(self.G)
        x_array = np.asarray(self.x)
        
        # Обеспечиваем правильную размерность массивов
        if G_array.ndim == 0:  # Скаляр
            G_array = np.array([G_array])
        
        if x_array.ndim == 0:  # Скаляр
            x_array = np.array([x_array])
        
        # Векторизованные вычисления с правильной размерностью
        if G_array.ndim == 1 and x_array.ndim == 1:
            # Если оба одномерные, создаем сетку
            SV_liquid = G_array[:, np.newaxis] * (1 - x_array) / self.liquid_density
            SV_gas = G_array[:, np.newaxis] * x_array / self.gas_density
        else:
            # Для других случаев используем прямое умножение
            SV_liquid = G_array * (1 - x_array) / self.liquid_density
            SV_gas = G_array * x_array / self.gas_density

        return SV_liquid, SV_gas

    # Вспомогательные свойства
    def Di(self, B):      
        """Диаметр межфазной поверхности"""
        return self.d - 2 * B

    def Fi(self, B):      
        """Истинное объемное паросодержание"""
        return ((self.d - 2 * B) / self.d) ** 2

    def RE0_gas(self, B, SV_gas):    
        """Число Рейнольдса для газообразной фазы"""
        return (self.gas_density * SV_gas / self.Fi(B) * self.Di(B)) / self.gas_viscosity

    def E0(self, B, SV_gas):
        """Коэффициент трения для газа"""
        return 0.3164 * self.RE0_gas(B, SV_gas) ** (-0.25)

    def Ei(self, B, SV_gas):
        """Коэффициент межфазного трения Уоллиса"""
        return self.E0(B, SV_gas) * (1 + (self.ki * B) / self.d)

    def Tc(self, B, jl):
        """Касательное напряжение"""
        return self.Ec(jl) * self.liquid_density * jl ** 2 / (8 * (1 - self.Fi(B)) ** 2)

    def wb(self, B, SV_liquid): 
        """Скорость на границе раздела фаз"""
        T_c = self.Tc(B, SV_liquid)
        form = (T_c / self.liquid_density) ** 0.5
        # Добавляем проверку для избежания log(0)
        log_arg = max(B * form / self.liquid_viscosity, 1e-10)
        return (2.5 * np.log(log_arg) + 5.5) * form

    def Ti(self, B, SV_gas, SV_liquid): 
        """Межфазное касательное напряжение"""
        E_i = self.Ei(B, SV_gas)
        w_b = self.wb(B, SV_liquid) if self.flg_wb else 0
        return E_i * self.gas_density * (SV_gas / self.Fi(B) - w_b) ** 2 / 8

    def calcDPDZ(self, B, SV_gas, SV_liquid):
        """Градиент давления"""
        T_i = self.Ti(B, SV_gas, SV_liquid)
        return 4.0 * T_i / self.Di(B) + self.gas_density * self.g

    def equation(self, B, SV_gas, SV_liquid):    
        """Уравнение для поиска толщины пленки"""
        return (self.Tc(B, SV_liquid) - 
                self.Ti(B, SV_gas, SV_liquid) - 
                self.delta_density * self.g * B)

    def calcOnePoint(self, args):
        """Поиск толщины пленки для одной точки"""
        try:
            sol = optimize.root_scalar(
                self.equation,
                args=args,
                bracket=[1.0e-13, self.d / 2 - 1.0e-13],
                method='brentq'
            )
            return sol.root
        except ValueError as e:
            # Если решение не найдено, возвращаем среднее значение
            print(f"Warning: root finding failed for args {args}, using fallback value. Error: {e}")
            return self.d / 4

    def calculate_one_point(self, jg, jl):
        """Расчет всех параметров в одной точке"""
        B = self.calcOnePoint((jg, jl))
        dpdz = self.calcDPDZ(B, jg, jl)
        
        # Дополнительные параметры для анализа
        ReL = self.Re_liquid(jl)
        ReG = self.RE0_gas(B, jg)
        
        return [jg, jl, B, dpdz, self.substance, ReL, ReG]

    def calculate(self):
        """Основной метод расчета для всех точек"""
        # Проверяем размерности массивов
        SV_gas_flat = np.asarray(self.SV_gas).flatten()
        SV_liquid_flat = np.asarray(self.SV_liquid).flatten()
        
        results = []
        for jg in SV_gas_flat:
            for jl in SV_liquid_flat:
                results.append(self.calculate_one_point(jg, jl))
        
        return results

# Тестирование
params_t = {
    'Substance': 'CO2',
    'Temperature': 0,
    'G': 300,
    'x': np.linspace(0.1, 0.9, 9),
}

result = DpDz(g=9.8155, ki=350, d=0.005, value_fb=False, thermodinamic_params=params_t)

df = pd.DataFrame(result.calculate(), 
                  columns=['Gas_velocity', 'Liquid_velocity', 'Film_thickness', 
                           'Pressure_gradient', 'Substance', 'ReL', 'ReG'])
plt.plot(params_t['x'], df['Pressure_gradient'])
plt.show()