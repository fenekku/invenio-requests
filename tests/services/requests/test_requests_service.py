# -*- coding: utf-8 -*-
#
# Copyright (C) 2021 CERN.
# Copyright (C) 2021 Northwestern University.
#
# Invenio-Requests is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Service tests."""

import pytest
from invenio_records_resources.services.errors import PermissionDeniedError

from invenio_requests.records.api import (
    RequestEvent,
    RequestEventFormat,
    RequestEventType,
)


def test_submit_request(app, identity_simple, submit_request, request_events_service):
    result = submit_request(identity_simple)
    id_ = result._request.id
    result_dict = result.to_dict()
    RequestEvent.index.refresh()

    assert "open" == result_dict["status"]
    results = request_events_service.search(identity_simple, id_)
    assert 1 == results.total
    hits = list(results.hits)
    assert RequestEventType.COMMENT.value == hits[0]["type"]
    assert "Can I belong to the community?" == hits[0]["payload"]["content"]


def test_accept_request(
    app,
    identity_simple,
    identity_simple_2,
    submit_request,
    requests_service,
    request_events_service,
):
    # Submit a request
    result = submit_request(identity_simple)
    id_ = result._request.id

    data = {
        "payload": {
            "content": "Welcome to the community!",
            "format": RequestEventFormat.HTML.value,
        }
    }

    # Other user accepts it with comment
    data = {
        "payload": {
            "content": "Welcome to the community!",
            "format": RequestEventFormat.HTML.value,
        }
    }
    result = requests_service.execute_action(identity_simple_2, id_, "accept", data)
    result_dict = result.to_dict()

    RequestEvent.index.refresh()

    assert "accepted" == result_dict["status"]
    results = request_events_service.search(identity_simple_2, id_)
    assert 3 == results.total  # submit comment + accept + comment
    hits = list(results.hits)
    assert 1 == len([h for h in hits if RequestEventType.ACCEPTED.value == h["type"]])


def test_cancel_request(
    app,
    identity_simple,
    identity_simple_2,
    submit_request,
    requests_service,
    request_events_service,
):
    # Submit a request
    result = submit_request(identity_simple)
    id_ = result._request.id

    data = {
        "payload": {
            "content": "",  # no comment is fine
            "format": RequestEventFormat.HTML.value,
        }
    }

    # Cancel it  (no comment is fine)
    result = requests_service.execute_action(identity_simple, id_, "cancel")
    result_dict = result.to_dict()

    RequestEvent.index.refresh()

    assert "cancelled" == result_dict["status"]
    results = request_events_service.search(identity_simple, id_)
    assert 2 == results.total  # submit comment + cancel
    hits = list(results.hits)
    assert 1 == len([h for h in hits if RequestEventType.CANCELLED.value == h["type"]])


def test_decline_request(
    app,
    identity_simple,
    identity_simple_2,
    submit_request,
    requests_service,
    request_events_service,
):
    # Submit a request
    result = submit_request(identity_simple)
    id_ = result._request.id

    data = {
        "payload": {"content": "Sorry but no.", "format": RequestEventFormat.HTML.value}
    }

    # Other user declines it
    result = requests_service.execute_action(identity_simple_2, id_, "decline", data)
    result_dict = result.to_dict()

    RequestEvent.index.refresh()

    assert "declined" == result_dict["status"]
    results = request_events_service.search(identity_simple, id_)
    assert 3 == results.total  # submit comment + decline + comment
    hits = list(results.hits)
    assert 1 == len([h for h in hits if RequestEventType.DECLINED.value == h["type"]])
