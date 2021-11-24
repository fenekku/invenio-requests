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
from invenio_records_permissions.generators import (
    AnyUser,
    AuthenticatedUser,
    Generator,
    SystemProcess,
)


class Creator(Generator):
    """Allows request makers."""

    def needs(self, request=None, **kwargs):
        """Enabling Needs.

        record is a request here
        """
        # TODO when request is more fleshed out
        return [any_user]
        # return [
        #     UserNeed(owner.owner_id) for owner in record.access.owners
        # ]
        # even above could be optimized without caching by using raw ids

    def query_filter(self, identity=None, **kwargs):
        """Filters for current identity as owner."""
        # TODO when request is more fleshed out
        return Q('match_all')


class Receiver(Generator):
    """Allows request Receiver."""

    def needs(self, request=None, **kwargs):
        """Enabling Needs.

        record is a request here
        """
        # TODO when request is more fleshed out
        return [any_user]
        # return [
        #     UserNeed(owner.owner_id) for owner in record.access.owners
        # ]
        # even above could be optimized without caching by using raw ids

    def query_filter(self, identity=None, **kwargs):
        """Filters for current identity as owner."""
        # TODO when request is more fleshed out
        return []


class Commenter(Generator):
    """Allows request event commenter."""

    def needs(self, event=None, **kwargs):
        """Enabling Needs."""
        # TODO: postponed until we have a common owner/creator since it is
        #       used in multiple places
        return [any_user]
        # return [UserNeed(event.created_by.owner_id)] if event else []

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
    can_create = [SystemProcess(), AnyUser()]

    # - require: authenticated user
    can_search = [SystemProcess(), AnyUser()]
    # - require: user is creator or receiver
    can_read = [SystemProcess(), AnyUser()]
    # - require: user is creator or receiver
    can_update = [SystemProcess(), AnyUser()]
    # - require: admins only?
    can_delete = [SystemProcess(), AnyUser()]

    # Actions: Submit/Cancel/Accept/Decline/Expire
    can_submit = [Creator(), SystemProcess()]
    can_accept = [Receiver(), SystemProcess()]
    can_decline = [Receiver(), SystemProcess()]
    can_cancel = [Creator(), SystemProcess()]
    can_expire = [SystemProcess()]

    # Request Events: Comments
    can_create_comment = [Creator(), Receiver(), SystemProcess()]
    can_update_comment = [Commenter(), SystemProcess()]
    can_delete_comment = [Commenter(), Receiver(), SystemProcess()]

    # Request Events: All other events
    can_create_event = [AnyUser(), SystemProcess()]
    can_read_event = [Creator(), Receiver(), SystemProcess()]
    can_update_event = [SystemProcess()]
    can_delete_event = [SystemProcess()]
    can_search_event = [Creator(), Receiver(), SystemProcess()]
