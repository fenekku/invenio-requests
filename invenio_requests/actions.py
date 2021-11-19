# -*- coding: utf-8 -*-
#
# Copyright (C) 2021 TU Wien.
# Copyright (C) 2021 Northwestern University.
#
# Invenio-Requests is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""RequestActions define code to be executed when performing actions on requests."""


from invenio_access.permissions import system_process
from invenio_db import db

from .errors import CannotExecuteActionError, NoSuchActionError
from .proxies import current_requests
from .records.api import RequestEventFormat, RequestEventType


class RequestActions:
    """Namespace for RequestActions static calls."""

    @classmethod
    def get_action(cls, request, action_name):
        """Get the action registered under the given name.

        :param action_name: The registered name of the action.
        :return: The action registered under the given name.
        """
        try:
            return request.request_type.available_actions[action_name](request)
        except KeyError:
            raise NoSuchActionError(action=action_name)

    @classmethod
    def can_execute(cls, identity, request, action_name, data=None):
        """Check wether identity and request can execute action.

        Perhaps data is sometimes useful for that check, so also included.
        """
        return cls.get_action(request, action_name).can_execute(identity, data)

    @classmethod
    def execute(cls, identity, request, action_name, data=None):
        """Have identity execute on request the action with the data."""
        return cls.get_action(request, action_name).execute(identity, data)


class RequestAction:
    """Base class for actions on requests."""

    def __init__(self, request):
        """Constructor."""
        self.request = request

    def _commit(self):
        """Persist changes."""
        self.request.commit()
        db.session.commit()
        requests_service = current_requests.requests_service
        if requests_service.indexer:
            requests_service.indexer.index(self.request)

    def can_execute(self, identity, data=None):
        """Check whether the action can be executed.

        This is mostly intended to be a hook for checking prerequisites
        (think, for instance, CI/CD pipeline runs).
        :param identity: The identity of the executor.
        :return: True if the action can be executed, False otherwise.
        """
        return True

    def execute(self, identity, data=None):
        """Execute the request action.

        :param identity: The identity of the executor.
        :param data: The passed input to the action.
        """
        # probably want to do something with self.request.topic
        if not self.can_execute(identity):
            action_name = type(self).__name__
            raise CannotExecuteActionError(action_name)

    def post_execute(self, identity):
        """Post-run hook that is run after the action has completed successfully.

        This hook should only be executed when the general workflow of the action
        has completed successfully.
        As such, it can be used to index records, for instance.
        """
        pass


class SubmitAction(RequestAction):
    """Submit a request."""

    def can_execute(self, identity, data=None):
        """Check whether the action can be executed."""
        return self.request.status == "draft"

    def execute(self, identity, data=None):
        """Execute the request action."""
        self.request.status = "open"

        request_id = self.request.number

        # Persist request changes
        self._commit()

        events_service = current_requests.request_events_service
        events_service.create(
            identity,
            request_id,
            {
                **data,
                "type": RequestEventType.COMMENT.value,
            }
        )


class AcceptAction(RequestAction):
    """Decline a request."""

    def can_execute(self, identity, data=None):
        """Check whether the action can be executed."""
        return self.request.status == "open"

    def execute(self, identity, data=None):
        """Execute the request action."""
        self.request.status = "accepted"

        request_id = self.request.number

        # Persist request changes
        self._commit()

        events_service = current_requests.request_events_service
        events_service.create(
            identity,
            request_id,
            {
                **data,
                "type": RequestEventType.ACCEPTED.value,
            }
        )


class DeclineAction(RequestAction):
    """Decline a request."""

    def can_execute(self, identity, data=None):
        """Check whether the action can be executed."""
        return self.request.status == "open"

    def execute(self, identity, data=None):
        """Execute the request action."""
        self.request.status = "declined"

        request_id = self.request.number

        # Persist request changes
        self._commit()

        events_service = current_requests.request_events_service
        events_service.create(
            identity,
            request_id,
            {
                **data,
                "type": RequestEventType.DECLINED.value,
            }
        )


class CancelAction(RequestAction):
    """Cancel a request."""

    def can_execute(self, identity, data=None):
        """Check whether the action can be executed."""
        return self.request.status == "open"

    def execute(self, identity, data=None):
        """Execute the request action."""
        self.request.status = "cancelled"

        request_id = self.request.number

        # Persist request changes
        self._commit()

        events_service = current_requests.request_events_service
        events_service.create(
            identity,
            request_id,
            {
                **data,
                "type": RequestEventType.CANCELLED.value,
            }
        )


class ExpireAction(RequestAction):
    """Expire a request."""

    def can_execute(self, identity, data=None):
        """Check whether the action can be executed."""
        is_system_process = system_process in identity.provides
        return self.request.is_open and is_system_process

    def execute(self, identity, data=None):
        """Execute the request action."""
        self.request.status = "expired"
