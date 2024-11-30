from django.contrib.auth import get_permission_codename
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.utils.functional import cached_property
from wagtail import hooks
from wagtail.contrib.modeladmin.options import (
    ModelAdmin,
    ModelAdminGroup,
    modeladmin_register,
)
from wagtail.models import Page, Site, UserPagePermissionsProxy

# from .views import (
#     MainMenuEditView,
#     OrganizationMainMenuCreateView,
#     OrganizationMainMenuIndexView,
# )
from wagtailmenus.views import (
    FlatMenuCreateView,
    FlatMenuEditView,
    MainMenuEditView,
    MainMenuIndexView,
)

from organization.models import (
    BasePage,
    ExtendedSite,
    FooterMenu,
    Organization,
    OrganizationRootPage,
)
from organization.utils import OrganizationPermissionHelper

from .models import (
    OrganizationFlatMenu,
    OrganizationFlatMenuItem,
    OrganizationMainMenu,
    OrganizationMainMenuItem,
)
from .views import FooterMenuIndexView


class OrganizationMainMenuIndex(MainMenuIndexView):
    def get_queryset(self):

        return OrganizationMainMenu.objects.filter(
            site=Site.find_for_request(self.request)
        )


class OrganizationMainMenuEdit(MainMenuEditView):
    def get_queryset(self):
        return OrganizationMainMenu.objects.filter(
            site=Site.find_for_request(self.request)
        )


class OrganizationFlatMenuCreateView(FlatMenuCreateView):
    def form_valid(self, form):
        # get current site
        # check if form has site field, if yes, use it as is
        if "site" in form.data:
            return super().form_valid(form)

        current_site = Site.find_for_request(self.request)
        # set the site on the form's instance
        form.instance.site = current_site
        # continue with super's form_valid
        return super().form_valid(form)

    def get_queryset(self):
        return OrganizationFlatMenu.objects.filter(
            site=Site.find_for_request(self.request)
        )


class OrganizationFlatMenuEditView(FlatMenuEditView):
    def form_valid(self, form):
        # check if form has site field, if yes, use it as is
        if "site" in form.data:
            return super().form_valid(form)
        # Get the current site
        site = Site.find_for_request(self.request)

        # Create the object but don't save it yet
        self.instance = form.save(commit=False)

        # Set the site
        self.instance.site = site

        # Now save the object
        self.instance.save()

        return super().form_valid(form)

    def get_queryset(self):
        return OrganizationFlatMenu.objects.filter(
            site=Site.find_for_request(self.request)
        )


class OrganizationMainMenuAdmin(ModelAdmin):
    model = OrganizationMainMenu
    menu_label = "Header Menu"
    menu_icon = "list-ul"
    permission_helper_class = OrganizationPermissionHelper
    index_view_class = OrganizationMainMenuIndex
    edit_view_class = MainMenuEditView
    menu_order = 210

    def get_queryset(self, request):
        request = request or self.request
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        site = Site.find_for_request(request)
        return qs.filter(site=site)


class OrganizationFooterMenuAdmin(ModelAdmin):
    model = FooterMenu
    menu_label = "Footer Menu"
    menu_icon = "list-ul"
    permission_helper_class = OrganizationPermissionHelper
    index_view_class = FooterMenuIndexView
    # edit_view_class = OrganizationFlatMenuEditView
    # create_view_class = OrganizationFlatMenuCreateView

    def get_queryset(self, request):
        request = request or self.request
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        site = Site.find_for_request(request)
        return qs.filter(site=site)


class OrganizationFlatMenuAdmin(ModelAdmin):
    model = OrganizationFlatMenu
    menu_label = "Footer Menu Items"
    menu_icon = "list-ul"
    permission_helper_class = OrganizationPermissionHelper
    edit_view_class = OrganizationFlatMenuEditView
    create_view_class = OrganizationFlatMenuCreateView

    def get_queryset(self, request):
        request = request or self.request
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        site = Site.find_for_request(request)
        return qs.filter(site=site)


class OrganizationMenuAdminGroup(ModelAdminGroup):
    menu_label = "Menus"
    menu_icon = "folder-open-inverse"
    items = (
        OrganizationMainMenuAdmin,
        OrganizationFooterMenuAdmin,
        OrganizationFlatMenuAdmin,
    )
    menu_order = 220


modeladmin_register(OrganizationMenuAdminGroup)
