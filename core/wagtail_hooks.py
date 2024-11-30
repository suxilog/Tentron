import re
from unicodedata import category

from django.conf import settings
from django.contrib.admin.utils import (
    get_fields_from_path,
    label_for_field,
    lookup_field,
    prepare_lookup_value,
    quote,
    unquote,
)
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils.text import capfirst
from django.utils.translation import gettext as _
from django.utils.translation import gettext_lazy
from wagtail import hooks
from wagtail.admin.menu import MenuItem
from wagtail.contrib.modeladmin.helpers import ButtonHelper
from wagtail.contrib.modeladmin.options import (
    ModelAdmin,
    ModelAdminGroup,
    modeladmin_register,
)
from wagtail.contrib.modeladmin.views import CreateView, EditView, IndexView
from wagtail.log_actions import log
from wagtail.models import Locale, RevisionMixin, Site, TranslatableMixin

from organization.utils import CommonPagePermissionHelper, CommonPermissionHelper

from .models import (
    Attribute,
    AttributeValue,
    BlogCategory,
    BlogDetailPage,
    BlogTag,
    FaqCategory,
    FaqItem,
    FaqPage,
    ProductPage,
    ProductType,
    SingleProductPage,
    TestimonialItem,
    VariantProductPage,
)
from .views import FaqPageIndexView


class TentronCreateView(CreateView):
    # def get_initial(self):
    #     initial = super().get_initial()
    #     # get current site
    #     current_site = Site.find_for_request(self.request)
    #     # update initial site with current site
    #     initial.update({"site": current_site.pk})
    #     return initial

    # def get_form_kwargs(self):
    #     kwargs = super().get_form_kwargs()
    #     # get current site
    #     current_site = Site.find_for_request(self.request)
    #     # update querydict site in kwargs data with current site
    #     try:
    #         kwargs["data"] = kwargs["data"].copy()
    #         # if kwargs['data'] has site key, use is as is
    #         if "site" in kwargs["data"]:
    #             pass
    #         else:
    #             kwargs["data"].update({"site": current_site.pk})
    #     except KeyError:
    #         pass
    #     if getattr(settings, "WAGTAIL_I18N_ENABLED", False) and issubclass(
    #         self.model, TranslatableMixin
    #     ):
    #         selected_locale = self.request.GET.get("locale")
    #         if selected_locale:
    #             kwargs["instance"].locale = get_object_or_404(
    #                 Locale, language_code=selected_locale
    #             )

    #     return kwargs
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

    # pass


class TentronEditView(EditView):
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


class FaqCategoryCreateView(TentronCreateView):
    pass


class FaqCategoryEditView(TentronEditView):
    pass


class FaqItemCreateView(TentronCreateView):
    pass


class FaqItemEditView(TentronEditView):
    pass


class FaqPageAdmin(ModelAdmin):
    model = FaqPage
    menu_label = "FAQ Page"
    menu_icon = "doc-full-inverse"
    menu_order = 228
    add_to_settings_menu = False
    exclude_from_explorer = False
    list_display = ("title", "site")
    index_view_class = FaqPageIndexView

    def get_queryset(self, request):
        request = request or self.request
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        site = Site.find_for_request(request)
        return qs.filter(site=site)


class FaqItemAdmin(ModelAdmin):
    model = FaqItem
    menu_label = "FAQ Item"
    menu_icon = "list-ul"
    menu_order = 229
    add_to_settings_menu = False
    exclude_from_explorer = False
    list_display = ("question", "get_categories")
    permission_helper_class = CommonPermissionHelper
    create_view_class = FaqItemCreateView
    edit_view_class = FaqItemEditView

    def get_queryset(self, request):
        request = request or self.request
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        site = Site.find_for_request(request)
        return qs.filter(site=site)


