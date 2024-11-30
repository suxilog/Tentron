from django.contrib.auth import get_user_model
from django.db.models import Q
from django.urls import path, reverse
from django.utils.translation import gettext as _
from wagtail import hooks
from wagtail.admin.forms import WagtailAdminModelForm
from wagtail.admin.menu import MenuItem
from wagtail.admin.panels import ObjectList, extract_panel_definitions_from_model_class
from wagtail.contrib.modeladmin.helpers import ButtonHelper
from wagtail.contrib.modeladmin.options import (
    ModelAdmin,
    ModelAdminGroup,
    modeladmin_register,
)
from wagtail.contrib.modeladmin.views import CreateView

# from .forms import MessageForm
from .helpers import MessageButtonHelper
from .mixins import TentronAdminMixin
from .models import MessageRecipient, TentronMessageTask
from .views import MessageTaskIndexView, index


class ViewButtonHelper(ButtonHelper):
    def view_button(self, obj, classnames_add=None, classnames_exclude=None):
        if classnames_add is None:
            classnames_add = []
        if classnames_exclude is None:
            classnames_exclude = []

        classnames = self.finalise_classname(classnames_add, classnames_exclude)
        return {
            "url": reverse("message:message_log_detail", args=[obj.pk]),
            "label": "View",
            "classname": classnames,
            "title": "View this object",
        }

    def get_buttons_for_obj(
        self, obj, exclude=None, classnames_add=None, classnames_exclude=None
    ):
        btns = super().get_buttons_for_obj(
            obj, exclude, classnames_add, classnames_exclude
        )
        btns.append(
            self.view_button(
                obj,
                classnames_add=classnames_add,
                classnames_exclude=classnames_exclude,
            )
        )
        return btns


class TentronMessageTaskAdmin(TentronAdminMixin, ModelAdmin):
    model = TentronMessageTask
    menu_label = "Add"  # Django admin display name
    menu_icon = "doc-empty"  # Change as required
    menu_order = 230  # The position in the Wagtail admin menu
    add_to_settings_menu = False  # Whether to add your model to the settings sub-menu
    exclude_from_explorer = (
        False  # Whether to exclude your model from Wagtail's explorer menu
    )
    list_display = ("sender", "recipients", "sent_at")
    search_fields = ("content",)
    button_helper_class = MessageButtonHelper
    index_view_class = MessageTaskIndexView
    base_url_path = "message"

    def get_queryset(self, request):
        if request.user.is_superuser:
            return super().get_queryset(request)
        return super().get_queryset(request).filter(sender=request.user)


class MessageRecipientAdmin(ModelAdmin):
    model = MessageRecipient
    menu_label = "Message Log"  # Django admin display name
    menu_icon = "list-ul"  # Change as required
    list_display = ("recipient", "title", "sent_at", "read_at")
    button_helper_class = ViewButtonHelper
    menu_order = 240

    def get_list_display(self, request):
        list = super().get_list_display(request)
        if request.user.is_superuser:
            return list + ("sender",)
        return list

    def get_queryset(self, request):
        if request.user.is_superuser:
            return super().get_queryset(request)
        return (
            super()
            .get_queryset(request)
            .filter(Q(recipient=request.user) | Q(message__sender=request.user))
        )


class MessageAdminGroup(ModelAdminGroup):
    menu_label = _("Message")
    menu_icon = "mail"
    items = (TentronMessageTaskAdmin, MessageRecipientAdmin)
    menu_order = 220


modeladmin_register(MessageAdminGroup)
