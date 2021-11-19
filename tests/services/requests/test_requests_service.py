# -*- coding: utf-8 -*-
#
# Copyright (C) 2021 CERN.
# Copyright (C) 2021 Northwestern University.
#
# Invenio-Requests is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Service tests."""
import copy

import pytest
from flask_principal import Identity, Need, UserNeed

from invenio_requests.proxies import current_requests
from invenio_requests.records.api import (
    RequestEvent,
    RequestEventFormat,
    RequestEventType,
)
from invenio_requests.records.request_types import RequestType

# Convenience fixtures


@pytest.fixture(scope="module")
def requests_service(app):
    """Request Factory fixture."""
    return current_requests.requests_service


@pytest.fixture(scope="module")
def request_events_service(app):
    """Request Factory fixture."""
    return current_requests.request_events_service


@pytest.fixture()
def create_request(example_user, request_record_input_data, requests_service):
    """Request Factory fixture."""

    def _create_request(identity, input_data=None):
        """Create a request."""
        input_data = input_data or request_record_input_data
        # Need to use the service to get the id
        item = requests_service.create(
            identity, input_data, RequestType, receiver=example_user
        )
        return item._request

    return _create_request


@pytest.fixture(scope="module")
def identity_simple_2():
    """Another simple identity fixture."""
    i = Identity(2)
    i.provides.add(UserNeed(2))
    i.provides.add(Need(method="system_role", value="any_user"))
    return i


@pytest.fixture()
def submit_request(create_request, requests_service):
    """Opened Request Factory fixture."""

    def _submit_request(identity, data=None):
        """Create and submit a request."""
        request = create_request(identity)
        id_ = request.number
        data = data or {
            "content": "Can I belong to the community?",
            "format": RequestEventFormat.HTML.value
        }
        return requests_service.execute_action(identity, id_, "submit", data)

    return _submit_request


# Tests


def test_submit_request(app, identity_simple, submit_request, request_events_service):
    result = submit_request(identity_simple)
    id_ = result._request.number
    result_dict = result.to_dict()

    RequestEvent.index.refresh()

    assert "open" == result_dict["status"]
    results = request_events_service.search(identity_simple, id_)
    assert 1 == results.total
    hits = list(results.hits)
    assert RequestEventType.COMMENT.value == hits[0]["type"]
    assert "Can I belong to the community?" == hits[0]["content"]


def test_accept_request(
        app, identity_simple, identity_simple_2, submit_request, requests_service,
        request_events_service):
    # Submit a request
    result = submit_request(identity_simple)
    id_ = result._request.number

    # Other user accepts it with comment
    data = {
        "content": "Welcome to the community!",
        "format": RequestEventFormat.HTML.value
    }
    result = requests_service.execute_action(identity_simple_2, id_, "accept", data)
    result_dict = result.to_dict()

    RequestEvent.index.refresh()

    assert "accepted" == result_dict["status"]
    results = request_events_service.search(identity_simple_2, id_)
    assert 2 == results.total  # submit comment + accept
    hits = list(results.hits)
    assert 1 == len([h for h in hits if RequestEventType.ACCEPTED.value == h["type"]])


def test_cancel_request(
        app, identity_simple, submit_request, requests_service,
        request_events_service):
    # Submit a request
    result = submit_request(identity_simple)
    id_ = result._request.number

    # Cancel it
    data = {
        "content": "",  # no comment is fine
        "format": RequestEventFormat.HTML.value
    }
    result = requests_service.execute_action(identity_simple, id_, "cancel", data)
    result_dict = result.to_dict()

    RequestEvent.index.refresh()

    assert "cancelled" == result_dict["status"]
    results = request_events_service.search(identity_simple, id_)
    assert 2 == results.total  # submit comment + cancel
    hits = list(results.hits)
    assert 1 == len([h for h in hits if RequestEventType.CANCELLED.value == h["type"]])


def test_decline_request(
        app, identity_simple, identity_simple_2, submit_request, requests_service,
        request_events_service):
    # Submit a request
    result = submit_request(identity_simple)
    id_ = result._request.number

    # Other user declines it
    data = {
        "content": "Sorry but no.",
        "format": RequestEventFormat.HTML.value
    }
    result = requests_service.execute_action(identity_simple_2, id_, "decline", data)
    result_dict = result.to_dict()

    RequestEvent.index.refresh()

    assert "declined" == result_dict["status"]
    results = request_events_service.search(identity_simple, id_)
    assert 2 == results.total  # submit comment + decline
    hits = list(results.hits)
    assert 1 == len([h for h in hits if RequestEventType.DECLINED.value == h["type"]])
