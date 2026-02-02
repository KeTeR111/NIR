import numpy as np
from scipy import optimize
import CoolProp.CoolProp as CP

class DpDz():

    def __init__(self, g, d, ki, thermodynamic_params: dict, value_fb: bool):

        self.g = g   # Ускорение свободного падения
        self.d = d  # Диаметр канала
        self.ki: int | None = ki # Коэффициент для расчета по Уоллису меняется в зависимости от условия 
        self.s = np.pi * (self.d / 2) ** 2 # Площадь сечения трубы
        self.substance = thermodynamic_params['Substance']
        self.T = thermodynamic_params.get('Temperature', None)
        self.P = thermodynamic_params.get('Pressure', None)
        self.liquid_density = thermodynamic_params.get('Liquid density', None)
        self.liquid_viscosity = thermodynamic_params.get('Liquid viscosity', None)
        self.gas_density = thermodynamic_params.get('Gas density', None)
        self.gas_viscosity = thermodynamic_params.get('Gas viscosity', None)

        self.G = thermodynamic_params.get('G', None)
        self.x = thermodynamic_params.get('x', None)
        self.SV_liquid = thermodynamic_params.get('Liquid velocity', None)
        self.SV_gas = thermodynamic_params.get('Gas velocity', None)

        if (self.liquid_density is not None) and (self.gas_density is not None):
            self.delta_density = self.liquid_density - self.gas_density
            self.simplex_density = self.gas_density / self.liquid_density
            self.simplex_viscosity = self.gas_viscosity / self.liquid_viscosity
        
        self.check_values()
        self.flg_wb = value_fb

    def check_values(self):
        if self.SV_liquid is None or self.SV_gas is None:
            if self.G is not None and self.x is not None:
                if self.T is None:
                    self.SV_liquid, self.SV_gas = self.phase_velocity_G_x()
                else:
                    self.liquid_density = CP.PropsSI('D', 'T', self.T + 273, 'Q', 0, self.substance)      # Плотность жидкости [kg/m³]
                    mu_liq = CP.PropsSI('VISCOSITY', 'T', self.T + 273, 'Q', 0, self.substance)   # Вязкость жидкости [Pa·s]
                    self.liquid_viscosity = mu_liq

                    # Свойства пара (Q=1)
                    self.gas_density = CP.PropsSI('D', 'T', self.T + 273, 'Q', 1, self.substance)         # Плотность пара [kg/m³]
                    mu_gas = CP.PropsSI('VISCOSITY', 'T', self.T + 273, 'Q', 1, self.substance)      # Вязкость пара [Pa·s]
                    self.gas_viscosity = mu_gas

                    self.simplex_density = self.gas_density / self.liquid_density
                    self.simplex_viscosity = self.gas_viscosity / self.liquid_viscosity

                    self.delta_density = self.liquid_density - self.gas_density

                    self.SV_liquid, self.SV_gas, self.G = self.phase_velocity_G_x()
            else:
                print(f"G is None: {self.G is None}, X is None: {self.x is None}")
                raise ValueError("Недостаточно данных для расчета скоростей фаз")
            
    def phase_velocity_G_x(self):
        """
        Расчет расходных скоростей фаз из массовой скорости
        с поддержкой векторных вычислений для меняющегося паросодержания
        """
        
        # Проверки
        if self.G is None or self.x is None:
            raise ValueError("Для расчета скоростей требуются G и x")
        
        if self.liquid_density is None or self.gas_density is None:
            raise ValueError("Для расчета скоростей требуются плотности фаз")
        
        # Преобразуем в массивы
        G_array = np.array(self.G)
        x_array = np.array(self.x)
        
        # Обеспечиваем правильную размерность массивов
        if G_array.ndim == 0:  # Скаляр
            G_array = np.array([G_array])
        
        if x_array.ndim == 0:  # Скаляр
            x_array = np.array([x_array])
        
        # Используем np.outer для всех комбинаций G и x
        SV_liquid = np.outer(G_array, 1 - x_array) / self.liquid_density
        SV_gas = np.outer(G_array, x_array) / self.gas_density

        G_flat = np.repeat(G_array, len(x_array))

        return SV_liquid, SV_gas, G_flat

    # Число Рейнольдса для жидкости
    def Re_liquid(self, jl):
        return (self.liquid_density * jl * self.d) / self.liquid_viscosity

    def Ec(self, jl):
        Re_l = self.Re_liquid(jl)
        if Re_l <= 2000:
            ec = 64 / Re_l
        else:
        # ec =  0.3164 * (Re_l) ** (-0.25)
        # ec = 1 / (1.82 * np.log10(Re_l) - 1.64) ** 2
            ec = (1.82 * np.log10(self.Re_liquid(jl)) - 1.64) ** (-2)
        return ec
        
    # Диаметр межфазной поверхности 
    def Di(self, B):
        return self.d - 2 * B

    # Истинное объемное паросодержание
    def Fi(self, B):
        return ((self.d - 2 * B) / self.d) ** 2
        
    # Число Рейнольдса для газообразной фазы
    def RE0_gas(self, B, jg): 
        fi = self.Fi(B)
        di = self.Di(B)
        return (self.gas_density * jg / fi * di) / self.gas_viscosity

    def E0(self, B, jg):
        Re_G = self.RE0_gas(B, jg)
        # return (0.3164 * (self.RE0_gas(B, jg)) ** (-0.25))
        return 1 / (1.82 * np.log10(Re_G) - 1.64) ** 2
        # return ( 1.82 * np.log10(self.RE0_gas(B, jg) - 1.64) ) ** (-2)

    # Коэффициент межфазного трения Уоллиса 
    def Ei(self, B, jg):
        e0 = self.E0(B, jg)
        if self.ki is None:
            return e0 * (1 + (24 * (self.liquid_density / self.gas_density) ** (1 / 3) * B) / self.d)
        else:
            return e0 * (1 + (self.ki * B) / self.d)
    
    def Tc(self, B, jl):
        ec = self.Ec(jl)
        fi = self.Fi(B)
        return (ec * self.liquid_density * (jl) ** 2 / (8 * (1 - fi) ** 2)) 

    def wb(self, B, jl): 
        T_c = self.Tc(B, jl)
        form = (T_c / self.liquid_density) ** 0.5
        # return  (2.5 * np.log((B * form / self.liquid_viscosity)) + 5.5) * form
        return 0
    
    # Функция для расчета касательного напряжения 
    def Ti(self, B, jg, jl): 
        E_i = self.Ei(B, jg)
        fi = self.Fi(B)
        if self.flg_wb:
            w_b = self.wb(B, jl)
        else:
            w_b = 0
        return (E_i * self.gas_density * (jg / fi - w_b) ** 2 / 8)

    # Функция для расчета градиента давления 
    def calcDPDZ(self, B, jg, jl):
        Ti = self.Ti(B, jg, jl)
        di = self.Di(B)
        return 4.0 * Ti / di

    # Функция по которой считается толщина пленки 
    def equation(self, B, jg, jl):    
        LHS = self.Ti(B, jg, jl) 
        RHS = self.Tc(B, jl) * self.Di(B) / self.d
        return LHS - RHS
        

    # Функция для расчета толщины пленки 
    def calcOnePoint(self, args):
        sol = optimize.root_scalar(self.equation,
                                args=args,   
                                bracket=[1.0e-6, self.d / 2 - 1.0e-6], 
                                method='brentq')
        return sol.root

    def alpha(self, B):
        lam = CP.PropsSI('CONDUCTIVITY', 'T', self.T + 273, 'Q', 0, self.substance)
        a = lam / B
        return a
    
    @property
    def reduced_pressure(self):
        P_crit = CP.PropsSI('Pcrit', self.substance)  # Критическое давление
        P_sat = CP.PropsSI('P', 'T', self.T + 273, 'Q', 0, self.substance)  # Давление насыщения
        return P_sat / P_crit  # Приведённое давление

    # Функция всех параметров в 1 точке 
    def calculate_one_point(self, jg, jl, x, G):
        params = (jg, jl)
        # Расчет толщины пленки
        B = self.calcOnePoint(params) 
        
        # Расчет градиента давления
        dpdz = self.calcDPDZ(B, jg, jl) 
        ReL = self.Re_liquid(jl)
        ReG = self.RE0_gas(B, jg)

        # Расчет fi
        fi = self.Fi(B)

        # Расчет КТО
        alph = self.alpha(B)

        # Расчет критического давления 
        Pcrit = self.reduced_pressure

        if self.flg_wb:
            w_b = self.wb(B, jl)
        else:
            w_b = 0
        
        Res = {
           'Substance': self.substance, 
            'x': x,
            'G': G,
            'T': self.T,
            'Liquid density': self.liquid_density,
            'Gas density': self.gas_density,
            'Lquid viscosity': self.liquid_viscosity,
            'Gas viscosity': self.gas_viscosity,
            'Simplex density':self.simplex_density,
            'Simplex viscosity':self.simplex_viscosity,
            'jl': jl,
            'jg': jg,
            'Re liquid': ReL,
            'Re gas': ReG,
            'fi': fi,
            'alpha': alph,
            'Pred': Pcrit,
            'B': B,
            'DpDz': dpdz
        }
        
        return Res
    
    # Итоговая функция расчета для всех данных точек 
    def calculate(self):
        Res = []
        
        # Проверяем, являются ли массивы одномерными
        if self.SV_gas.ndim == 1 and self.SV_liquid.ndim == 1:
            # Одномерный случай - параллельная обработка
            for jg, jl, x, g in zip(self.SV_gas, self.SV_liquid, self.x, self.G):
                Res.append(self.calculate_one_point(jg, jl, x, g))
        else:
            # Многомерный случай - вложенная обработка
            for arr_gas, arr_liquid in zip(self.SV_gas, self.SV_liquid):
                res_row = []
                for jg, jl, x, g in zip(arr_gas, arr_liquid, self.x, self.G):
                    res_row.append(self.calculate_one_point(jg, jl, x, g))
                Res.append(res_row)
        
        # Распаковка единичного результата
        return Res[0] if len(Res) == 1 else Res
    
    
