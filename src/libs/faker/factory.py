# coding=utf-8

from __future__ import unicode_literals
from __future__ import absolute_import

from importlib import import_module
import locale as pylocale

import logging
import sys

from faker import Generator
from faker.config import DEFAULT_LOCALE, PROVIDERS, AVAILABLE_LOCALES
from faker.utils.loading import list_module


logger = logging.getLogger(__name__)

# identify if python is being run in interactive mode. If so, disable logging.
inREPL = getattr(sys, 'ps1', False)
if inREPL:
    logger.setLevel(logging.CRITICAL)
else:
    logger.debug('Not in REPL -> leaving logger event level as is.')


class Factory(object):

    @classmethod
    def create(
            cls,
            locale=None,
            providers=None,
            generator=None,
            includes=None,
            **config):
        if includes is None:
            includes = []

        # fix locale to package name
        locale = locale.replace('-', '_') if locale else DEFAULT_LOCALE
        locale = pylocale.normalize(locale).split('.')[0]
        if locale not in AVAILABLE_LOCALES:
            msg = 'Invalid configuration for faker locale `{0}`'.format(locale)
            raise AttributeError(msg)

        config['locale'] = locale
        providers = providers or PROVIDERS

        providers += includes

        faker = generator or Generator(**config)

        for prov_name in providers:
            if prov_name == 'faker.providers':
                continue

            prov_cls, lang_found = cls._get_provider_class(prov_name, locale)
            provider = prov_cls(faker)
            provider.__provider__ = prov_name
            provider.__lang__ = lang_found
            faker.add_provider(provider)

        return faker

    @classmethod
    def _get_provider_class(cls, provider, locale=''):

        if provider_class := cls._find_provider_class(provider, locale):
            return provider_class, locale

        if locale and locale != DEFAULT_LOCALE:
            if provider_class := cls._find_provider_class(
                provider, DEFAULT_LOCALE
            ):
                return provider_class, DEFAULT_LOCALE

        if provider_class := cls._find_provider_class(provider):
            return provider_class, None

        msg = 'Unable to find provider `{0}` with locale `{1}`'.format(
            provider, locale)
        raise ValueError(msg)

    @classmethod
    def _find_provider_class(cls, provider_path, locale=None):

        provider_module = import_module(provider_path)

        if getattr(provider_module, 'localized', False):

            logger.debug(
                f'Looking for locale `{locale}` in provider `{provider_module.__name__}`.'
            )

            available_locales = list_module(provider_module)
            if not locale or locale not in available_locales:
                unavailable_locale = locale
                locale = getattr(
                    provider_module, 'default_locale', DEFAULT_LOCALE)
                logger.debug(
                    f'Specified locale `{unavailable_locale}` is not available for provider `{provider_module.__name__}`. Locale reset to `{locale}` for this provider.'
                )
            else:
                logger.debug(
                    f'Provider `{provider_module.__name__}` has been localized to `{locale}`.'
                )

            path = "{provider_path}.{locale}".format(
                provider_path=provider_path,
                locale=locale,
            )
            provider_module = import_module(path)

        else:

            logger.debug(
                f'Provider `{provider_module.__name__}` does not feature localization. Specified locale `{locale}` is not utilized for this provider.'
            )

            if locale is not None:
                provider_module = import_module(provider_path)

        return provider_module.Provider
