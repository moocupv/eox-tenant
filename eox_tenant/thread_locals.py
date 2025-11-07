"""Thread-local storage utilities for eox_tenant."""
import threading

# Thread-local storage para el idioma actual
_thread_locals = threading.local()


def set_current_language(language):
    """
    Guarda el idioma actual en thread-local storage.
    
    Args:
        language (str): Código de idioma a establecer
    """
    _thread_locals.language = language


def get_current_language():
    """
    Obtiene el idioma actual desde thread-local storage.
    
    Returns:
        str: Código de idioma actual o None si no está establecido
    """
    return getattr(_thread_locals, 'language', None)
