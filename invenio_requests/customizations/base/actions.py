# -*- coding: utf-8 -*-
#
# Copyright (C) 2021 CERN.
# Copyright (C) 2021 TU Wien.
#
# Invenio-Requests is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Base class for customizable actions on requests."""

from invenio_db import db

from ...errors import CannotExecuteActionError, NoSuchActionError
from ...proxies import current_requests


class RequestAction:
    """Base class for actions on requests."""

    def __init__(self, request):
        """Constructor."""
        self.request = request

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

    def _commit(self):
        """Persist changes."""
        self.request.commit()
        db.session.commit()
        requests_service = current_requests.requests_service
        if requests_service.indexer:
            requests_service.indexer.index(self.request)


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
