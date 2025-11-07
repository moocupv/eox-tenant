# eox_tenant/middleware.py

"""
Middleware para detección de idioma en eox-tenant.
"""
from django.utils.translation import get_language
from eox_tenant.models import set_current_language


class TenantLanguageMiddleware:
    """
    Middleware que detecta el idioma del usuario y lo guarda en thread-local.
    
    Prioridad de detección:
    1. Idioma del perfil de usuario (si está autenticado)
    2. Idioma de la sesión Django
    3. Idioma del navegador (Accept-Language header)
    4. Idioma por defecto del sistema
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Detectar idioma del usuario
        language = self._get_user_language(request)
        
        # Guardar en thread-local para acceso desde cualquier parte
        set_current_language(language)
        
        # Guardar también en request para acceso directo si es necesario
        request.tenant_language = language
        
        response = self.get_response(request)
        
        # Limpiar thread-local después de la request (importante para evitar leaks)
        set_current_language(None)
        
        return response
    
    def _get_user_language(self, request):
        """
        Detecta el idioma del usuario con la siguiente prioridad:
        1. Idioma del perfil de usuario (si está autenticado)
        2. Idioma de la sesión Django
        3. Idioma del navegador (Accept-Language header)
        4. Idioma por defecto
        
        Args:
            request: HttpRequest object
        
        Returns:
            str: Código de idioma detectado
        """
        # 1. Idioma del perfil de usuario autenticado
        if hasattr(request, 'user') and request.user.is_authenticated:
            user_language = self._get_user_profile_language(request.user)
            if user_language:
                return user_language
        
        # 2. Idioma actual de Django (puede venir de sesión o LocaleMiddleware)
        current_language = get_language()
        if current_language and current_language != 'en-us':
            # Normalizar: en-us -> en
            return current_language.lower().replace('_', '-')
        
        # 3. Idioma del navegador (Accept-Language header)
        browser_language = self._get_browser_language(request)
        if browser_language:
            return browser_language
        
        # 4. Idioma por defecto
        from django.conf import settings
        return getattr(settings, 'LANGUAGE_CODE', 'en').lower().replace('_', '-')
    
    def _get_user_profile_language(self, user):
        """
        Obtiene el idioma del perfil del usuario en OpenEdX.
        
        Args:
            user: User object
        
        Returns:
            str: Código de idioma del perfil o None
        """
        try:
            # OpenEdX guarda el idioma en UserPreference
            from openedx.core.djangoapps.user_api.preferences.api import get_user_preference
            user_language = get_user_preference(user, 'pref-lang')
            
            if user_language:
                # Normalizar el código
                return user_language.lower().replace('_', '-')
        except (ImportError, AttributeError, Exception):
            # Si no estamos en OpenEdX o hay algún error, continuar
            pass
        
        # Intentar obtener de user.profile (si existe)
        try:
            if hasattr(user, 'profile') and hasattr(user.profile, 'language'):
                language = user.profile.language
                if language:
                    return language.lower().replace('_', '-')
        except Exception:
            pass
        
        return None
    
    def _get_browser_language(self, request):
        """
        Obtiene el idioma preferido del navegador desde Accept-Language header.
        
        Formato del header: "es-ES,es;q=0.9,en;q=0.8,fr;q=0.7"
        
        Args:
            request: HttpRequest object
        
        Returns:
            str: Código de idioma del navegador o None
        """
        accept_language = request.META.get('HTTP_ACCEPT_LANGUAGE', '')
        
        if not accept_language:
            return None
        
        try:
            # Parse Accept-Language header
            languages = []
            for lang_entry in accept_language.split(','):
                lang_entry = lang_entry.strip()
                
                # Separar idioma y quality factor
                if ';' in lang_entry:
                    lang, quality_str = lang_entry.split(';', 1)
                    try:
                        # Extraer el valor q (quality)
                        quality = float(quality_str.split('=')[1])
                    except (IndexError, ValueError):
                        quality = 1.0
                else:
                    lang = lang_entry
                    quality = 1.0
                
                # Normalizar el código de idioma
                lang = lang.strip().lower().replace('_', '-')
                languages.append((lang, quality))
            
            # Ordenar por quality factor (mayor primero)
            languages.sort(key=lambda x: x[1], reverse=True)
            
            # Retornar el idioma con mayor prioridad
            if languages:
                return languages[0][0]
        except Exception:
            # Si hay cualquier error parseando, ignorar
            pass
        
        return None


class TenantLanguageDebugMiddleware:
    """
    Middleware opcional para debugging de detección de idioma.
    Solo usar en desarrollo.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        from eox_tenant.models import get_current_language
        
        # Log del idioma detectado
        detected_language = get_current_language()
        
        if hasattr(request, 'user') and request.user.is_authenticated:
            user_info = f"User: {request.user.username}"
        else:
            user_info = "User: Anonymous"
        
        browser_lang = request.META.get('HTTP_ACCEPT_LANGUAGE', 'N/A')
        
        print(f"[TenantLanguage] {user_info} | Detected: {detected_language} | Browser: {browser_lang}")
        
        response = self.get_response(request)
        return response
