# test_dpdz.py
import pytest
import numpy as np
from class_DpDz import DpDz


class TestDpDz:
    """Тесты для класса DpDz"""

    @pytest.fixture
    def basic_params(self):
        """Базовые параметры для инициализации класса"""
        return {
            "g": 9.81,
            "d": 0.1,
            "ki": 24,
            "thermodinamic_params": {
                "Substance": "Water",
                "Liquid density": 1000.0,
                "Liquid viscosity": 0.001,
                "Gas density": 1.2,
                "Gas viscosity": 1.8e-5,
                "G": 100.0,
                "x": 0.5,
                "Temperature": 20.0,
                "Pressure": 101325.0
            },
            "value_fb": False
        }

    @pytest.fixture
    def dpdz_obj(self, basic_params):
        """Создание экземпляра DpDz с базовыми параметрами"""
        return DpDz(**basic_params)

    def test_initialization(self, dpdz_obj, basic_params):
        """Тест инициализации класса"""
        assert dpdz_obj.g == basic_params["g"]
        assert dpdz_obj.d == basic_params["d"]
        assert dpdz_obj.ki == basic_params["ki"]
        assert dpdz_obj.substance == basic_params["thermodinamic_params"]["Substance"]
        assert dpdz_obj.flg_wb == basic_params["value_fb"]

    def test_phase_velocity_calculation(self, dpdz_obj):
        """Тест расчета скоростей фаз"""
        jl, jg = dpdz_obj.phase_velocity_G_x()
        
        # Проверяем, что скорости - массивы numpy
        assert isinstance(jl, np.ndarray)
        assert isinstance(jg, np.ndarray)
        
        # Проверяем правильность расчетов для тестовых значений
        G = dpdz_obj.G
        x = dpdz_obj.x
        rho_l = dpdz_obj.liquid_density
        rho_g = dpdz_obj.gas_density
        
        expected_jl = G * (1 - x) / rho_l
        expected_jg = G * x / rho_g
        
        np.testing.assert_array_almost_equal(jl.ravel(), expected_jl.ravel())
        np.testing.assert_array_almost_equal(jg.ravel(), expected_jg.ravel())

    def test_re_liquid(self, dpdz_obj):
        """Тест расчета числа Рейнольдса для жидкости"""
        jl = 1.0  # тестовая скорость
        expected_re = (dpdz_obj.liquid_density * jl * dpdz_obj.d) / dpdz_obj.liquid_viscosity
        calculated_re = dpdz_obj.Re_liquid(jl)
        
        assert pytest.approx(calculated_re, rel=1e-6) == expected_re

    def test_ec_coefficient(self, dpdz_obj):
        """Тест коэффициента трения Ec"""
        # Ламинарный режим
        jl_laminar = 0.1  # скорость для Re <= 2000
        re_laminar = dpdz_obj.Re_liquid(jl_laminar)
        expected_ec_laminar = 64 / re_laminar if re_laminar <= 2000 else \
                             (1.82 * np.log10(re_laminar) - 1.64) ** (-2)
        
        # Турбулентный режим
        jl_turbulent = 10.0  # скорость для Re > 2000
        re_turbulent = dpdz_obj.Re_liquid(jl_turbulent)
        expected_ec_turbulent = (1.82 * np.log10(re_turbulent) - 1.64) ** (-2)
        
        calculated_ec_laminar = dpdz_obj.Ec(jl_laminar)
        calculated_ec_turbulent = dpdz_obj.Ec(jl_turbulent)
        
        assert pytest.approx(calculated_ec_laminar, rel=1e-6) == expected_ec_laminar
        assert pytest.approx(calculated_ec_turbulent, rel=1e-6) == expected_ec_turbulent

    def test_fi_and_di_calculation(self, dpdz_obj):
        """Тест расчетов истинного паросодержания и диаметра"""
        B = 0.01  # толщина пленки
        
        expected_fi = ((dpdz_obj.d - 2 * B) / dpdz_obj.d) ** 2
        expected_di = dpdz_obj.d - 2 * B
        
        calculated_fi = dpdz_obj.Fi(B)
        calculated_di = dpdz_obj.Di(B)
        
        assert pytest.approx(calculated_fi, rel=1e-6) == expected_fi
        assert pytest.approx(calculated_di, rel=1e-6) == expected_di

    def test_re_gas(self, dpdz_obj):
        """Тест расчета числа Рейнольдса для газа"""
        B = 0.01
        jg = 10.0
        
        # Расчет по формуле класса
        calculated_re = dpdz_obj.RE0_gas(B, jg)
        
        # Прямой расчет для проверки
        fi = dpdz_obj.Fi(B)
        di = dpdz_obj.Di(B)
        expected_re = (dpdz_obj.gas_density * jg / fi * di) / dpdz_obj.gas_viscosity
        
        assert pytest.approx(calculated_re, rel=1e-6) == expected_re

    def test_e0_calculation(self, dpdz_obj):
        """Тест коэффициента трения для газа"""
        B = 0.01
        jg = 10.0
        
        re_gas = dpdz_obj.RE0_gas(B, jg)
        expected_e0 = (1.82 * np.log10(re_gas) - 1.64) ** (-2)
        calculated_e0 = dpdz_obj.E0(B, jg)
        
        assert pytest.approx(calculated_e0, rel=1e-6) == expected_e0

    def test_ei_calculation(self, dpdz_obj):
        """Тест межфазного коэффициента трения"""
        B = 0.01
        jg = 10.0
        
        e0 = dpdz_obj.E0(B, jg)
        expected_ei = e0 * (1 + (24 * (dpdz_obj.liquid_density / dpdz_obj.gas_density) ** (1 / 3) * B) / dpdz_obj.d)
        calculated_ei = dpdz_obj.Ei(B, jg)
        
        assert pytest.approx(calculated_ei, rel=1e-6) == expected_ei

    def test_tc_calculation(self, dpdz_obj):
        """Тест касательного напряжения в жидкости"""
        B = 0.01
        jl = 1.0
        
        ec = dpdz_obj.Ec(jl)
        fi = dpdz_obj.Fi(B)
        expected_tc = ec * dpdz_obj.liquid_density * (jl) ** 2 / (8 * (1 - fi) ** 2)
        calculated_tc = dpdz_obj.Tc(B, jl)
        
        assert pytest.approx(calculated_tc, rel=1e-6) == expected_tc

    def test_ti_calculation_without_wb(self, dpdz_obj):
        """Тест межфазного касательного напряжения без учета wb"""
        B = 0.01
        jg = 10.0
        jl = 1.0
        
        # При flg_wb = False, wb = 0
        ei = dpdz_obj.Ei(B, jg)
        fi = dpdz_obj.Fi(B)
        expected_ti = ei * dpdz_obj.gas_density * (jg / fi) ** 2 / 8
        calculated_ti = dpdz_obj.Ti(B, jg, jl)
        
        assert pytest.approx(calculated_ti, rel=1e-6) == expected_ti

    def test_calc_dpdz(self, dpdz_obj):
        """Тест расчета градиента давления"""
        B = 0.01
        jg = 10.0
        jl = 1.0
        
        ti = dpdz_obj.Ti(B, jg, jl)
        di = dpdz_obj.Di(B)
        expected_dpdz = 4.0 * ti / di + dpdz_obj.gas_density * dpdz_obj.g
        calculated_dpdz = dpdz_obj.calcDPDZ(B, jg, jl)
        
        assert pytest.approx(calculated_dpdz, rel=1e-6) == expected_dpdz

    def test_equation_balance(self, dpdz_obj):
        """Тест уравнения баланса (должно быть близко к нулю при правильном B)"""
        # Для простоты тестируем с B = 0
        B = 0.0
        jg = 10.0
        jl = 1.0
        
        # При B=0 уравнение должно быть несбалансированным, но мы проверяем корректность вычисления
        lhs = dpdz_obj.Tc(B, jl)
        rhs = dpdz_obj.Ti(B, jg, jl) + dpdz_obj.delta_density * dpdz_obj.g * B
        equation_value = dpdz_obj.equation(B, jg, jl)
        
        expected_value = lhs - rhs
        assert pytest.approx(equation_value, rel=1e-6) == expected_value

    def test_calculate_one_point(self, dpdz_obj):
        """Тест расчета одной точки"""
        jg = 10.0
        jl = 1.0
        x = 0.5
        
        result = dpdz_obj.calculate_one_point(jg, jl, x)
        
        # Проверяем структуру результата
        expected_keys = ['jg', 'jl', 'B', 'DpDz', 'Substance', 'Re liquid', 'Re gas', 'x']
        assert all(key in result for key in expected_keys)
        
        # Проверяем типы данных
        assert isinstance(result['B'], float)
        assert isinstance(result['DpDz'], float)
        assert isinstance(result['Re liquid'], float)
        assert isinstance(result['Re gas'], float)
        
        # Проверяем, что B в допустимых пределах
        assert 0 <= result['B'] <= dpdz_obj.d / 2

    def test_calculate_method_with_single_values(self, basic_params):
        """Тест метода calculate с одиночными значениями"""
        basic_params["thermodinamic_params"]["Liquid velocity"] = [1.0]
        basic_params["thermodinamic_params"]["Gas velocity"] = [10.0]
        
        dpdz = DpDz(**basic_params)
        results = dpdz.calculate()
        
        # При одиночных значениях должен вернуться один словарь
        assert isinstance(results, dict)
        assert 'B' in results
        assert 'DpDz' in results

    def test_calculate_method_with_arrays(self, basic_params):
        """Тест метода calculate с массивами значений"""
        basic_params["thermodinamic_params"]["Liquid velocity"] = [[1.0, 2.0], [1.5, 2.5]]
        basic_params["thermodinamic_params"]["Gas velocity"] = [[10.0, 20.0], [15.0, 25.0]]
        basic_params["thermodinamic_params"]["x"] = [0.3, 0.7]
        
        dpdz = DpDz(**basic_params)
        results = dpdz.calculate()
        
        # Должен вернуться список списков словарей
        assert isinstance(results, list)
        assert len(results) == 2  # По количеству массивов
        assert all(isinstance(row, list) for row in results)
        assert all(isinstance(item, dict) for row in results for item in row)

    def test_error_handling(self):
        """Тест обработки ошибок при недостаточных данных"""
        params = {
            "g": 9.81,
            "d": 0.1,
            "ki": 24,
            "thermodinamic_params": {
                "Substance": "Water",
                # Не хватает плотностей и скоростей
            },
            "value_fb": False
        }
        
        with pytest.raises(ValueError, match="Недостаточно данных для расчета скоростей фаз"):
            DpDz(**params)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])