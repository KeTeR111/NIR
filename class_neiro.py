import numpy as np 
from pathlib import Path
from scipy import optimize
import CoolProp.CoolProp as CP
import pandas as pd
import matplotlib.pyplot as plt

class DpDz():

    def __init__(self, g, d, ki, thermodinamic_params: dict, value_fb: bool):
        self.g = g   # Ускорение свободного падения [m/s²]
        self.d = d  # Диаметр канала [m]
        self.ki = ki    # Коэффициент для расчета по Уоллису
        
        # Площадь сечения трубы [m²]
        self.s = np.pi * (self.d / 2) ** 2 
        
        self.substance = thermodinamic_params['Substance'] 
        self.T = thermodinamic_params.get('Temperature', None)
        self.P = thermodinamic_params.get('Pressure', None) 
        
        # Инициализация свойств
        self.liquid_density = None
        self.liquid_viscosity = None  # Динамическая вязкость [Pa·s]
        self.gas_density = None
        self.gas_viscosity = None     # Динамическая вязкость [Pa·s]
        
        self.G = thermodinamic_params.get('G', None)
        self.x = thermodinamic_params.get('x', None)
        self.SV_liquid = thermodinamic_params.get('Liquid velocity', None)
        self.SV_gas = thermodinamic_params.get('Gas velocity', None)
        
        self.check_values()
        self.flg_wb = value_fb

    def check_values(self):
        if self.SV_liquid is None or self.SV_gas is None:
            if self.G is not None and self.x is not None:
                if self.T is not None:
                    # ВАЖНО: CoolProp работает в K, а не °C
                    T_kelvin = self.T + 273.15  # Преобразование в Кельвины
                    
                    try:
                        # Плотность жидкости [kg/m³]
                        self.liquid_density = CP.PropsSI('D', 'T', T_kelvin, 'Q', 0, self.substance)
                        
                        # Динамическая вязкость жидкости [Pa·s]
                        mu_liq = CP.PropsSI('VISCOSITY', 'T', T_kelvin, 'Q', 0, self.substance)
                        self.liquid_viscosity = mu_liq  # Оставляем как динамическую вязкость
                        
                        # Плотность пара [kg/m³]
                        self.gas_density = CP.PropsSI('D', 'T', T_kelvin, 'Q', 1, self.substance)
                        
                        # Динамическая вязкость пара [Pa·s]  
                        mu_gas = CP.PropsSI('VISCOSITY', 'T', T_kelvin, 'Q', 1, self.substance)
                        self.gas_viscosity = mu_gas  # Оставляем как динамическую вязкость
                        
                        self.delta_density = self.liquid_density - self.gas_density
                        
                        print(f"T = {self.T}°C: ρ_l = {self.liquid_density:.1f}, ρ_g = {self.gas_density:.1f}, μ_l = {self.liquid_viscosity:.2e}, μ_g = {self.gas_viscosity:.2e}")
                        
                        self.SV_liquid, self.SV_gas = self.phase_velocity_G_x()
                        
                    except Exception as e:
                        print(f"Ошибка получения свойств CO2 при T={self.T}°C: {e}")
                        # Резервные значения для CO2
                        self.set_default_co2_properties()
                else:
                    raise ValueError("Температура не задана")
            else:
                raise ValueError("Недостаточно данных для расчета скоростей фаз")

    def phase_velocity_G_x(self):
        """Расчет расходных скоростей фаз"""
        G_array = np.array(self.G)
        x_array = np.array(self.x)

        if G_array.ndim == 0:
            G_array = np.array([G_array])
        if x_array.ndim == 0:
            x_array = np.array([x_array])

        SV_liquid = []
        SV_gas = []
        
        for G_val in G_array:
            # Массовый расход жидкости и газа [kg/m²s]
            G_liquid = G_val * (1 - x_array)
            G_gas = G_val * x_array
            
            # Объемные скорости [m/s]
            jl = G_liquid / self.liquid_density
            jg = G_gas / self.gas_density
            
            SV_liquid.append(jl)
            SV_gas.append(jg)

        SV_gas = np.array(SV_gas)
        SV_liquid = np.array(SV_liquid)
        
        return SV_liquid, SV_gas

    def Re_liquid(self, jl):   
        """Число Рейнольдса для жидкости"""
        return (self.liquid_density * jl * self.d) / self.liquid_viscosity  

    def Ec(self, jl):
        """Коэффициент трения для жидкости"""
        Re_l = self.Re_liquid(jl)
        if Re_l <= 2000:
            return 64 / Re_l  # Ламинарный режим
        else:
            return 0.3164 * (Re_l) ** (-0.25)  # Турбулентный режим (Блазиус)
        
    def Di(self, B):      
        """Диаметр межфазной поверхности"""
        return self.d - 2 * B  

    def Fi(self, B):      
        """Истинное объемное паросодержание"""
        return ((self.d - 2 * B) / self.d) ** 2                                          
        
    def RE0_gas(self, B, SV_gas):    
        """Число Рейнольдса для газа"""
        return (self.gas_density * SV_gas * self.Di(B)) / (self.gas_viscosity * self.Fi(B))

    def E0(self, B, SV_gas):
        """Коэффициент трения для газа"""
        Re_g = self.RE0_gas(B, SV_gas)
        if Re_g <= 2000:
            return 64 / Re_g
        else:
            return 0.3164 * (Re_g) ** (-0.25)

    def Ei(self, B, SV_gas):
        """Коэффициент межфазного трения Уоллиса"""
        return self.E0(B, SV_gas) * (1 + (self.ki * B) / self.d)

    def Tc(self, B, jl):
        """Касательное напряжение на стенке"""
        return (self.Ec(jl) * self.liquid_density * jl**2) / 8

    def wb(self, B, SV_liquid): 
        """Скорость на границе раздела фаз"""
        T_c = self.Tc(B, SV_liquid)
        u_tau = np.sqrt(T_c / self.liquid_density)  # Динамическая скорость
        Re_tau = (B * u_tau * self.liquid_density) / self.liquid_viscosity
        
        if Re_tau > 30:  # Турбулентный пограничный слой
            return u_tau * (2.5 * np.log(Re_tau) + 5.5)
        else:  # Ламинарный пограничный слой
            return (T_c * B) / self.liquid_viscosity

    def Ti(self, B, SV_gas, SV_liquid): 
        """Межфазное касательное напряжение"""
        E_i = self.Ei(B, SV_gas)
        if self.flg_wb:
            w_b = self.wb(B, SV_liquid)
        else:
            w_b = 0
            
        relative_velocity = max(0.1, abs(SV_gas / self.Fi(B) - w_b))  # Избегаем деления на 0
        return E_i * self.gas_density * relative_velocity**2 / 8

    def calcDPDZ(self, B, SV_gas, SV_liquid):
        """Градиент давления [Pa/m]"""
        T_i = self.Ti(B, SV_gas, SV_liquid)
        friction_term = 4.0 * T_i / self.Di(B)
        gravity_term = self.liquid_density * self.g * (1 - self.Fi(B)) + self.gas_density * self.g * self.Fi(B)
        
        return friction_term + gravity_term  # [Pa/m]

    def equation(self, B, SV_gas, SV_liquid):    
        """Уравнение для нахождения толщины пленки"""
        LHS = self.Tc(B, SV_liquid)
        RHS = self.Ti(B, SV_gas, SV_liquid) + self.delta_density * self.g * B  
        return LHS - RHS
        

    def calcOnePoint(self, args):
        """Решение для одной точки"""
        SV_gas, SV_liquid = args
        try:
            sol = optimize.root_scalar(self.equation,
                                    args=(SV_gas, SV_liquid),   
                                    bracket=[1.0e-6, self.d / 2 - 1.0e-6], 
                                    method='brentq')
            return sol.root
        except:
            # Возвращаем среднее значение при ошибке
            return self.d / 4
        
    def calculate_one_point(self, jg, jl):
        """Расчет всех параметров в одной точке"""
        params = (jg, jl)
        B = self.calcOnePoint(params) 
        dpdz = self.calcDPDZ(B, jg, jl) 
        ReL = self.Re_liquid(jl)
        ReG = self.RE0_gas(B, jg)

        if self.flg_wb:
            w_b = self.wb(B, jl)
        else:
            w_b = 0
        
        return {
            'jg': jg,
            'jl': jl,
            'B': B,
            'DpDz': dpdz,  # [Pa/m]
            'DpDz_kPa_m': dpdz / 1000,  # [kPa/m]
            'Substance': self.substance,
            'Re liquid': ReL,
            'Re gas': ReG,
            'Void fraction': self.Fi(B)
        }
    
    def calculate(self):
        """Основная функция расчета"""
        ndim_gas = self.SV_gas.ndim
        ndim_liquid = self.SV_liquid.ndim
        Res = []

        if ndim_gas > 1 or ndim_liquid > 1:
            for arr1, arr2 in zip(self.SV_gas, self.SV_liquid):
                res = []
                for jg, jl in zip(arr1, arr2):
                    res.append(self.calculate_one_point(jg, jl))
                Res.append(res)
        else:
            for jg, jl in zip(self.SV_gas.flatten(), self.SV_liquid.flatten()):
                Res.append(self.calculate_one_point(jg, jl))

        if len(Res) == 1:
            Res = Res[0]

        return Res


if __name__ == "__main__":  
    T = np.array([0, -10, -20, -30, -35, -40])
    
    plt.figure(figsize=(10, 6))
    
    for t in T:
        params_t = {
            'Substance': 'CO2',
            'Temperature': t,
            'G': np.array([300]),
            'x': np.linspace(0.1, 0.9, 9),
        }
        
        try:
            result = DpDz(g=9.81, ki=350, d=0.005, value_fb=False, thermodinamic_params=params_t)
            results = result.calculate()
            df = pd.DataFrame(results)
            
            plt.plot(params_t['x'], df['DpDz'], 'o-', label=f'T = {t}°C')
            print(f"T = {t}°C: min DpDz = {df['DpDz'].min():.1f} kPa/m, max DpDz = {df['DpDz'].max():.1f} Pa/m")
            
        except Exception as e:
            print(f"Ошибка при T={t}°C: {e}")
    
    plt.xlabel('Паросодержание, x')
    plt.ylabel('Градиент давления, kPa/m')
    plt.title('Градиент давления CO2 в двухфазном потоке')
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.show()