class FaqCategoryAdmin(ModelAdmin):
    model = FaqCategory
    menu_label = "FAQ Category"
    menu_icon = "clipboard-list"
    menu_order = 230
    add_to_settings_menu = False
    exclude_from_explorer = False
    list_display = ("name",)
    permission_helper_class = CommonPermissionHelper
    create_view_class = FaqCategoryCreateView
    edit_view_class = FaqCategoryEditView
    prepopulated_fields = {"slug": ("name",)}
    form_fields_exclude = ["site"]
    # index_view_class = FaqCategoryIndexView
    def get_queryset(self, request):
        request = request or self.request
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        site = Site.find_for_request(request)
        return qs.filter(site=site)

    def get_list_display(self, request):
        list = super().get_list_display(request)
        list += ("slug",)
        if request.user.is_superuser:
            return list + ("site",)
        return list


class FaqAdminGroup(ModelAdminGroup):
    menu_label = "FAQ"
    menu_icon = "help"
    items = (FaqPageAdmin, FaqItemAdmin, FaqCategoryAdmin)
    menu_order = 202


modeladmin_register(FaqAdminGroup)
## Blog Admin
class BlogAdmin(ModelAdmin):
    model = BlogDetailPage
    menu_label = _("Blog")
    menu_icon = "doc-empty-inverse"
    menu_order = 231
    add_to_settings_menu = False
    exclude_from_explorer = False
    list_display = ("title",)
    permission_helper_class = CommonPagePermissionHelper
    create_view_class = TentronCreateView
    edit_view_class = TentronEditView

    def get_queryset(self, request):
        request = request or self.request
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        site = Site.find_for_request(request)
        return qs.filter(site=site)

    def get_list_display(self, request):
        list = super().get_list_display(request)
        if request.user.is_superuser:
            return list + ("site",)
        return list


class BlogCategoryAdmin(ModelAdmin):
    model = BlogCategory
    menu_label = _("Blog Category")
    menu_icon = "clipboard-list"
    menu_order = 232
    add_to_settings_menu = False
    exclude_from_explorer = False
    list_display = ("name",)
    permission_helper_class = CommonPermissionHelper
    create_view_class = TentronCreateView
    edit_view_class = TentronEditView
    prepopulated_fields = {"slug": ("name",)}

    def get_queryset(self, request):
        request = request or self.request
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        site = Site.find_for_request(request)
        return qs.filter(site=site)


class BlogTagAdmin(ModelAdmin):
    model = BlogTag
    menu_label = _("Blog Tag")
    menu_icon = "tag"
    menu_order = 233
    add_to_settings_menu = False
    exclude_from_explorer = False
    list_display = ("name",)
    permission_helper_class = CommonPermissionHelper
    create_view_class = TentronCreateView
    edit_view_class = TentronEditView
    prepopulated_fields = {"slug": ("name",)}

    def get_queryset(self, request):
        request = request or self.request
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        site = Site.find_for_request(request)
        return qs.filter(site=site)


class BlogAdminGroup(ModelAdminGroup):
    menu_label = _("Blog")
    menu_icon = "doc-full"
    items = (BlogAdmin, BlogTagAdmin, BlogCategoryAdmin)
    menu_order = 201


modeladmin_register(BlogAdminGroup)
## Testimonial item Admin
class TestimonialItemAdmin(ModelAdmin):
    model = TestimonialItem
    menu_label = _("Testimonial")
    menu_icon = "user"
    menu_order = 229
    add_to_settings_menu = False
    exclude_from_explorer = False
    list_display = ("name", "image", "company")
    permission_helper_class = CommonPermissionHelper
    create_view_class = TentronCreateView
    edit_view_class = TentronEditView

    def get_queryset(self, request):
        request = request or self.request
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        site = Site.find_for_request(request)
        return qs.filter(site=site)


modeladmin_register(TestimonialItemAdmin)
## Product Admin
class ProductAdmin(ModelAdmin):
    model = ProductPage
    menu_label = _("All")
    menu_icon = "list-ul"
    menu_order = 229
    add_to_settings_menu = False
    exclude_from_explorer = False
    list_display = ("title", "slug")
    permission_helper_class = CommonPagePermissionHelper
    create_view_class = TentronCreateView
    edit_view_class = TentronEditView

    def get_queryset(self, request):
        request = request or self.request
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        site = Site.find_for_request(request)
        return qs.filter(site=site)

    def get_list_display(self, request):
        list = super().get_list_display(request)
        if request.user.is_superuser:
            return list + ("site",)
        return list


