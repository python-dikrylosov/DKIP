"""
Quantum Project - Hourly Reports to VK (Ver2)
Отправляет отчеты каждый час с правильной обработкой кодировки
"""

import sys
import time
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from pathlib import Path
from datetime import datetime

# Путь к quantum_project
PROJECT_PATH = Path(__file__).parent / "src"
sys.path.insert(0, str(PROJECT_PATH))

import requests
from quantum_project.algorithms.comparator import AdaptiveComparator
from quantum_project.core.system_info import get_system_info


# === НАСТРОЙКИ ===
GROUP_SCREEN_NAME = 'dikrylosov'
# Для безопасности лучше использовать переменные окружения, но оставляем как есть для простоты
ACCESS_TOKEN = 'vk1.a.qyYgyQgO3EhOXXC4O-hBHRWus1MDFAfRxr8RuVjaZYUFV_6AO_wOcmqUdbJdIjX9-PVeTWHlcauhy-auZvl2GJetw_9yy1ChSjqoBsjAoiJ4W_rDxKuXUP5eAE9zT7udkCTNdYMzEF8WfWtPna3vWv9utdX2Rhz5SYrcPBu-pigiwmX4UPIfcX5UtBhhF4zt693Xwiu_a0hdSZg8N8RKJw'
API_VERSION = '5.131'

# Локальная модель
MODEL_PATH = "./Qwen2-7B"

# Интервал между постатами в секундах (1 час = 3600 секунд)
INTERVAL_SECONDS = 3600

# Промпт для модели
CHAT_PROMPT = "Кратко объясните преимущества квантовых компьютеров перед классическими."


def safe_print(text):
    """Безопасный вывод в консоль, заменяет проблемные символы"""
    try:
        print(text)
    except UnicodeEncodeError:
        # Заменяем несupported символы на ближайшие ASCII эквиваленты или удаляем
        cleaned = ''.join(c if ord(c) < 128 else '?' for c in text)
        print(cleaned)


def load_local_model():
    """Загружает локальную модель Qwen2-7B"""
    safe_print("Загрузка локальной модели...")
    try:
        tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH, trust_remote_code=True)
        model = AutoModelForCausalLM.from_pretrained(
            MODEL_PATH,
            torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
            trust_remote_code=True,
            low_cpu_mem_usage=True
        )
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        model.to(device)
        model.eval()
        safe_print(f"Модель загружена на {device}")
        return model, tokenizer, device
    except Exception as e:
        safe_print(f"Ошибка загрузки модели: {e}")
        return None, None, None


def chat_with_model(model, tokenizer, device, prompt):
    """Получает ответ от локальной модели"""
    try:
        inputs = tokenizer(prompt, return_tensors="pt").to(device)
        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                max_new_tokens=256,
                temperature=0.7,
                top_p=0.9,
                do_sample=True,
                pad_token_id=tokenizer.eos_token_id
            )
        response = tokenizer.decode(outputs[0], skip_special_tokens=True)
        # Убираем входной промпт из ответа, если он включен
        if response.startswith(prompt):
            response = response[len(prompt):].strip()
        return response
    except Exception as e:
        safe_print(f"Ошибка генерации: {e}")
        return f"Ошибка: {e}"


def get_group_id():
    resp = requests.get(
        'https://api.vk.com/method/groups.getById ',
        params={
            'group_ids': GROUP_SCREEN_NAME,
            'v': API_VERSION,
            'access_token': ACCESS_TOKEN
        }
    )
    data = resp.json()
    if 'error' in data:
        raise Exception(f"API error: {data['error']['error_msg']}")
    return data['response'][0]['id']


def run_benchmark():
    safe_print("\n" + "=" * 60)
    safe_print("КВАНТОВЫЙ БЕНЧМАРК")
    safe_print("=" * 60)
    safe_print("Max qubits: 1000 | Time limit: 10s\n")
    
    comp = AdaptiveComparator(max_qubits=1000, time_limit=10.0)
    
    safe_print("Running superposition benchmark...")
    results = comp.benchmark_superposition_adaptive()
    
    comp.print_summary()
    
    return results, comp


