## Overview
This version of eox-tenant adds comprehensive internationalization (i18n) support for tenant configurations, allowing you to 
serve different content based on user language preferences.
## Table of Contents
- [Quick Start](#quick-start) - [Configuration Structure](#configuration-structure) - [Language Detection](#language-detection) 
- [API Reference](#api-reference) - [Migration Guide](#migration-guide) - [Examples](#examples) - [Best 
Practices](#best-practices)
## Quick Start
### 1. Enable i18n Middleware
Add to your Django settings (after LocaleMiddleware): ```python MIDDLEWARE_CLASSES = [
    # ... other middleware ...
    'django.middleware.locale.LocaleMiddleware', 'eox_tenant.middleware.TenantLanguageMiddleware', # ← Add this
    # ... other middleware ...
] ``` 2. Structure Your Configs Transform your tenant configs from: ```json { "PLATFORM_NAME": "My Platform", "SITE_NAME": 
  "platform.com"
}
``` To i18n format: ```json { "en": { "PLATFORM_NAME": "My Platform", "SITE_NAME": "platform.com"
  },
  "es": { "PLATFORM_NAME": "Mi Plataforma", "SITE_NAME": "plataforma.com"
  },
  "fr": { "PLATFORM_NAME": "Ma Plateforme", "SITE_NAME": "plateforme.com"
  }
}
``` 3. Access i18n Configs ```python from eox_tenant.models import TenantConfig tenant = 
TenantConfig.objects.get(external_key='my-tenant')
# Get configs for current user's language
lms_configs = tenant.lms_configs_i18n platform_name = lms_configs.get('PLATFORM_NAME')
# Or get specific language
spanish_configs = tenant.get_lms_configs_for_language('es') ```
## Configuration Structure
### Supported Configuration Types
i18n support is available for: - lms_configs - LMS/Learning Management System settings - studio_configs - Studio/CMS settings - 
theming_configs - Theme and branding settings
### i18n Structure Format
Language codes at the root level: ```json { "en": { /* English configs */ }, "es": { /* Spanish configs */ }, "es-mx": { /* 
  Mexican Spanish configs */ }, "pt": { /* Portuguese configs */ }, "pt-br": { /* Brazilian Portuguese configs */ }, "fr": { /* 
  French configs */ }, "de": { /* German configs */ }, "it": { /* Italian configs */ }, "zh": { /* Chinese configs */ }, "ja": { 
  /* Japanese configs */ }, "ko": { /* Korean configs */ }, "ar": { /* Arabic configs */ }, "ru": { /* Russian configs */ }
}
```
### Legacy Structure (Still Supported)
Non-i18n configs continue to work: ```json { "PLATFORM_NAME": "My Platform", "SITE_NAME": "platform.com"
}
``` The system automatically detects which structure is being used.
## Language Detection
### Detection Priority
The middleware detects language in this order: 1. User Profile Language (if authenticated) From UserProfile.language 2. Django 
Activated Language
   From LocaleMiddleware 3. Browser Accept-Language Header Parsed from HTTP request 4. Default Fallback Falls back to 'en'
### Language Fallback Chain
When requesting a specific language variant: `es-mx → es → en → first_available` Example: - User requests es-mx (Mexican 
Spanish) - If es-mx not available, tries es (generic Spanish) - If es not available, tries en (English) - If en not available, 
returns first available language
### Manual Language Override
```python from eox_tenant.models import set_current_language, get_current_language
# Set language for current thread
set_current_language('es')
# Get current language
current_lang = get_current_language() # Returns: 'es'
# Access configs with this language
configs = tenant.lms_configs_i18n ```
## API Reference
### Model Methods
#### get_lms_configs_for_language(language=None)
Get LMS configs for specific language with fallback. **Parameters:** - language (str, optional): Language code (e.g., 'en', 
'es', 'es-mx')
  If None, uses current thread language **Returns:** - dict: Configuration dictionary for the language **Example:** ```python
# Get Spanish configs
configs = tenant.get_lms_configs_for_language('es') platform_name = configs.get('PLATFORM_NAME')
# Use current language
configs = tenant.get_lms_configs_for_language() ```
#### get_studio_configs_for_language(language=None)
Get Studio configs for specific language with fallback. **Parameters:** - language (str, optional): Language code **Returns:** - 
dict: Studio configuration dictionary **Example:** ```python studio_configs = tenant.get_studio_configs_for_language('fr') ```
#### get_theming_configs_for_language(language=None)
Get theming configs for specific language with fallback. **Parameters:** - language (str, optional): Language code **Returns:** 
- dict: Theming configuration dictionary **Example:** ```python theme_configs = tenant.get_theming_configs_for_language('de') 
logo_url = theme_configs.get('LOGO_URL') ```
#### get_available_languages(config_type='lms')
Get list of available languages in configs. **Parameters:** - config_type (str): Type of config - 'lms', 'studio', or 'theming' 
**Returns:** - list: List of available language codes **Example:** ```python languages = tenant.get_available_languages('lms')
# Returns: ['en', 'es', 'fr']
studio_langs = tenant.get_available_languages('studio')
# Returns: ['en', 'es']
```
#### get_value_i18n(key, default=None, language=None, config_type='lms')
Get specific configuration value with i18n support. **Parameters:** - key (str): Configuration key - default (any, optional): 
Default value if key not found - language (str, optional): Language code - config_type (str): Type of config - 'lms', 'studio', 
or 'theming' **Returns:** Configuration value or default **Example:** ```python
# Get PLATFORM_NAME in Spanish
name = tenant.get_value_i18n('PLATFORM_NAME', language='es', config_type='lms')
# With default value
site = tenant.get_value_i18n('SITE_NAME', default='example.com', language='en')
# Use current language
platform = tenant.get_value_i18n('PLATFORM_NAME') ```
### Model Properties
#### lms_configs_i18n
Get LMS configs for current language. **Returns:** - dict: LMS configuration dictionary **Example:** ```python configs = 
tenant.lms_configs_i18n platform_name = configs.get('PLATFORM_NAME') ```
#### studio_configs_i18n
Get Studio configs for current language. **Returns:** - dict: Studio configuration dictionary
#### theming_configs_i18n
Get theming configs for current language. **Returns:** - dict: Theming configuration dictionary
### Utility Functions
#### set_current_language(language)
Set language for current thread. **Parameters:** - language (str): Language code or None to clear **Example:** ```python from 
eox_tenant.models import set_current_language set_current_language('es')
# Now all i18n properties use Spanish
set_current_language(None)
# Clear language
```
#### get_current_language()
Get current thread's language. **Returns:** - str or None: Current language code **Example:** ```python from eox_tenant.models 
import get_current_language lang = get_current_language() print(f"Current language: {lang}") ```
## Migration Guide
### From Legacy to i18n Configs
#### Step 1: Backup Current Configs
```python
# In Django shell
from eox_tenant.models import TenantConfig import json tenant = TenantConfig.objects.get(external_key='my-tenant')
# Backup
backup = { 'lms_configs': tenant.lms_configs, 'studio_configs': tenant.studio_configs, 'theming_configs': 
    tenant.theming_configs,
}
with open('tenant_backup.json', 'w') as f: json.dump(backup, f, indent=2) ```
#### Step 2: Transform to i18n Structure
```python
# Transform lms_configs
old_configs = tenant.lms_configs new_configs = { 'en': old_configs, # Keep English as default 'es': {
        # Add Spanish translations
        'PLATFORM_NAME': 'Mi Plataforma', 'SITE_NAME': old_configs.get('SITE_NAME'), # Keep if not translated
        # ... other keys
    }
}
tenant.lms_configs = new_configs tenant.save() ```
#### Step 3: Verify
```python
# Check it works
tenant.refresh_from_db()
# Test English
en_configs = tenant.get_lms_configs_for_language('en') print(en_configs.get('PLATFORM_NAME'))
# Test Spanish
es_configs = tenant.get_lms_configs_for_language('es') print(es_configs.get('PLATFORM_NAME'))
# Test fallback
de_configs = tenant.get_lms_configs_for_language('de') print(de_configs.get('PLATFORM_NAME')) # Should fallback to English ```
### Rollback Plan
If you need to rollback: ```python
# Restore from backup
import json with open('tenant_backup.json', 'r') as f: backup = json.load(f) tenant = 
TenantConfig.objects.get(external_key='my-tenant') tenant.lms_configs = backup['lms_configs'] tenant.studio_configs = 
backup['studio_configs'] tenant.theming_configs = backup['theming_configs'] tenant.save() ```
## Examples
### Example 1: Basic Multi-Language Setup
```json { "lms_configs": { "en": { "PLATFORM_NAME": "Education Platform", "SITE_NAME": "learn.example.com", "CONTACT_EMAIL": 
      "support@example.com"
    },
    "es": { "PLATFORM_NAME": "Plataforma Educativa", "SITE_NAME": "aprender.ejemplo.com", "CONTACT_EMAIL": "soporte@ejemplo.com"
    }
  }
}
```
### Example 2: Regional Variants
```json { "lms_configs": { "en": { "PLATFORM_NAME": "Learning Platform", "CURRENCY": "USD"
    },
    "es": { "PLATFORM_NAME": "Plataforma de Aprendizaje", "CURRENCY": "EUR"
    },
    "es-mx": { "PLATFORM_NAME": "Plataforma de Aprendizaje", "CURRENCY": "MXN"
    },
    "pt-br": { "PLATFORM_NAME": "Plataforma de Aprendizado", "CURRENCY": "BRL"
    }
  }
}
```
### Example 3: Partial Translation
You don't need to translate everything: ```json { "lms_configs": { "en": { "PLATFORM_NAME": "My Platform", "SITE_NAME": 
      "platform.com", "CONTACT_EMAIL": "support@platform.com", "TERMS_URL": "https://platform.com/terms"
    },
    "es": { "PLATFORM_NAME": "Mi Plataforma"
      // Other keys will fallback to English
    }
  }
}
```
### Example 4: View Usage
```python from django.views import View from eox_tenant.models import TenantConfig class PlatformInfoView(View): def get(self, 
    request):
        tenant = TenantConfig.objects.get(external_key='my-tenant')
        # Automatically uses request user's language
        configs = tenant.lms_configs_i18n return JsonResponse({ 'platform_name': configs.get('PLATFORM_NAME'), 'site_name': 
            configs.get('SITE_NAME'), 'available_languages': tenant.get_available_languages('lms')
        })
