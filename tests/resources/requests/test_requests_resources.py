# -*- coding: utf-8 -*-
#
# Copyright (C) 2021 TU Wien.
#
# Invenio-Requests is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Request resource tests."""

import copy


def check_reference_search_filter_results(response, expected_hits, expected_req_nums):
    """Check if all expected results are there."""
    hits = response.json["hits"]["hits"]
    reported_hits = int(response.json["hits"]["total"])
    req_numbers = [r["number"] for r in response.json["hits"]["hits"]]

    assert len(req_numbers) == len(expected_req_nums)
    for num in expected_req_nums:
        assert num in req_numbers

    assert reported_hits == len(hits) == expected_hits


def test_reference_search_filters(app, client_logged_as, headers, example_requests):
    """Test if the reference search filters (e.g. receiver=user:1) work as intended."""
    # use the admin with superuser-access to evade potential permission issues
    client = client_logged_as("admin@example.org")
    req1, req2, req3 = example_requests

    # get unfiltered responses
    response = client.get(
        "/requests/",
        headers=headers,
    )
    check_reference_search_filter_results(
        response, 3, [req1.number, req2.number, req3.number]
    )

    # get requests where user #1 is the receiver (should be the first two)
    response = client.get(
        "/requests/?receiver=user:1",
        headers=headers,
    )
    check_reference_search_filter_results(response, 2, [req1.number, req2.number])

    # get requests where user #2 is the receiver (should be the last one)
    response = client.get(
        "/requests/?receiver=user:2",
        headers=headers,
    )
    check_reference_search_filter_results(response, 1, [req3.number])

    # get requests where user #3 is the receiver (none)
    response = client.get(
        "/requests/?receiver=user:3",
        headers=headers,
    )
    check_reference_search_filter_results(response, 0, [])

    # check what happens when there's an invalid reference
    # (the filter should get dropped)
    response = client.get(
        "/requests/?receiver=nosuchthing:1",
        headers=headers,
    )
    check_reference_search_filter_results(
        response, 3, [req1.number, req2.number, req3.number]
    )


def test_empty_comment(
    app, client_logged_as, headers, example_requests, request_action_resource_data
):
    client = client_logged_as("user1@example.org")
    r1, r2, r3 = example_requests
    for r in [r1, r2, r3]:
        r.status = "open"
        r.commit()

    # Accept (valid for other actions too) no payload is Ok
    response = client.post(f"/requests/{r1.id}/actions/accept", headers=headers)
    assert 200 == response.status_code
    assert "accepted" == response.json["status"]

    # Accept {} is Ok
    response = client.post(
        f"/requests/{r2.id}/actions/accept", headers=headers, json={}
    )
    assert 200 == response.status_code
    assert "accepted" == response.json["status"]

    # Accept empty content is an error
    data = copy.deepcopy(request_action_resource_data)
    data["payload"]["content"] = ""
    response = client.post(
        f"/requests/{r3.id}/actions/accept", headers=headers, json=data
    )
    assert 400 == response.status_code

    response = client.get(f"/requests/{r3.id}", headers=headers)
    assert "open" == response.json["status"]
