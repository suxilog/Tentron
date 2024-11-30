# organizations/wagtail_hooks.py

from socket import SO_BROADCAST

from django.contrib.auth.models import Permission
from django.db.models import Q
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from wagtail import hooks
from wagtail.admin.menu import MenuItem
from wagtail.contrib.modeladmin.options import ModelAdmin, modeladmin_register
from wagtail.models import Site

from organization.models import OrganizationRootPage

from .models import ExtendedSite, Organization, SiteSettings
from .utils import CommonPermissionHelper, ExtendedSitePermissionHelper
from .views import SiteSettingsIndexView


class SiteSettingsAdmin(ModelAdmin):
    model = SiteSettings
    menu_label = _("Site settings")
    menu_icon = "site"
    menu_order = 299
    add_to_settings_menu = False
    exclude_from_explorer = True
    list_display = ("site_name",)
    permission_helper_class = CommonPermissionHelper
    index_view_class = SiteSettingsIndexView
    # edit_template_name = "organization/site_settings/edit.html"

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs

        return qs.filter(site=Site.find_for_request(request))


modeladmin_register(SiteSettingsAdmin)


@hooks.register("construct_settings_menu")
def hide_site_settings_menu_item_from_setting(request, menu_items):
    if request.user.is_superuser:
        return menu_items
    menu_items[:] = [
        item
        for item in menu_items
        if item.name not in ["site-setting", "footer-menu", "main-menu", "flat-menus"]
    ]


@hooks.register("construct_reports_menu")
def hide_site_history_menu_item_from_non_superuser(request, menu_items):
    if not request.user.is_superuser:
        menu_items[:] = [
            item
            for item in menu_items
            if item.name
            not in [
                "locked-pages",
                "site-history",
                "aging-pages",
                "workflows",
                "workflow-tasks",
            ]
        ]


class OrganizationAdmin(ModelAdmin):
    model = Organization
    menu_label = "Organizations"
    menu_icon = "group"
    menu_order = 298
    add_to_settings_menu = False
    exclude_from_explorer = False
    list_display = ("name",)


modeladmin_register(OrganizationAdmin)


@hooks.register("construct_page_chooser_queryset")
def show_my_pages_only(pages, request):
    # Only show own pages
    if request.user.is_superuser:
        return pages
    site = Site.find_for_request(request)
    organization_root_page = OrganizationRootPage.objects.get(site=site)
    pages = organization_root_page.get_descendants().defer_streamfields()
    return pages


@hooks.register("construct_document_chooser_queryset")
def show_my_uploaded_documents_only(documents, request):
    # Only show uploaded documents
    documents = documents.filter(uploaded_by_user=request.user)

    return documents


@hooks.register("construct_image_chooser_queryset")
def show_my_uploaded_images_only(images, request):
    # Only show uploaded images
    images = images.filter(uploaded_by_user=request.user)

    return images


from wagtailmodelchooser import Chooser, register_model_chooser


@register_model_chooser
class ThemeChooser(Chooser):
    from theme.models import Theme

    model = Theme
    model_template = "wagtailmodelchooser/modal.html"
    modal_results_template = "wagtailmodelchooser/results.html"

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(Q(user=request.user) | Q(is_common=True))
