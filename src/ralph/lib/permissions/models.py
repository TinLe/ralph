# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from six import with_metaclass

from django.db import models
from django.db.models.base import ModelBase
from django.utils.translation import ugettext_lazy as _


def get_perm_key(action, class_name, field_name):
    """
    Generate django permission code name.

    :Example:

        >> perm = get_perm_key('change', 'baseobject', 'remarks')
        change_baseobject_remarks_field

    :param action: Permission action (change/view)
    :type action: str
    :param class_name: Django model class name
    :type class_name: str
    :param field_name: Django model field name
    :type field_name: str

    :return: django permission code name
    :rtype: str
    """
    return '{}_{}_{}_field'.format(action, class_name, field_name)


class PermissionByFieldBase(ModelBase):

    """
    Metaclass adding django permissions based on all fields in the model.

    :Example:

        class Test(with_metaclass(PermissionByFieldBase, models.Model)):

            ...

            class Permissions:
                # Fields to exclude generated permissions
                blacklist = set(['sample_field'])
    """

    def __new__(cls, name, bases, attrs):
        new_class = super(PermissionByFieldBase, cls).__new__(
            cls, name, bases, attrs
        )
        class_name = new_class._meta.model_name
        for field in new_class._meta.fields:
            blacklist = new_class.Permissions.blacklist
            name = field.name
            if not field.primary_key and name not in blacklist:
                new_class._meta.permissions.append((
                    get_perm_key('change', class_name, name),
                    _('Can change {} field').format(field.verbose_name)
                ))
                new_class._meta.permissions.append((
                    get_perm_key('view', class_name, name),
                    _('Can view {} field').format(field.verbose_name)
                ))

        return new_class


class PermByFieldMixin(with_metaclass(PermissionByFieldBase, models.Model)):

    """Django Abstract model class for permission by fields."""

    def has_access_to_field(self, field_name, user, action='change'):
        """
        Checks the user has the permission to the field

        :Example:

            >> user = User.objects.get(username='root')
            >> model.has_access_to_field('remarks', user, action='change')
            True

        :param field_name: django model field name
        :type field_name: str
        :param user: User object
        :type user: django User object
        :param action: permission action (change/view)
        :type action: str

        :return: True or False
        :rtype: bool
        """
        perm_key = get_perm_key(
            action,
            self._meta.model_name,
            field_name
        )
        return user.has_perm(
            '{}.{}'.format(self._meta.app_label, perm_key)
        )

    def allowed_fields(self, user, action='change'):
        """
        Returns a list with the names of the fields to which the user has permission

        :Example:

            >> user = User.objects.get(username='root')
            >> model.allowed_fields(user, 'change')
            ['parent', 'remarks', 'service_env']

        :param user: User object
        :type user: django User object
        :param action: permission action (change/view)
        :type action: str

        :return: List of field names
        :rtype: list
        """
        result = []
        blacklist = self.Permissions.blacklist
        for field in self._meta.fields:
            if (
                not field.primary_key and
                field.name not in blacklist and
                self.has_access_to_field(field.name, user, action)
            ):
                result.append(field.name)

        return result

    class Meta:
        abstract = True

