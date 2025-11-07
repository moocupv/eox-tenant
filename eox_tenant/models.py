"""
	Models for eox_tenant.
	"""
	import collections
	import threading
	from django.contrib.sites.models import Site
	from django.db import models
	from django.utils.translation import gettext_lazy as _
	from django.utils.translation import get_language
	from jsonfield.fields import JSONField
	from model_utils.models import TimeStampedModel
	from organizations.models import Organization


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


	class TenantConfig(TimeStampedModel):
		"""
		Model to persist tenant configurations.
		"""

		external_key = models.CharField(
			max_length=63,
			db_index=True,
			unique=True,
		)

		organizations = models.ManyToManyField(
			Organization,
			blank=True,
		)

		lms_configs = JSONField(
			blank=True,
			default={},
			load_kwargs={'object_pairs_hook': collections.OrderedDict}
		)

		studio_configs = JSONField(
			blank=True,
			default={},
			load_kwargs={'object_pairs_hook': collections.OrderedDict}
		)

		theming_configs = JSONField(
			blank=True,
			default={},
			load_kwargs={'object_pairs_hook': collections.OrderedDict}
		)

		meta = JSONField(
			blank=True,
			default={},
			load_kwargs={'object_pairs_hook': collections.OrderedDict}
		)

		class Meta:
			"""
			Model meta class.
			"""
			app_label = "eox_tenant"

		def __str__(self):
			"""
			String representation of the model.
			"""
			return f"<TenantConfig: {self.external_key}>"

		def _is_i18n_structure(self, configs=None):
			"""
			Detecta si la estructura de configs es i18n o legacy.
			
			Una estructura es i18n si:
			- Las claves del primer nivel son códigos de idioma (2-5 caracteres)
			- Contiene al menos 'en' o algún código ISO 639-1
			- NO contiene claves típicas de configuración OpenEdX
			
			Args:
				configs (dict): Configuración a analizar. Si es None, usa self.lms_configs
			
			Returns:
				bool: True si es estructura i18n, False si es legacy
			"""
			if configs is None:
				configs = self.lms_configs
			
			if not isinstance(configs, dict) or not configs:
				return False
			
			# Claves comunes en configuración OpenEdX (legacy)
			legacy_keys = {
				'PLATFORM_NAME', 'SITE_NAME', 'CONTACT_EMAIL', 'FOOTER_COPYRIGHT',
				'course_org_filter', 'EDNX_USE_SIGNAL', 'template_dir',
				'CONTACT_MAILING_ADDRESS', 'FOOTER_ORGANIZATION_IMAGE',
				'HOMEPAGE_OVERLAY_HTML', 'SESSION_COOKIE_DOMAIN',
				'COURSE_CATALOG_VISIBILITY_PERMISSION', 'COURSE_ABOUT_VISIBILITY_PERMISSION',
			}
			
			first_keys = set(configs.keys())
			
			# Si tiene claves legacy conocidas, es estructura legacy
			if first_keys & legacy_keys:
				return False
			
			# Si todas las claves parecen códigos de idioma, es i18n
			language_like_keys = [
				k for k in first_keys
				if isinstance(k, str) and 
				2 <= len(k) <= 5 and 
				k.replace('-', '').replace('_', '').isalpha() and
				k.islower()
			]
			
			# Si más del 50% de las claves parecen idiomas, es i18n
			if language_like_keys and len(language_like_keys) / len(first_keys) > 0.5:
				return True
			
			return False
		
		def _normalize_language_code(self, language):
			"""
			Normaliza un código de idioma a formato estándar.
			
			Args:
				language (str): Código de idioma
			
			Returns:
				str: Código normalizado (lowercase, con guiones)
			"""
			if not language:
				return 'en'
			
			# Convertir guiones bajos a guiones y a minúsculas
			return language.replace('_', '-').lower()
		
		def get_lms_configs_for_language(self, language=None):
			"""
			Obtiene la configuración LMS para el idioma especificado.
			
			Lógica de fallback:
			1. Intenta con el idioma completo (ej: 'es-mx')
			2. Si no existe, intenta con el código corto (ej: 'es')
			3. Si no existe, usa 'en'
			4. Si no es estructura i18n, retorna el dict completo (legacy)
			
			Args:
				language (str): Código de idioma. Si es None, usa get_language()
			
			Returns:
				dict: Configuración para el idioma
			"""
			configs = self.lms_configs
			
			# Si no es estructura i18n, retornar todo (legacy)
			if not self._is_i18n_structure(configs):
				return configs
			
			# Determinar idioma a usar
			if language is None:
				# Intentar obtener de thread-local primero
				language = get_current_language()
				
				# Si no está en thread-local, usar Django
				if language is None:
					language = get_language() or 'en'
			
			language = self._normalize_language_code(language)
			
			# 1. Intentar con idioma completo (es-mx, es-es, etc.)
			if language in configs:
				return configs[language]
			
			# 2. Intentar con código corto (es-mx -> es)
			short_code = language.split('-')[0]
			if short_code in configs and short_code != language:
				return configs[short_code]
			
			# 3. Fallback a inglés
			if 'en' in configs:
				return configs['en']
			
			# 4. Retornar el primer idioma disponible
			if configs:
				return list(configs.values())[0]
			
			return {}
		
		def get_studio_configs_for_language(self, language=None):
			"""
			Obtiene la configuración Studio para el idioma especificado.
			
			Similar a get_lms_configs_for_language pero para studio_configs.
			
			Args:
				language (str): Código de idioma. Si es None, usa get_language()
			
			Returns:
				dict: Configuración para el idioma
			"""
			configs = self.studio_configs
			
			# Si no es estructura i18n, retornar todo (legacy)
			if not self._is_i18n_structure(configs):
				return configs
			
			# Determinar idioma a usar
			if language is None:
				# Intentar obtener de thread-local primero
				language = get_current_language()
				
				# Si no está en thread-local, usar Django
				if language is None:
					language = get_language() or 'en'
			
			language = self._normalize_language_code(language)
			
			# Aplicar misma lógica de fallback
			if language in configs:
				return configs[language]
			
			short_code = language.split('-')[0]
			if short_code in configs and short_code != language:
				return configs[short_code]
			
			if 'en' in configs:
				return configs['en']
			
			if configs:
				return list(configs.values())[0]
			
			return {}
		
		def get_theming_configs_for_language(self, language=None):
			"""
			Obtiene la configuración de theming para el idioma especificado.
			
			Similar a get_lms_configs_for_language pero para theming_configs.
			
			Args:
				language (str): Código de idioma. Si es None, usa get_language()
			
			Returns:
				dict: Configuración para el idioma
			"""
			configs = self.theming_configs
			
			# Si no es estructura i18n, retornar todo (legacy)
			if not self._is_i18n_structure(configs):
				return configs
			
			# Determinar idioma a usar
			if language is None:
				# Intentar obtener de thread-local primero
				language = get_current_language()
				
				# Si no está en thread-local, usar Django
				if language is None:
					language = get_language() or 'en'
			
			language = self._normalize_language_code(language)
			
			# Aplicar misma lógica de fallback
			if language in configs:
				return configs[language]
			
			short_code = language.split('-')[0]
			if short_code in configs and short_code != language:
				return configs[short_code]
			
			if 'en' in configs:
				return configs['en']
			
			if configs:
				return list(configs.values())[0]
			
			return {}
		
		def get_available_languages(self, config_type='lms'):
			"""
			Retorna lista de idiomas disponibles en la configuración especificada.
			
			Args:
				config_type (str): Tipo de configuración ('lms', 'studio', 'theming')
			
			Returns:
				list: Lista de códigos de idioma disponibles (vacía si legacy)
			"""
			if config_type == 'lms':
				configs = self.lms_configs
			elif config_type == 'studio':
				configs = self.studio_configs
			elif config_type == 'theming':
				configs = self.theming_configs
			else:
				return []
			
			if not self._is_i18n_structure(configs):
				return []
			
			return list(configs.keys())
		
		@property
		def lms_configs_i18n(self):
			"""
			Property que retorna lms_configs en el idioma actual.
			
			Para usar en código nuevo:
				tenant.lms_configs_i18n.get('PLATFORM_NAME')
			
			Returns:
				dict: Configuración en el idioma actual
			"""
			return self.get_lms_configs_for_language()
		
		@property
		def studio_configs_i18n(self):
			"""
			Property que retorna studio_configs en el idioma actual.
			
			Returns:
				dict: Configuración en el idioma actual
			"""
			return self.get_studio_configs_for_language()
		
		@property
		def theming_configs_i18n(self):
			"""
			Property que retorna theming_configs en el idioma actual.
			
			Returns:
				dict: Configuración en el idioma actual
			"""
			return self.get_theming_configs_for_language()
		
		def get_value_i18n(self, key, default=None, language=None, config_type='lms'):
			"""
			Obtiene un valor de configuración en el idioma especificado.
			
			Args:
				key (str): Clave de configuración
				default: Valor por defecto
				language (str): Idioma (opcional)
				config_type (str): Tipo de configuración ('lms', 'studio', 'theming')
			
			Returns:
				Valor de la configuración o default
			"""
			if config_type == 'lms':
				configs = self.get_lms_configs_for_language(language)
			elif config_type == 'studio':
				configs = self.get_studio_configs_for_language(language)
			elif config_type == 'theming':
				configs = self.get_theming_configs_for_language(language)
			else:
				return default
			
			return configs.get(key, default)
		
		def get_organizations(self):
			"""
			Return the organizations for this tenant configuration.
			"""
			return ", ".join([org.short_name for org in self.organizations.all()])

		def get_route_domain(self):
			"""
			Return the domain for the route associated to this tenant configuration.
			"""
			try:
				return self.route.domain
			except Route.DoesNotExist:
				return "NOT CONFIGURED"

		def get_site_name(self):
			"""
			Return the SITE_NAME from lms_configs.
			"""
			return self.get_value_i18n("SITE_NAME", "NOT CONFIGURED")

		def get_template_dir(self):
			"""
			Return the template_dir from lms_configs.
			"""
			return self.get_value_i18n("template_dir", "NOT CONFIGURED")

		def get_course_org_filter(self):
			"""
			Return the course_org_filter from lms_configs.
			"""
			course_org_filter = self.get_value_i18n("course_org_filter")
			
			if isinstance(course_org_filter, list):
				return ", ".join(course_org_filter)
			
			return course_org_filter or "NOT CONFIGURED"

		def get_ednx_use_signal(self):
			"""
			Return the EDNX_USE_SIGNAL from lms_configs.
			"""
			ednx_use_signal = self.get_value_i18n("EDNX_USE_SIGNAL")
			
			if ednx_use_signal is None:
				return "EMPTY"
			
			return str(ednx_use_signal)

		@classmethod
		def get_configuration(cls, **kwargs):
			"""
			Return tenant configuration based on provided filters.
			
			Arguments:
				**kwargs: Filter arguments (e.g., external_key, domain)
			
			Returns:
				TenantConfig: First matching configuration or None
			"""
			domain = kwargs.get("domain")
			external_key = kwargs.get("external_key")
			org = kwargs.get("org")

			if domain:
				try:
					route = Route.objects.get(domain=domain)
					return route.config
				except Route.DoesNotExist:
					pass

			if external_key:
				try:
					return cls.objects.get(external_key=external_key)
				except cls.DoesNotExist:
					pass

			if org:
				try:
					organization = Organization.objects.get(short_name=org)
					return cls.objects.filter(organizations=organization).first()
				except Organization.DoesNotExist:
					pass

			return None

		def get_config_for_org(self, org):
			"""
			Return configuration for a specific organization.
			
			Args:
				org (str): Organization short name
			
			Returns:
				dict: Configuration dictionary in current language
			"""
			org_filter = self.get_value_i18n("course_org_filter")  # pylint: disable=no-member
			
			if org_filter and org in org_filter:
				return self.get_lms_configs_for_language()
			
			return {}

		@staticmethod
		def get_value(val_name, **kwargs):
			"""
			Return a configuration value for the given filters.
			
			Arguments:
				val_name (str): Name of the configuration value
				**kwargs: Filter arguments
			
			Returns:
				Value from configuration or None
			"""
			result = TenantConfig.get_configuration(**kwargs)
			
			if result:
				value = result.get_value_i18n(val_name)
				return value
			
			return None


	class Route(models.Model):
		"""
		Model to persist site routes.
		"""

		domain = models.CharField(
			_("domain name"),
			max_length=100,
			unique=True,
		)

		config = models.ForeignKey(
			TenantConfig,
			on_delete=models.CASCADE,
			related_name='route',
		)

		class Meta:
			"""
			Model meta class.
			"""
			app_label = "eox_tenant"

		def __str__(self):
			"""
			String representation of the model.
			"""
			return f"<Route: {self.domain} -> {self.config.external_key}>"


	class TenantSiteConfigProxy(models.Model):
		"""
		Proxy model for Site configuration.
		This allows accessing tenant configurations through Django's Site framework.
		"""
		
		site = models.OneToOneField(
			Site,
			on_delete=models.CASCADE,
			primary_key=True,
		)
		
		tenant_config = models.ForeignKey(
			TenantConfig,
			on_delete=models.CASCADE,
			related_name='site_configs',
		)

		class Meta:
			"""
			Model meta class.
			"""
			app_label = "eox_tenant"
			verbose_name = "Tenant Site Configuration"
			verbose_name_plural = "Tenant Site Configurations"

		def __str__(self):
			"""
			String representation of the model.
			"""
			return f"<TenantSiteConfig: {self.site.domain} -> {self.tenant_config.external_key}>"

		def get_value(self, key, default=None):
			"""
			Get a configuration value in the current language.
			
			Args:
				key (str): Configuration key
				default: Default value if key not found
			
			Returns:
				Configuration value or default
			"""
			return self.tenant_config.get_value_i18n(key, default)