class SingleProductAdmin(ModelAdmin):
    model = SingleProductPage
    menu_label = _("Single products")
    menu_icon = "doc-full-inverse"
    menu_order = 230
    add_to_settings_menu = False
    exclude_from_explorer = False
    list_display = ("title", "slug")
    permission_helper_class = CommonPagePermissionHelper
    create_view_class = TentronCreateView
    edit_view_class = TentronEditView

    def get_queryset(self, request):
        request = request or self.request
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        site = Site.find_for_request(request)
        return qs.filter(site=site)

    def get_list_display(self, request):
        list = super().get_list_display(request)
        if request.user.is_superuser:
            return list + ("site",)
        return list


class VariantProductAdmin(ModelAdmin):
    model = VariantProductPage
    menu_label = _("Variant products")
    menu_icon = "copy"
    menu_order = 231
    add_to_settings_menu = False
    exclude_from_explorer = False
    list_display = ("title", "slug")
    permission_helper_class = CommonPagePermissionHelper
    create_view_class = TentronCreateView
    edit_view_class = TentronEditView

    def get_queryset(self, request):
        request = request or self.request
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        site = Site.find_for_request(request)
        return qs.filter(site=site)

    def get_list_display(self, request):
        list = super().get_list_display(request)
        if request.user.is_superuser:
            return list + ("site",)
        return list


class ProductTypeAdmin(ModelAdmin):
    model = ProductType
    menu_label = "Category"
    menu_icon = "clipboard-list"
    menu_order = 232
    add_to_settings_menu = False
    exclude_from_explorer = False
    list_display = ("name", "parent")
    permission_helper_class = CommonPermissionHelper
    prepopulated_fields = {"slug": ("name",)}
    # index_view_class = FaqCategoryIndexView
    create_view_class = TentronCreateView
    edit_view_class = TentronEditView

    def get_queryset(self, request):
        request = request or self.request
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        site = Site.find_for_request(request)
        return qs.filter(site=site)

    def get_list_display(self, request):
        list = super().get_list_display(request)
        list += ("slug",)
        if request.user.is_superuser:
            return list + ("site",)
        return list


class AttributeAdmin(ModelAdmin):
    model = Attribute
    menu_label = "Attribute"
    menu_icon = "list-ul"
    menu_order = 233
    add_to_settings_menu = False
    exclude_from_explorer = False
    list_display = ("name", "slug", "type")
    permission_helper_class = CommonPermissionHelper
    prepopulated_fields = {"slug": ("name",)}
    create_view_class = TentronCreateView
    edit_view_class = TentronEditView

    def get_queryset(self, request):
        request = request or self.request
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        site = Site.find_for_request(request)
        return qs.filter(site=site)

    def get_list_display(self, request):
        list = super().get_list_display(request)
        list += ("slug",)
        if request.user.is_superuser:
            return list + ("site",)
        return list


class AttributeValueAdmin(ModelAdmin):
    model = AttributeValue
    menu_label = "Attribute Value"
    menu_icon = "list-ol"
    menu_order = 234
    add_to_settings_menu = False
    exclude_from_explorer = False
    list_display = ("value",)
    search_fields = ("value",)
    permission_helper_class = CommonPermissionHelper
    # index_view_class = FaqCategoryIndexView
    create_view_class = TentronCreateView
    edit_view_class = TentronEditView

    def get_queryset(self, request):
        request = request or self.request
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        site = Site.find_for_request(request)
        return qs.filter(site=site)

    def get_list_display(self, request):
        list = super().get_list_display(request)
        if request.user.is_superuser:
            return list + ("site",)
        return list


class ProductAdminGroup(ModelAdminGroup):
    menu_label = "Products"
    menu_icon = "tasks"
    items = (
        ProductAdmin,
        SingleProductAdmin,
        VariantProductAdmin,
        ProductTypeAdmin,
        AttributeAdmin,
        AttributeValueAdmin,
    )
    menu_order = 200


modeladmin_register(ProductAdminGroup)
