"""Модуль для получения системной информации."""

import platform
import psutil
import torch


class SystemInfo:
    """Класс для хранения системной информации."""
    
    def __init__(self, processor, total_ram_gb, has_cuda, gpu_name=None):
        self.processor = processor
        self.total_ram_gb = total_ram_gb
        self.has_cuda = has_cuda
        self.gpu_name = gpu_name


def get_system_info() -> SystemInfo:
    """Получает информацию о системе."""
    processor = platform.processor() or "Unknown"
    total_ram_gb = psutil.virtual_memory().total / (1024 ** 3)
    has_cuda = torch.cuda.is_available()
    gpu_name = None
    
    if has_cuda:
        gpu_name = torch.cuda.get_device_name(0)
    
    return SystemInfo(
        processor=processor,
        total_ram_gb=total_ram_gb,
        has_cuda=has_cuda,
        gpu_name=gpu_name
    )