```
### Example 5: Template Usage
```django {% load i18n %} {# In your template #} {{ tenant.lms_configs_i18n.PLATFORM_NAME }} {{ 
tenant.theming_configs_i18n.LOGO_URL }} ```
### Example 6: Management Command
```python from django.core.management.base import BaseCommand from eox_tenant.models import TenantConfig, set_current_language 
class Command(BaseCommand):
    def handle(self, *args, **options): tenant = TenantConfig.objects.get(external_key='my-tenant')
        # Get configs for each language
        for lang in tenant.get_available_languages('lms'): set_current_language(lang) configs = tenant.lms_configs_i18n 
            self.stdout.write(
                f"{lang}: {configs.get('PLATFORM_NAME')}" ) ```
## Best Practices
1. Always Provide English Fallback ```json { "en": { "PLATFORM_NAME": "My Platform"
  },
  "es": { "PLATFORM_NAME": "Mi Plataforma"
  }
}
``` 2. Use Consistent Keys Across Languages ```json { "en": { "PLATFORM_NAME": "...", "SITE_NAME": "...", "CONTACT_EMAIL": "..."
  },
  "es": { "PLATFORM_NAME": "...", // ✓ Same keys "SITE_NAME": "...", "CONTACT_EMAIL": "..."
  }
}
``` 3. Don't Duplicate Untranslated Content ```json { "en": { "PLATFORM_NAME": "My Platform", "LOGO_URL": 
    "https://cdn.example.com/logo.png"
  },
  "es": { "PLATFORM_NAME": "Mi Plataforma"
    // ✓ LOGO_URL will fallback to English
  }
}
``` 4. Test Fallback Behavior ```python
# Test with non-existent language
configs = tenant.get_lms_configs_for_language('xx') assert configs == tenant.get_lms_configs_for_language('en') ``` 5. Document 
Available Languages ```python
# In your tenant docs
SUPPORTED_LANGUAGES = { 'lms': ['en', 'es', 'fr'], 'studio': ['en', 'es'], 'theming': ['en', 'es', 'fr', 'de']
}
``` 6. Monitor Language Usage ```python
# In middleware or analytics
from eox_tenant.models import get_current_language def track_language_usage(request): lang = get_current_language()
    # Log to analytics
    analytics.track('language_used', {'language': lang}) ``` 7. Handle Missing Translations Gracefully ```python def 
