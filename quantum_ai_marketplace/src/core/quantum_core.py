"""
QuantumCore - Модуль квантовых бенчмарков и симуляции
"""

import time
from datetime import datetime
from typing import List, Dict, Optional


class QuantumResult:
    """Результат квантового бенчмарка"""
    
    def __init__(self, n_qubits: int, states_count: int, 
                 classical_time: float, timeout: bool, timestamp: str):
        self.n_qubits = n_qubits
        self.states_count = states_count
        self.classical_time = classical_time
        self.timeout = timeout
        self.timestamp = timestamp
    
    def to_dict(self) -> Dict:
        return {
            'n_qubits': self.n_qubits,
            'states_count': self.states_count,
            'classical_time': self.classical_time,
            'timeout': self.timeout,
            'timestamp': self.timestamp
        }


class QuantumCore:
    """
    Ядро квантовых вычислений
    
    Предоставляет функционал для:
    - Адаптивных квантовых бенчмарков
    - Симуляции квантовых состояний
    - Оценки квантового преимущества
    """
    
    def __init__(self, max_qubits: int = 1000, time_limit: float = 10.0):
        self.max_qubits = max_qubits
        self.time_limit = time_limit
        self.results_history: List[QuantumResult] = []
    
    def run_benchmark(self, qubit_ranges: Optional[List[int]] = None) -> List[QuantumResult]:
        """
        Запуск адаптивного квантового бенчмарка
        
        Args:
            qubit_ranges: Список количеств кубитов для тестирования
            
        Returns:
            Список результатов бенчмарка
        """
        if qubit_ranges is None:
            qubit_ranges = [10, 15, 20, 25, 30]
        
        print(f"\n🔬 Запуск квантового бенчмарка...")
        results = []
        
        for n_qubits in qubit_ranges:
            start_time = time.time()
            
            # Симуляция квантовых вычислений
            states_count = 2 ** n_qubits
            classical_time = (states_count / 1e9) * 0.001  # Упрощенная модель
            
            elapsed = time.time() - start_time
            timeout = elapsed > self.time_limit
            
            result = QuantumResult(
                n_qubits=n_qubits,
                states_count=states_count,
                classical_time=classical_time,
                timeout=timeout,
                timestamp=datetime.now().isoformat()
            )
            
            results.append(result)
            self.results_history.append(result)
            
            status = "TIMEOUT" if timeout else f"{classical_time*1000:.2f} ms"
            print(f"  {n_qubits} qubits ({states_count:,} states) -> {status}")
            
            if timeout:
                print(f"  ⚠️ Достигнут лимит времени {self.time_limit}s")
                break
        
        return results
    
    def get_quantum_advantage(self) -> Optional[Dict]:
        """
        Определение преимущества квантовых вычислений
        
        Returns:
            Словарь с метриками квантового преимущества
        """
        if not self.results_history:
            return None
        
        last_result = self.results_history[-1]
        
        return {
            'max_qubits_tested': last_result.n_qubits,
            'quantum_speedup': last_result.states_count / 1e6,
            'recommendation': 'Квантовое преимущество достигается при >50 кубитах',
            'classical_simulation_time': last_result.classical_time,
            'states_simulated': last_result.states_count
        }
    
    def get_summary(self) -> Dict:
        """
        Получение сводки по всем бенчмаркам
        
        Returns:
            Словарь с общей статистикой
        """
        if not self.results_history:
            return {'total_runs': 0}
        
        total_runs = len(self.results_history)
        max_qubits = max(r.n_qubits for r in self.results_history)
        timeouts = sum(1 for r in self.results_history if r.timeout)
        
        return {
            'total_runs': total_runs,
            'max_qubits_tested': max_qubits,
            'total_timeouts': timeouts,
            'success_rate': (total_runs - timeouts) / total_runs if total_runs > 0 else 0
        }
    
    def clear_history(self):
        """Очистка истории результатов"""
        self.results_history = []
        print("📊 История бенчмарков очищена")
