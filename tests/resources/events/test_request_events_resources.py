# -*- coding: utf-8 -*-
#
# Copyright (C) 2021 CERN.
# Copyright (C) 2021 Northwestern University.
#
# Invenio-Requests is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Resource tests."""

import copy

from invenio_requests.records.api import RequestEvent, RequestEventType


def assert_api_response_json(expected_json, received_json):
    """Assert the REST API response's json."""
    # We don't compare dynamic times at this point
    received_json.pop("created")
    received_json.pop("updated")
    assert expected_json == received_json


def assert_api_response(response, code, json):
    """Assert the REST API response."""
    assert code == response.status_code
    assert_api_response_json(json, response.json)


def test_simple_comment_flow(
    app, client_logged_as, headers, events_resource_data, example_request
):
    client = client_logged_as("user1@example.org")
    request_id = example_request.id

    # User 1 comments
    response = client.post(
        f"/requests/{request_id}/comments",
        headers=headers,
        json=events_resource_data
    )

    comment_id = response.json["id"]
    expected_json_1 = {
        **events_resource_data,
        "id": comment_id,
        "links": {
            "self": f"https://127.0.0.1:5000/api/requests/{request_id}/comments/{comment_id}",  # noqa
            # "self_html": "",  # TODO: UI link
            # "report": ""  # TODO
        },
        "revision_id": 1,
        "type": RequestEventType.COMMENT.value,
    }
    assert_api_response(response, 201, expected_json_1)

    # User 1 reads comment
    response = client.get(
        f"/requests/{request_id}/comments/{comment_id}",
        headers=headers,
    )

    assert_api_response(response, 200, expected_json_1)

    # User 2 comments
    client = client_logged_as("user2@example.org")
    response = client.post(
        f"/requests/{request_id}/comments",
        headers=headers,
        json=events_resource_data
    )
    comment_id = response.json["id"]
    revision_id = response.json["revision_id"]

    # User 2 updates comments
    data = copy.deepcopy(events_resource_data)
    data["payload"]["content"] = "I've revised my comment."
    revision_headers = copy.deepcopy(headers)
    revision_headers["if_match"] = revision_id
    response = client.put(
        f"/requests/{request_id}/comments/{comment_id}",
        headers=revision_headers,
        json=data,
    )
    expected_json_2 = {
        **data,
        "id": comment_id,
        "links": {
            "self": f"https://127.0.0.1:5000/api/requests/{request_id}/comments/{comment_id}",  # noqa
            # "self_html": "",  # TODO: UI link
            # "report": ""  # TODO
        },
        "revision_id": 2,
        "type": RequestEventType.COMMENT.value,
    }
    assert_api_response(response, 200, expected_json_2)

    # User 2 deletes comments
    revision_headers["if_match"] = 2
    response = client.delete(
        f"/requests/{request_id}/comments/{comment_id}",
        headers=revision_headers,
    )
    assert 204 == response.status_code
    assert b"" == response.data

    RequestEvent.index.refresh()

    # User 2 gets the timeline (will be sorted)
    response = client.get(
        f"/requests/{request_id}/timeline",
        headers=headers
    )
    assert 200 == response.status_code
    assert 2 == response.json["hits"]["total"]
    assert_api_response_json(expected_json_1, response.json["hits"]["hits"][0])
    expected_json_3 = {
        "id": comment_id,
        "links": {
            "self": f"https://127.0.0.1:5000/api/requests/{request_id}/comments/{comment_id}",  # noqa
        },
        "revision_id": 4,
        "type": RequestEventType.REMOVED.value,
    }
    assert_api_response_json(expected_json_3, response.json["hits"]["hits"][1])


def test_timeline_links(
        client_logged_as, events_resource_data, example_request, headers):
    """Tests the links for the timeline (search) endpoint."""
    client = client_logged_as("user1@example.org")
    request_id = example_request.id
    response = client.post(
        f"/requests/{request_id}/comments",
        headers=headers,
        json=events_resource_data
    )

    response = client.get(f"/requests/{request_id}/timeline", headers=headers)
    search_record_links = response.json["links"]

    expected_links = {
        # NOTE: Variations are covered in records-resources
        "self": f"https://127.0.0.1:5000/api/requests/{request_id}/timeline?page=1&size=25&sort=oldest"  # noqa
    }
    assert expected_links == search_record_links
