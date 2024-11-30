from django.contrib.auth.models import AbstractBaseUser
from django.utils.translation import gettext_lazy as _
from wagtail.contrib.modeladmin.helpers import (
    AdminURLHelper,
    ButtonHelper,
    PermissionHelper,
)


class MessageButtonHelper(ButtonHelper):
    def edit_button(self, *args, **kwargs):
        button = super().edit_button(*args, **kwargs)
        button.update({"label": _("View Message"), "title": _("View Message")})
        return button
