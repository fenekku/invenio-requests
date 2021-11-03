# -*- coding: utf-8 -*-
#
# Copyright (C) 2021 TU Wien.
#
# Invenio-Requests is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Request type registry for looking up registered request types per name."""


class RequestTypeRegistry:
    """Registry for looking up registerd request types per name."""

    def __init__(self, registered_types):
        """Constructor."""
        self.registered_types = registered_types

    def register_type(self, request_class, as_type=None, force=False):
        """Register the specified request_class.

        :param request_class: The request class to register.
        :param as_type: Optional, the name under which to register the type.
                        If not specified, the request_type name from the
                        request_class will be taken.
        :param force: Override already registered type, if there is a
                      different type already registered with the same name.
        """
        type_ = as_type or request_class.request_type.value
        if force:
            self.registered_types[type_] = request_class
        else:
            self.registered_types.setdefault(type_, request_class)

    def lookup(self, type_name, quiet=False, default=None):
        """Look up a registered type by its name.

        :param type_name: The type name to look up.
        :param quiet: TODO
        :param default: The default value to return if no type is found and
                        quiet is set.
        :return: The type registered for the name.
        """
        if not quiet:
            return self.registered_types[type_name]

        return self.registered_types.get(type_name, default)
