# -*- coding: utf-8 -*-
#
# Copyright (C) 2021 CERN.
# Copyright (C) 2021 Northwestern University.
# Copyright (C) 2021 TU Wien.
#
# Invenio-Requests is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Request permissions."""

from elasticsearch_dsl import Q
from invenio_access.permissions import any_user
from invenio_records_permissions import RecordPermissionPolicy
from invenio_records_permissions.generators import AnyUser, Generator, SystemProcess


class RequestCheckGenerator(Generator):
    """Generator with support for a request check function."""

    def __init__(self, check=None):
        """Constructor."""
        super().__init__()
        self._request_check_fn = check

    def _check_request(self, request):
        """Perform request check if such a function is defined."""
        if request is None:
            return False

        if self._request_check_fn is not None:
            return self._request_check_fn(request)

        return True


class Creator(RequestCheckGenerator):
    """Allows request makers."""

    def needs(self, request=None, **kwargs):
        """Enabling Needs.

        record is a request here
        """
        if request is None:
            return []

        if self._check_request(request):
            creator = request.created_by
            if creator is not None and creator.get_need() is not None:
                return [creator.get_need()]

        return []

    def query_filter(self, identity=None, **kwargs):
        """Filters for current identity as owner."""
        # TODO when request is more fleshed out
        return Q("match_all")


class Receiver(RequestCheckGenerator):
    """Allows request Receiver."""

    def needs(self, request=None, **kwargs):
        """Enabling Needs.

        record is a request here
        """
        if request is None:
            return []

        if self._check_request(request):
            need = request.receiver.get_need()
            if need is not None:
                return [need]

        return []

    def query_filter(self, identity=None, **kwargs):
        """Filters for current identity as owner."""
        # TODO when request is more fleshed out
        return []


def is_open(request):
    """Check if the request is open."""
    return request.is_open


def is_not_open(request):
    """Check if the request is closed or a draft."""
    return not request.is_open


def is_closed(request):
    """Check if the request is closed."""
    return request.is_closed


def is_not_closed(request):
    """Check if the request is open or a draft."""
    return not request.is_closed


def is_draft(request):
    """Check if the request is a draft (neither open nor closed)."""
    return not request.is_open and not request.is_closed


def is_no_draft(request):
    """Check if the request is not a draft (either open or closed)."""
    return request.is_open or request.is_closed


class Commenter(Generator):
    """Allows request event commenter."""

    def needs(self, event=None, **kwargs):
        """Enabling Needs."""
        return [event.created_by.get_need()]

        # TODO: events also need this kind of structure
        if event is None:
            return []

        creator = event.created_by
        if creator is not None and creator.get_need() is not None:
            return [creator.get_need()]

        return []

    def query_filter(self, identity=None, **kwargs):
        """Filters for current identity as creator."""
        users = [n.value for n in identity.provides if n.method == "id"]
        if users:
            return Q("terms", **{"created_by.user": users})


class PermissionPolicy(RecordPermissionPolicy):
    """Permission policy."""

    # TODO:
    # - require: authenticated user,
    # - require: if receiver is community AND community restricted:
    #   community <id> member (delegate to entity?)
    can_create = [AnyUser(), SystemProcess()]

    # - require: authenticated user
    can_search = [AnyUser(), SystemProcess()]
    # - require: user is creator or receiver
    can_read = [Creator(), Receiver(check=is_no_draft), SystemProcess()]
    # - require: user is creator or receiver
    can_update = [Creator(check=is_not_closed), SystemProcess()]
    # - require: admins only?
    can_delete = [Creator(check=is_not_open), SystemProcess()]

    # Actions: Submit/Cancel/Accept/Decline/Expire
    can_action_submit = [Creator(check=is_draft), SystemProcess()]
    can_action_cancel = [Creator(check=is_open), SystemProcess()]
    can_action_accept = [Receiver(check=is_open), SystemProcess()]
    can_action_decline = [Receiver(check=is_open), SystemProcess()]
    can_action_expire = [SystemProcess()]

    # Request Events: Comments
    can_create_comment = [Creator(), Receiver(check=is_no_draft), SystemProcess()]
    # TODO: test permission that commenter can update its own comment
    can_update_comment = [Commenter(), SystemProcess()]
    # TODO: test permission that commenter and receiver can delete comment
    can_delete_comment = [Commenter(), Receiver(), SystemProcess()]

    # Request Events: All other events
    can_create_event = [SystemProcess()]
    # TODO: test permission request creator and receiver can read an event
    can_read_event = [Creator(), Receiver(), SystemProcess()]
    can_update_event = [SystemProcess()]
    can_delete_event = [SystemProcess()]
    # TODO: creator and receiver can see the full timeline
    can_search_event = [Creator(), Receiver(), SystemProcess()]
