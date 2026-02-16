from typing import Any

from managers.runtime_services import TextWindowRuntimeServices


def ensure_runtime_services(window: Any) -> TextWindowRuntimeServices:
    """TextWindow に runtime services を遅延注入して返す。"""
    services = getattr(window, "runtime_services", None)
    if isinstance(services, TextWindowRuntimeServices):
        return services
    services = TextWindowRuntimeServices(getattr(window, "main_window", None))
    setattr(window, "runtime_services", services)
    return services