get_config_value(tenant, key, language=None):
    """Get config value with safe fallback.""" configs = tenant.get_lms_configs_for_language(language) value = configs.get(key) 
    if not value and language != 'en':
        # Fallback to English
        en_configs = tenant.get_lms_configs_for_language('en') value = en_configs.get(key) return value or f'[Missing: {key}]' 
```
## Troubleshooting
### Issue: Configs Not Changing with Language
**Solution:** Ensure middleware is enabled and placed correctly: ```python MIDDLEWARE_CLASSES = [
    # ...
    'django.middleware.locale.LocaleMiddleware', 'eox_tenant.middleware.TenantLanguageMiddleware', # After LocaleMiddleware
    # ...
] ```
### Issue: Fallback Not Working
Check: - Language codes are lowercase ('es', not 'ES') - i18n structure is detected (language codes at root) - English fallback 
exists ```python
# Debug
tenant = TenantConfig.objects.get(external_key='my-tenant') print(tenant._is_i18n_structure()) # Should be True 
print(tenant.get_available_languages('lms')) # Should list languages ```
### Issue: Getting Wrong Language
**Debug:** ```python from eox_tenant.models import get_current_language
# Check what language is active
current = get_current_language() print(f"Current language: {current}")
# Check user profile
if request.user.is_authenticated: from student.models import UserProfile profile = UserProfile.objects.get(user=request.user) 
    print(f"User profile language: {profile.language}")
```
## Performance Considerations
### Caching
Consider caching configs per language: ```python from django.core.cache import cache def get_cached_configs(tenant, language): 
    cache_key = f'tenant_configs_{tenant.id}_{language}' configs = cache.get(cache_key) if configs is None:
        configs = tenant.get_lms_configs_for_language(language) cache.set(cache_key, configs, timeout=3600) # 1 hour return 
    configs
```
### Database Queries
The i18n methods don't add extra queries - they work with existing JSON fields.
## Security Notes
- Language detection uses safe parsing of Accept-Language header - No SQL injection risk (uses JSON field queries) - 
Thread-local storage is isolated per request
## Backward Compatibility
✅ 100% Backward Compatible - Legacy configs without i18n work unchanged - No database migrations required - Existing code 
continues to work - Can mix legacy and i18n configs
## Version History
v11.8.0 - Initial i18n support Based on eox-tenant v11.7.0
## Support
For issues or questions: - Check this documentation - Review examples above - Check GitHub issues - Contact maintainers Last 
Updated: November 7, 2024 Version: 11.8.0
Base Version: eox-tenant 11.7.0
