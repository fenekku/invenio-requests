# -*- coding: utf-8 -*-
#
# Copyright (C) 2021 CERN.
# Copyright (C) 2021 Northwestern University.
# Copyright (C) 2021 TU Wien.
#
# Invenio-Requests is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Pytest configuration.

See https://pytest-invenio.readthedocs.io/ for documentation on which test
fixtures are available.
"""


import pytest
from flask_principal import Identity, Need, UserNeed
from invenio_app.factory import create_api as _create_api

from invenio_requests import current_requests
from invenio_requests.records.api import Request


@pytest.fixture(scope="module")
def celery_config():
    """Override pytest-invenio fixture.

    TODO: Remove this fixture if you add Celery support.
    """
    return {}


# @pytest.fixture(scope="module")
# def extra_entry_points():
#     """Extra entry points to load the mock_module features."""
#     return {
#         'invenio_db.model': [
#             'mock_module = mock_module.models',
#         ],
#         'invenio_jsonschemas.schemas': [
#             'mock_module = mock_module.jsonschemas',
#         ],
#         'invenio_search.mappings': [
#             'comments = mock_module.mappings',
#         ]
#     }


@pytest.fixture(scope="module")
def app_config(app_config):
    """Mimic an instance's configuration."""
    app_config["JSONSCHEMAS_HOST"] = "localhost"
    app_config["BABEL_DEFAULT_LOCALE"] = "en"
    # app_config["I18N_LANGUAGES"] = [('da', 'Danish')]
    app_config[
        "RECORDS_REFRESOLVER_CLS"
    ] = "invenio_records.resolver.InvenioRefResolver"
    app_config[
        "RECORDS_REFRESOLVER_STORE"
    ] = "invenio_jsonschemas.proxies.current_refresolver_store"
    return app_config


@pytest.fixture(scope="module")
def create_app(instance_path):
    """Application factory fixture."""
    return _create_api


@pytest.fixture(scope="module")
def identity_simple():
    """Simple identity fixture."""
    i = Identity(1)
    i.provides.add(UserNeed(1))
    i.provides.add(Need(method="system_role", value="any_user"))
    return i


@pytest.fixture()
def request_record_input_data():
    """Input data to a Request record."""
    return {
        "title": "Foo bar",
        "receiver": {"type": "baz", "id": "nyx"}
    }


@pytest.fixture()
def example_request(db, identity_simple, request_record_input_data):
    """Example record."""
    # Need to use the service to get the id I guess...
    requests_service = current_requests.requests_service
    item = requests_service.create(
        identity_simple, request_record_input_data, Request)
    return item._request