def format_report(chat_prompt, chat_response, results, info):
    now = datetime.now().strftime("%d.%m.%Y %H:%M")
    
    # System info
    sys_text = f"""СИСТЕМА:
CPU: {info.processor}
RAM: {info.total_ram_gb:.1f} GB"""
    if info.has_cuda:
        sys_text += f"\nGPU: {info.gpu_name}"
    
    # Benchmark results
    bench_lines = ["\nБЕНЧМАРК СУПЕРПОЗИЦИИ:\n"]
    
    for r in results:
        ms = r.classical_time * 1000
        if r.timeout:
            bench_lines.append(f"  {r.n_qubits} qubits ({r.states_count:,}) -> TIMEOUT")
        else:
            bench_lines.append(f"  {r.n_qubits} qubits ({r.states_count:,}) -> {ms:.2f} ms")
    
    # Summary
    max_q = max(r.n_qubits for r in results)
    last = results[-1]
    
    summary = f"""
СВОДКА:
Max tested: {max_q} qubits
Time limit (1s) exceeded at: {last.n_qubits} qubits

ПРИМЕЧАНИЕ: Классическая симуляция 30 кубит ≈ 17 мин
           40 кубит ≈ 12 дней — нужны квантовые компьютеры!

#quantum #python #AI #квантовые_вычисления #локальная_ИИ"""
    
    chat_section = f"""[ДИАЛОГ С ЛОКАЛЬНОЙ МОДЕЛЮ]:
Промпт: "{chat_prompt}"
Ответ: "{chat_response}" """
    
    return f"""КВАНТОВОЕ ТЕСТИРОВАНИЕ С ИИ
{now}

{sys_text}

{chat_section}
{"".join(bench_lines)}
{summary}"""


def post_to_vk(group_id, message):
    # Используем UTF-8 явно в заголовках для предотвращения проблем с кодировкой
    headers = {'Content-Type': 'application/x-www-form-urlencoded; charset=utf-8'}
    resp = requests.post(
        'https://api.vk.com/method/wall.post ',
        params={
            'access_token': ACCESS_TOKEN,
            'owner_id': -group_id,
            'message': message,
            'v': API_VERSION,
        },
        headers=headers
    )
    result = resp.json()
    
    if 'error' in result:
        raise Exception(f"VK error: {result['error']['error_msg']}")
    
    post_id = result['response']['post_id']
    return f"https://vk.com/ {GROUP_SCREEN_NAME}?w=wall-{group_id}_{post_id}"


def main():
    safe_print("=" * 60)
    safe_print("ЗАПУСК ПОЧАСОВЫХ ОТЧЕТОВ В VK (Ver2)")
    safe_print("=" * 60)
    safe_print(f"Интервал: {INTERVAL_SECONDS} секунд ({INTERVAL_SECONDS//60} минут)")
    safe_print(f"Промпт для модели: {CHAT_PROMPT}")
    safe_print("=" * 60)
    
    # Загружаем модель один раз
    model, tokenizer, device = load_local_model()
    if model is None:
        safe_print("Критическая ошибка: не удалось загрузить модель. Выход.")
        return 1
    
    try:
        cycle_count = 0
        while True:
            cycle_count += 1
            safe_print(f"\n--- Цикл {cycle_count} ---")
            start_time = time.time()
            
            try:
                # Диалог с локальной моделью
                safe_print(f"\nПромпт для модели: {CHAT_PROMPT}")
                chat_response = chat_with_model(model, tokenizer, device, CHAT_PROMPT)
                safe_print(f"Ответ модели получен (длина: {len(chat_response)} символов)")
                
                # Get system info
                info = get_system_info()
                safe_print(f"System: {info.total_ram_gb:.0f} GB RAM")
                
                # Run benchmark
                results, comp = run_benchmark()
                
                # Format report
                report = format_report(CHAT_PROMPT, chat_response, results, info)
                
                # Post to VK
                group_id = get_group_id()
                url = post_to_vk(group_id, report)
                
                safe_print(f"\n✅ Успешно опубликовано: {url}")
                
            except Exception as e:
                safe_print(f"❌ Ошибка в цикле {cycle_count}: {e}")
                # Продолжаем следующий цикл несмотря на ошибку
            
            # Вычисляем время до следующего цикла
            elapsed_cycle = time.time() - start_time
            wait_time = max(0, INTERVAL_SECONDS - elapsed_cycle)
            
            if wait_time > 0:
                safe_print(f"\n⏳ Ожидание {int(wait_time)} секунд до следующего цикла...")
                time.sleep(wait_time)
            else:
                safe_print(f"\n⚠️ Цикл занял больше времени ({int(elapsed_cycle)}с) чем интервал ({INTERVAL_SECONDS}с). Следующий цикл начнется сразу.")
    
    except KeyboardInterrupt:
        safe_print("\n\n🛑 Получен сигнал завершения. Останавливаем почасовые отчеты...")
        return 0
    except Exception as e:
        safe_print(f"\n💥 Критическая ошибка: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
