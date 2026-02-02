# tests/test_re_liquid.py
"""
Пример тестирования одного метода - Re_liquid
Это шаблон для тестирования других методов
"""
import pytest
import numpy as np
from class_DpDz import DpDz

class TestReLiquidMethod:
    """
    Тестирование метода Re_liquid.
    
    Метод: Re_liquid(self, jl)
    Назначение: Расчет числа Рейнольдса для жидкой фазы
    Формула: Re = (ρ_l * jl * d) / μ_l
    """
    
    @pytest.fixture
    def sample_instance(self):
        """Создает экземпляр для тестирования"""
        params = {
            'Substance': 'Water',
            'Temperature': 100,
            'Liquid density': 958.4,      # кг/м³
            'Liquid viscosity': 0.00028,   # Па·с
            'Gas density': 0.598,
            'Gas viscosity': 0.000012,
            'Liquid velocity': 0.5,        # м/с (но для Re_liquid не важно)
            'Gas velocity': 5.0,
        }
        
        return DpDz(
            g=9.81,
            d=0.01,      # 10 мм в метрах
            ki=24,
            thermodinamic_params=params,
            value_fb=False
        )
    
    def test_method_exists(self, sample_instance):
        """Проверяем, что метод существует"""
        # ШАГ 1: Проверяем наличие метода
        assert hasattr(sample_instance, 'Re_liquid')
        assert callable(sample_instance.Re_liquid)
        print("✓ Метод Re_liquid существует")
    
    def test_method_signature(self):
        """Проверяем сигнатуру метода"""
        import inspect
        
        # Получаем сигнатуру метода из класса
        sig = inspect.signature(DpDz.Re_liquid)
        params = list(sig.parameters.keys())
        
        print(f"\nСигнатура метода: Re_liquid{sig}")
        print(f"Параметры: {params}")
        
        # Ожидаем: self и jl
        assert len(params) == 2, f"Ожидалось 2 параметра, получено {len(params)}"
        assert params[0] == 'self', "Первый параметр должен быть 'self'"
        # Второй параметр может называться 'jl' или по-другому
        print(f"✓ Метод принимает параметр: {params[1]}")
    
    def test_calculation_positive_velocity(self, sample_instance):
        """Тест расчета для положительной скорости"""
        # ШАГ 2: Проверяем корректный расчет
        
        # Тестовые данные
        jl = 0.5  # м/с
        expected_re = (958.4 * jl * 0.01) / 0.00028
        
        # Вызываем метод
        result = sample_instance.Re_liquid(jl)
        
        print(f"\nТест с jl = {jl} м/с:")
        print(f"  Ожидаемый Re: {expected_re}")
        print(f"  Полученный Re: {result}")
        
        # Проверяем
        assert isinstance(result, (float, int)), f"Ожидался float/int, получен {type(result)}"
        assert np.isclose(result, expected_re, rtol=1e-10), \
            f"Расчет не совпадает: ожидалось {expected_re}, получено {result}"
        print(f"✓ Расчет верный")
    
    def test_calculation_zero_velocity(self, sample_instance):
        """Тест расчета для нулевой скорости"""
        # ШАГ 3: Проверяем граничный случай
        
        jl = 0.0
        result = sample_instance.Re_liquid(jl)
        
        print(f"\nТест с jl = {jl} м/с:")
        print(f"  Полученный Re: {result}")
        
        assert result == 0.0, f"При jl=0 Re должен быть 0, получено {result}"
        print(f"✓ При нулевой скорости Re = 0")
    
    def test_calculation_negative_velocity(self, sample_instance):
        """Тест расчета для отрицательной скорости (если допустимо)"""
        # ШАГ 4: Проверяем нестандартные входные данные
        
        jl = -0.5
        result = sample_instance.Re_liquid(jl)
        
        print(f"\nТест с jl = {jl} м/с (отрицательная):")
        print(f"  Полученный Re: {result}")
        
        # Число Рейнольдса может быть отрицательным для отрицательной скорости
        # Это зависит от физического смысла
        expected = (958.4 * jl * 0.01) / 0.00028
        assert np.isclose(result, expected), \
            f"Ожидалось {expected} для отрицательной скорости, получено {result}"
        print(f"✓ Расчет для отрицательной скорости работает")
    
    def test_calculation_high_velocity(self, sample_instance):
        """Тест расчета для высокой скорости"""
        # ШАГ 5: Проверяем большие значения
        
        jl = 10.0  # Высокая скорость
        result = sample_instance.Re_liquid(jl)
        
        print(f"\nТест с jl = {jl} м/с (высокая скорость):")
        print(f"  Полученный Re: {result}")
        
        expected = (958.4 * jl * 0.01) / 0.00028
        assert np.isclose(result, expected), \
            f"Ожидалось {expected} для высокой скорости, получено {result}"
        assert result > 4000, f"При высокой скорости Re должен быть большим"
        print(f"✓ Расчет для высокой скорости работает")
    
    def test_calculation_multiple_values(self, sample_instance):
        """Тест расчета для нескольких значений (векторизация)"""
        # ШАГ 6: Проверяем работу с массивами (если поддерживается)
        
        jl_values = np.array([0.1, 0.5, 1.0, 2.0, 5.0])
        
        print(f"\nТест с массивом скоростей: {jl_values}")
        
        for jl in jl_values:
            result = sample_instance.Re_liquid(jl)
            expected = (958.4 * jl * 0.01) / 0.00028
            
            assert np.isclose(result, expected), \
                f"Для jl={jl}: ожидалось {expected}, получено {result}"
            print(f"  jl={jl:.1f} → Re={result:.1f} ✓")
    
    def test_dependencies(self, sample_instance):
        """Проверяем зависимости от атрибутов экземпляра"""
        # ШАГ 7: Проверяем, какие атрибуты использует метод
        
        print(f"\nЗависимости метода Re_liquid:")
        print(f"  Использует liquid_density: {sample_instance.liquid_density} кг/м³")
        print(f"  Использует d: {sample_instance.d} м")
        print(f"  Использует liquid_viscosity: {sample_instance.liquid_viscosity} Па·с")
        
        # Проверяем, что атрибуты установлены
        assert hasattr(sample_instance, 'liquid_density')
        assert hasattr(sample_instance, 'd')
        assert hasattr(sample_instance, 'liquid_viscosity')
        
        assert sample_instance.liquid_density is not None
        assert sample_instance.d is not None
        assert sample_instance.liquid_viscosity is not None
        print(f"✓ Все необходимые атрибуты установлены")
    
    def test_physical_meaning(self):
        """Объяснение физического смысла тестов"""
        print("\n" + "="*80)
        print("ФИЗИЧЕСКИЙ СМЫСЛ ТЕСТОВ ДЛЯ Re_liquid:")
        print("="*80)
        print("\nЧисло Рейнольдса (Re) характеризует режим течения:")
        print("  - Re < 2000: ламинарный режим")
        print("  - 2000 < Re < 4000: переходный режим")
        print("  - Re > 4000: турбулентный режим")
        print("\nВ наших тестах:")
        print(f"  - jl=0.5 м/с → Re≈{958.4*0.5*0.01/0.00028:.0f} (турбулентный)")
        print(f"  - jl=0.1 м/с → Re≈{958.4*0.1*0.01/0.00028:.0f} (ламинарный/переходный)")
        print(f"  - jl=10.0 м/с → Re≈{958.4*10.0*0.01/0.00028:.0f} (сильно турбулентный)")

def run_all_tests():
    """Запускает все тесты с подробным выводом"""
    print("=" * 80)
    print("ТЕСТИРОВАНИЕ МЕТОДА Re_liquid")
    print("=" * 80)
    
    # Создаем экземпляр для тестирования
    params = {
        'Substance': 'Water',
        'Temperature': 100,
        'Liquid density': 958.4,
        'Liquid viscosity': 0.00028,
        'Gas density': 0.598,
        'Gas viscosity': 0.000012,
        'Liquid velocity': 0.5,
        'Gas velocity': 5.0,
    }
    
    instance = DpDz(
        g=9.81,
        d=0.01,
        ki=24,
        thermodinamic_params=params,
        value_fb=False
    )
    
    test_class = TestReLiquidMethod()
    
    # Запускаем тесты вручную с выводом
    tests = [
        ("test_method_exists", lambda: test_class.test_method_exists(instance)),
        ("test_calculation_positive_velocity", lambda: test_class.test_calculation_positive_velocity(instance)),
        ("test_calculation_zero_velocity", lambda: test_class.test_calculation_zero_velocity(instance)),
        ("test_calculation_negative_velocity", lambda: test_class.test_calculation_negative_velocity(instance)),
        ("test_calculation_high_velocity", lambda: test_class.test_calculation_high_velocity(instance)),
        ("test_calculation_multiple_values", lambda: test_class.test_calculation_multiple_values(instance)),
        ("test_dependencies", lambda: test_class.test_dependencies(instance)),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            print(f"\n▶ Запуск теста: {test_name}")
            test_func()
            print(f"  ✅ ПРОШЕЛ: {test_name}")
            passed += 1
        except Exception as e:
            print(f"  ❌ ПРОВАЛЕН: {test_name}")
            print(f"     Ошибка: {str(e)}")
            failed += 1
    
    print("\n" + "=" * 80)
    print(f"РЕЗУЛЬТАТ: {passed} пройдено, {failed} провалено")
    print("=" * 80)
    
    if failed == 0:
        print("\n🎉 Все тесты пройдены успешно!")
        print("Теперь можно создать аналогичные тесты для других методов.")
    else:
        print("\n⚠ Некоторые тесты провалены. Нужно разобраться почему.")

if __name__ == "__main__":
    # Запускаем анализ метода
    import sys
    sys.path.insert(0, '.')
    
    # Анализируем метод
    from method_analyzer import analyze_re_liquid
    analyze_re_liquid()
    
    print("\n" + "=" * 80)
    print("ЗАПУСК ТЕСТОВ")
    print("=" * 80)
    
    # Запускаем тесты
    run_all_tests()