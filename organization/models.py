# organizations/models.py
import logging
import os
import re
import socket
import time
import uuid
from cProfile import run

from celery import chain
from django.apps import apps
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import Group, Permission
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import models, transaction
from django.utils import timezone
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _
from modelcluster.fields import ParentalKey
from modelcluster.models import ClusterableModel
from wagtail import blocks
from wagtail.admin.panels import FieldPanel, InlinePanel, ObjectList, TabbedInterface
from wagtail.contrib.settings.models import (
    BaseGenericSetting,
    BaseSiteSetting,
    register_setting,
)
from wagtail.fields import StreamField
from wagtail.images.blocks import ImageChooserBlock
from wagtail.models import GroupPagePermission, Orderable, Page, Site
from wagtail.models.collections import Collection, GroupCollectionPermission
from wagtail.rich_text import RichText
from wagtailmenus.models import MenuPage
from wagtailmodelchooser import Chooser, register_model_chooser
from wagtailmodelchooser.blocks import ModelChooserBlock

from .tasks import run_command_in_container

# from theme.models import Theme


logger = logging.getLogger("tentron")
TEMPLATE_FOLDER_CHOICES = (
    ("default", "Default"),
    ("site1", "Site 1"),
    ("capatel", "Capatel"),
)


class SiteSettingsTheme(Orderable):
    site_settings = ParentalKey(
        "organization.SiteSettings",
        on_delete=models.CASCADE,
        related_name="site_settings_theme",
    )
    theme = models.ForeignKey(
        "theme.Theme", on_delete=models.CASCADE, related_name="theme_site_settings"
    )

    panels = [
        FieldPanel("theme"),
    ]

    @property
    def template_folder(self):
        return self.theme.slug

    class Meta:
        verbose_name = _("Site Settings Theme")
        verbose_name_plural = _("Site Settings Themes")


@register_setting
class SiteSettings(ClusterableModel, BaseSiteSetting):
    # Basic Settings
    site_name = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text=_("The name of the site."),
    )
    site_description = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text=_("The description of the site."),
    )
    site_logo = models.ForeignKey(
        "wagtailimages.Image",
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name="+",
        help_text=_("The logo of the site."),
    )
    site_favorite_icon = models.ForeignKey(
        "wagtailimages.Image",
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name="+",
        help_text=_("The favorite icon of the site."),
    )

    copy_right = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text=_("The copy right of the site."),
    )
    inquiry_mode = models.BooleanField(
        default=True,
        help_text=_("Inquiry Mode, if True, the add to cart button will be hidden."),
    )

    # Tracking and Analytics Settings
    google_analytics = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text=_("The Google Analytics ID of the site."),
    )
    google_tag_manager_id = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text=_("The Google Tag Manager ID of the site, only GTM-XXXXXX."),
    )
    facebook_pixel = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text=_("The Facebook Pixel ID of the site."),
    )

    # Security Settings
    google_recaptcha_site_key = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text=_("The Google reCAPTCHA site key of the site."),
    )
    google_recaptcha_secret_key = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text=_("The Google reCAPTCHA secret key of the site."),
    )

    # SEO Settings
    default_meta_title = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text=_("The default meta title of the site."),
    )
    default_meta_description = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text=_("The default meta description of the site."),
    )
    default_meta_keywords = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text=_("The default meta keywords of the site."),
    )
    default_social_image = models.ForeignKey(
        "wagtailimages.Image",
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name="+",
        help_text=_("The default social image of the site."),
    )

    sitemap_active = models.BooleanField(
        default=False, help_text=_("Check to enable sitemap")
    )
    robots_txt = models.TextField(
        blank=True,
        null=True,
        default="User-agent: *\nDisallow: /",
        help_text=_("The robots.txt of the site. Default is disallow all."),
    )

    # External Scripts and Styles
    custom_js = models.TextField(
        blank=True,
        null=True,
        help_text=_("The custom JavaScript of the site. without <script> tag."),
    )
    custom_css = models.TextField(
        blank=True,
        null=True,
        help_text=_("The custom CSS of the site. without <style> tag."),
    )

    # Third Party Integrations
    google_maps_api_key = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text=_("The Google Maps API key of the site."),
    )

    # Contact and social media
    contact_email = models.EmailField(
        blank=True,
        null=True,
        help_text=_("The fixed contact email of the site."),
    )
    contact_phone = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text=_("The fixed contact phone of the site."),
    )
    contact_address = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text=_("The fixed contact address of the site."),
    )

    contact_content = StreamField(
        [
            (
                "contact_content",
                blocks.StructBlock(
                    [
                        (
                            "icon",
                            blocks.CharBlock(required=False, default="fa fa-envelope"),
                        ),
                        ("image", ImageChooserBlock(required=False)),
                        ("title", blocks.CharBlock(required=True)),
                        ("description", blocks.RichTextBlock(required=False)),
                    ]
                ),
            ),
        ],
        blank=True,
        null=True,
        help_text=_("The contact content of the site."),
        use_json_field=True,
    )
    social_media = StreamField(
        [
            (
                "social_media",
                blocks.StructBlock(
                    [
                        (
                            "icon",
                            blocks.CharBlock(
                                required=False,
                                default="fa fa-envelope",
                                help_text=_(
                                    'The icon of the social media. Find more icons at <a target="_blank" href="https://fontawesome.com/v5/search">https://fontawesome.com/v5/search</a>'
                                ),
                            ),
                        ),
                        ("image", ImageChooserBlock(required=False)),
                        ("title", blocks.CharBlock(required=True)),
                        ("description", blocks.RichTextBlock(required=False)),
                        ("link", blocks.URLBlock(required=True)),
                    ]
                ),
            ),
        ],
        blank=True,
        null=True,
        help_text=_("The social media of the site."),
        use_json_field=True,
    )

    basic_settings_tab_panels = [
        FieldPanel("site_name"),
        FieldPanel("site_description"),
        FieldPanel("site_logo"),
        FieldPanel("site_favorite_icon"),
        InlinePanel("site_settings_theme", label="Themes", min_num=1, max_num=1),
        FieldPanel("copy_right"),
        FieldPanel("inquiry_mode"),
    ]
    contact_social_media_tab_panels = [
        FieldPanel("contact_email"),
        FieldPanel("contact_phone"),
        FieldPanel("contact_address"),
        FieldPanel("contact_content"),
        FieldPanel("social_media"),
    ]
    tracking_and_analytics_tab_panels = [
        FieldPanel("google_analytics"),
        FieldPanel("google_tag_manager_id"),
        FieldPanel("facebook_pixel"),
    ]
    security_settings_tab_panels = [
        FieldPanel("google_recaptcha_site_key"),
        FieldPanel("google_recaptcha_secret_key"),
    ]
    seo_settings_tab_panels = [
        FieldPanel("default_meta_title"),
        FieldPanel("default_meta_description"),
        FieldPanel("default_meta_keywords"),
        FieldPanel("default_social_image"),
        FieldPanel("sitemap_active"),
        FieldPanel("robots_txt"),
    ]

    external_scripts_and_styles_tab_panels = [
        FieldPanel("custom_js"),
        FieldPanel("custom_css"),
    ]
    third_party_intergations_tab_panels = [
        FieldPanel("google_maps_api_key"),
    ]

    edit_handler = TabbedInterface(
        [
            ObjectList(basic_settings_tab_panels, heading=_("Basic Settings")),
            ObjectList(
                contact_social_media_tab_panels, heading=_("Contact and Social Media")
            ),
            ObjectList(
                tracking_and_analytics_tab_panels, heading=_("Tracking and Analytics")
            ),
            ObjectList(security_settings_tab_panels, heading=_("Security Settings")),
            ObjectList(seo_settings_tab_panels, heading=_("SEO Settings")),
            ObjectList(
                external_scripts_and_styles_tab_panels,
                heading=_("External Scripts and Styles"),
            ),
            ObjectList(
                third_party_intergations_tab_panels,
                heading=_("Third Party Integrations"),
            ),
        ]
    )

    class Meta:
        verbose_name = _("Site setting")
        verbose_name_plural = _("Site settings")

    @classmethod
    def user_is_member_of_organization(self, user, site):
        if user.is_superuser:
            return True
        site = site
        try:

            organization = site.extendedsite.organization
            # check if user in organization.memberships.all()
            return organization.memberships.filter(user=user).exists()

        except Exception as e:
            return False

    @classmethod
    def for_request(cls, request):
        """
        Get or create an instance of this model for the request,
        and cache the result on the request for faster repeat access.
        """
        attr_name = cls.get_cache_attr_name()
        if hasattr(request, attr_name):
            return getattr(request, attr_name)
        site = Site.find_for_request(request)
        site_settings = cls.for_site(site)
        # to allow more efficient page url generation
        site_settings._request = request
        setattr(request, attr_name, site_settings)
        # check if the user is member of the organization
        # if not cls.user_is_member_of_organization(request.user, site):
        #     raise PermissionDenied
        return site_settings


@register_setting
class FooterMenu(BaseSiteSetting):
    footer_menu = StreamField(
        [
            (
                "column",
                ModelChooserBlock("organization_menu.OrganizationFlatMenu"),
            ),
        ],
        blank=True,
        null=True,
        help_text=_(
            "The footer menu of the site, you need add footer menu items first."
        ),
        use_json_field=True,
    )
    panels = [
        FieldPanel("footer_menu"),
    ]

    class Meta:
        verbose_name = _("Footer Menu")
        verbose_name_plural = _("Footer Menu")


class ExtendedSite(models.Model):
    site = models.OneToOneField(Site, on_delete=models.CASCADE, primary_key=True)
    template_folder = models.CharField(
        max_length=50, choices=TEMPLATE_FOLDER_CHOICES, default="default"
    )
    organization = models.ForeignKey(
        "organization.Organization", on_delete=models.CASCADE
    )

    def __str__(self):
        return self.site.hostname

    panels = [
        FieldPanel("template_folder"),
        FieldPanel("organization", permission="organization.view_organization"),
        FieldPanel("site", permission="organization.view_organization"),
    ]

    class Meta:
        verbose_name = _("Site setting")
        verbose_name_plural = _("Site settings")

    # @classmethod
    # def find_for_request(cls, request):
    #     site = super().find_for_request(request)
    #     try:
    #         # Return the ExtendedSite instance if it exists
    #         return cls.objects.get(pk=site.pk)
    #     except ObjectDoesNotExist:
    #         # Return the 404 page if the ExtendedSite instance is not found
    #         # TODO: return 404 page or default notice page the request domain is not found
    #         raise Http404


class SoftDeleteManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(deleted_at__isnull=True)


class BaseModel(models.Model):
    site = models.ForeignKey(Site, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(default=timezone.now)
    deleted_at = models.DateTimeField(null=True, default=None, blank=True)

    objects = SoftDeleteManager()
    all_objects = models.Manager()

    class Meta:
        abstract = True

    def delete(self, *args, **kwargs):
        self.deleted_at = timezone.now()
        self.save(handle_ssl=False)

    def hard_delete(self, *args, **kwargs):
        super().delete(*args, **kwargs)

    def restore(self, *args, **kwargs):
        self.deleted_at = None
        self.save()

    def set_site_from_request(self, request):
        self.site = Site.find_for_request(request)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)


class BasePage(MenuPage):
    preview_modes = []
    max_count_per_site = None
    site = models.ForeignKey(Site, on_delete=models.SET_NULL, null=True)
    breadcrumb_background = models.ForeignKey(
        "wagtailimages.Image",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
        help_text=_("The background image for the breadcrumb section."),
    )
    disable_breadcrumb = models.BooleanField(
        default=False,
        help_text=_("Disable the breadcrumb section for this page."),
    )
    content_panels = MenuPage.content_panels + [
        FieldPanel("breadcrumb_background"),
        FieldPanel("disable_breadcrumb"),
    ]

    def user_can_view(self, user):
        group_name = self.site.extendedsite.organization.lower_name + " admins"
        group_name = self.site.extendedsite.organization.lower_name + " admins"
        return user.groups.filter(name=group_name).exists() or user.is_superuser

    def set_site_from_parent(self):
        parent = self.get_parent()
        if parent:
            parent_specific = parent.specific
            if hasattr(parent_specific, "site") and parent_specific.site:
                self.site = parent_specific.site

    def save(self, *args, **kwargs):
        self.set_site_from_parent()

        if (
            self.site
            and self.max_count_per_site is not None
            and self.site.hostname != "localhost"
        ):
            current_page_count = (
                self.__class__.objects.exclude(pk=self.pk)
                .filter(site=self.site)
                .count()
            )

            if current_page_count >= self.max_count_per_site:
                raise ValidationError(
                    f"每个组织只允许有 {self.max_count_per_site} 个 {self.__class__.__name__} 页面"
                )
        super().save(*args, **kwargs)

    @classmethod
    def can_create_for_site(cls, user, site):
        if user.is_superuser:
            return True
        # check if user is a member of site or organization
        if not user.organization_memberships.filter(
            organization=site.extendedsite.organization
        ).exists():
            return False

        if cls.max_count_per_site is None:
            return True
        current_page_count = cls.objects.filter(site=site).count()
        return current_page_count < cls.max_count_per_site

    def get_template(self, request, *args, **kwargs):

        current_site = Site.find_for_request(request)

        site_settings = SiteSettings.for_site(current_site)
        template_folder = site_settings.site_settings_theme.first().template_folder

        template_name = f"{template_folder}/{self.template}"
        is_ajax = request.GET.get("is_ajax", None)

        if request.headers.get("X-Requested-With") == "XMLHttpRequest" or is_ajax:
            template_name = template_name.replace(".html", "_ajax.html")

        return template_name

    def get_landing_page_template(self, request, *args, **kwargs):

        current_site = Site.find_for_request(request)

        site_settings = SiteSettings.for_site(current_site)
        template_folder = site_settings.site_settings_theme.first().template_folder

        return f"{template_folder}/{self.landing_page_template}"

    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request, *args, **kwargs)

        current_site = Site.find_for_request(request)

        extended_site = ExtendedSite.objects.get(site=current_site)

        context["organization"] = {
            "name": extended_site.organization.name,
        }
        context["tentron_current_site"] = current_site

        return context

    def get_page_class_name(self):
        return self.__class__.__name__

    def get_site_name(self):
        return self.site.site_name

    def beautify_title(self):
        if self.seo_title:
            return self.seo_title
        return self.title

    class Meta:
        abstract = True


class OrganizationRootPage(BasePage):
    max_count_per_site = 1
    content_panels = Page.content_panels + [
        FieldPanel("site"),
    ]

    class Meta:
        verbose_name = "Organization Root Page"


class Organization(ClusterableModel, BaseModel):
    name = models.CharField(max_length=255, unique=True)
    domain = models.CharField(max_length=255, null=True, blank=True, unique=True)
    ssl_enabled = models.BooleanField(
        default=False, help_text=_("Enable SSL, becareful the limit of Let's Encrypt.")
    )
    active_status = models.BooleanField(default=True)
    expiry_date = models.DateTimeField(null=True, blank=True)
    description = models.TextField(blank=True)

    panels = [
        FieldPanel("name"),
        FieldPanel("domain"),
        FieldPanel("ssl_enabled"),
        FieldPanel("active_status"),
        FieldPanel("expiry_date"),
        FieldPanel("description"),
        InlinePanel("memberships", label="Members"),
    ]

    def __str__(self):
        return self.name

    def clean(self):
        super().clean()

        if self.domain:
            self.domain = self.domain.lower()
            domain_regex = r"^[a-z0-9]+([\-\.]{1}[a-z0-9]+)*\.[a-z]{2,5}$"
            if not re.match(domain_regex, self.domain) and not settings.DEBUG:
                raise ValidationError(
                    _("Domain name is not valid, please check again.")
                )

    @transaction.atomic
    def initialize_organization(self):
        default_user = self._create_default_user_and_membership()
        (
            new_site,
            organization_root_page,
            new_home_page,
        ) = self._create_organization_site_and_root_page(default_user)
        default_group = self._create_default_group_and_permissions(
            default_user, organization_root_page
        )

        self._create_product_quote_page_and_fields(
            default_user, new_site, new_home_page
        )
        self._create_default_pages_and_menu_items(
            default_user, new_site, organization_root_page, new_home_page
        )
        self._create_nginx_config_file()
        self._create_nginx_ssl_config_file()

    def _create_default_user_and_membership(self):
        username = slugify(self.name)
        default_user = get_user_model().objects.create(
            username=username,
            email=f"default_user_{self.pk}@example.com",
            password=make_password("password"),
        )

        membership = OrganizationMembership(
            organization=self, user=default_user, sort_order=0
        )
        membership.save()
        self.memberships.add(membership)
        return default_user

    def _create_default_group_and_permissions(
        self, default_user, organization_root_page
    ):

        default_group, created = Group.objects.get_or_create(
            name=self.lower_name + " admins"
        )
        default_group.user_set.add(default_user)
        self._assign_default_group_permissions(default_group, organization_root_page)
        return default_group

    def _add_permissions_to_group(self, group, app_label, codenames):
        permissions = Permission.objects.filter(
            content_type__app_label=app_label, codename__in=codenames
        )
        for permission in permissions:
            group.permissions.add(permission)

    def _add_collection_permissions_to_group(
        self, group, collection, app_label, codenames
    ):
        permissions = Permission.objects.filter(
            content_type__app_label=app_label, codename__in=codenames
        )
        for permission in permissions:
            GroupCollectionPermission.objects.create(
                group=group,
                collection=collection,
                permission=permission,
            )

    def _assign_default_group_permissions(self, default_group, organization_root_page):
        # 在这里添加分配默认组权限的代码
        wagtail_permission_types = [
            "add",
            "edit",
            "publish",
            "bulk_delete",
            "lock",
            "unlock",
        ]

        for permission_type in wagtail_permission_types:
            GroupPagePermission.objects.create(
                group=default_group,
                page=organization_root_page,
                permission_type=permission_type,
            )

        # use organization name to create organization's collection, and assign default permissions to image, document, and collection management.
        # get root collection
        root_collection = Collection.objects.get(name="Root")

        # create organization collection inside root collection
        organization_collection = Collection(name=self.name)

        root_collection.add_child(instance=organization_collection)

        # Assign image permission types
        self._add_collection_permissions_to_group(
            default_group,
            organization_collection,
            "wagtailimages",
            ["add_image", "change_image", "choose_image"],
        )

        # Assign document permission types
        self._add_collection_permissions_to_group(
            default_group,
            organization_collection,
            "wagtaildocs",
            ["add_document", "change_document", "choose_document"],
        )

        # Assign document permission types
        self._add_collection_permissions_to_group(
            default_group,
            organization_collection,
            "wagtailcore",
            ["add_collection", "change_collection", "delete_collection"],
        )
        permission_list = [
            # Assign default site permissions
            ("wagtailadmin", ["access_admin"]),
            # Blogpage category permissions
            (
                "core",
                ["add_blogcategory", "change_blogcategory", "delete_blogcategory"],
            ),
            # Blogpage tags permissions
            ("core", ["add_blogtag", "change_blogtag", "delete_blogtag"]),
            # organization menu permissions
            (
                "organization_menu",
                ["change_organizationmainmenu", "view_organizationmainmenu"],
            ),
            # Flat menu and menu item permissions
            (
                "organization_menu",
                [
                    "add_organizationflatmenu",
                    "change_organizationflatmenu",
                    "delete_organizationflatmenu",
                ],
            ),
            (
                "organization_menu",
                [
                    "add_organizationflatmenuitem",
                    "change_organizationflatmenuitem",
                    "delete_organizationflatmenuitem",
                ],
            ),
            # Footer menu permissions
            ("organization", ["change_footermenu", "view_footermenu"]),
            # Faqcategory permissions
            ("core", ["add_faqcategory", "change_faqcategory", "delete_faqcategory"]),
            # FaqItem permissions
            ("core", ["add_faqitem", "change_faqitem", "delete_faqitem"]),
            # Attribute permissions
            ("core", ["add_attribute", "change_attribute", "delete_attribute"]),
            # Attribute Value permissions
            (
                "core",
                [
                    "add_attributevalue",
                    "change_attributevalue",
                    "delete_attributevalue",
                ],
            ),
            # Product category permissions
            ("core", ["add_producttype", "change_producttype", "delete_producttype"]),
            # Template permissions
            ("organization", ["change_extendedsite", "view_extendedsite"]),
            # Site settings permission
            ("organization", ["change_sitesettings"]),
            # Testimonial permissions
            (
                "core",
                [
                    "add_testimonialitem",
                    "change_testimonialitem",
                    "delete_testimonialitem",
                ],
            ),
            # Message permissions
            (
                "message",
                [
                    "add_tentronmessagetask",
                    "view_tentronmessagetask",
                    "view_messagerecipient",
                ],
            ),
        ]
        for app_label, perms in permission_list:
            self._add_permissions_to_group(default_group, app_label, perms)

    def _create_organization_site_and_root_page(self, default_user):
        # check self.domain is valid domain
        if not self.domain:
            raise ValidationError("Domain is required.")
        if Site.objects.filter(hostname=self.domain).exists():
            raise ValidationError("Domain already exists.")
        # create new site
        temp_site = Site.objects.get(hostname="localhost", port=80)
        organization_root_page = OrganizationRootPage(
            title=self.lower_name + " root", site=temp_site
        )

        site_root = Page.objects.get(slug="root")
        site_root.add_child(instance=organization_root_page)
        new_site = Site.objects.create(
            hostname=self.domain,
            port=80,
            root_page=organization_root_page,
            is_default_site=False,
            site_name=f"{self.name} Site",
        )
        HomePage = apps.get_model("home", "HomePage")

        new_home_page = HomePage(
            title="Home",
            slug="home",
            site=new_site,
            first_published_at=timezone.now(),
            live=True,
            owner=default_user,
            seo_title="Home",
            search_description="Home",
            show_in_menus=True,
        )
        organization_root_page.site = new_site
        organization_root_page.save()

        # set new Home Page as the first child of organization root page
        organization_root_page.add_child(instance=new_home_page)
        new_site.root_page = new_home_page
        new_site.save()

        ExtendedSite.objects.create(
            site=new_site, organization=self, template_folder="default"
        )
        self.site = new_site
        self.save(handle_ssl=False)
        return new_site, organization_root_page, new_home_page

    def _create_product_quote_page_and_fields(
        self, default_user, new_site, new_home_page
    ):
        # 在这里添加创建产品报价页面和字段的代码

        ProductForm = apps.get_model("core", "ProductForm")
        ProductFormField = apps.get_model("core", "ProductFormField")
        product_quote_page = ProductForm(
            title="Product Quote Page",
            slug="product-quote-page",
            site=new_site,
            first_published_at=timezone.now(),
            live=True,
            owner=default_user,
            seo_title="Get a Quote",
            search_description="Get a Quote",
        )
        new_home_page.add_child(instance=product_quote_page)
        product_quote_page_first_name_field = ProductFormField(
            label="First Name",
            field_type="singleline",
            required=True,
            column_width=6,
            page=product_quote_page,
            sort_order=1,
        )
        product_quote_page_first_name_field.save()
        product_quote_page_last_name_field = ProductFormField(
            label="Last Name",
            field_type="singleline",
            required=True,
            column_width=6,
            page=product_quote_page,
            sort_order=2,
        )
        product_quote_page_last_name_field.save()
        product_quote_page_email_field = ProductFormField(
            label="Email",
            field_type="email",
            required=True,
            column_width=6,
            page=product_quote_page,
            sort_order=3,
        )
        product_quote_page_email_field.save()
        product_quote_page_phone_number_field = ProductFormField(
            label="Phone Number",
            field_type="number",
            required=True,
            column_width=6,
            page=product_quote_page,
            sort_order=4,
        )
        product_quote_page_phone_number_field.save()
        product_quote_page_message_field = ProductFormField(
            label="Message",
            field_type="multiline",
            required=True,
            column_width=12,
            page=product_quote_page,
            sort_order=5,
        )
        product_quote_page_message_field.save()
        # lock down product quote page
        # product_quote_page.locked = True
        # product_quote_page.locked_at = timezone.now()
        # # get superuser
        # superuser = get_user_model().objects.get(is_superuser=True)
        # product_quote_page.locked_by = superuser
        product_quote_page.save()

    def _create_default_pages_and_menu_items(
        self, default_user, new_site, organization_root_page, new_home_page
    ):
        # 在这里添加创建默认页面的代码

        # about page
        AboutPage = apps.get_model("core", "AboutPage")
        about_page = AboutPage(
            title="About",
            slug="about",
            site=new_site,
            first_published_at=timezone.now(),
            live=True,
            owner=default_user,
            seo_title="About",
            search_description="About",
            show_in_menus=True,
        )
        new_home_page.add_child(instance=about_page)
        about_page.content.append(
            ("rich_text", RichText("<p>This is demo body text, please change it.</p>"))
        )
        about_page.save()

        # blog list page
        BlogListPage = apps.get_model("core", "BlogListPage")
        blog_list_page = BlogListPage(
            title="Blog",
            slug="blog",
            site=new_site,
            first_published_at=timezone.now(),
            live=True,
            owner=default_user,
            seo_title="Blog",
            search_description="Blog",
            show_in_menus=True,
        )
        new_home_page.add_child(instance=blog_list_page)
        blog_list_page.content.append(
            ("rich_text", RichText("<p>This is demo body text, please change it.</p>"))
        )
        blog_list_page.save()
        # contact page
        ContactPage = apps.get_model("core", "ContactPage")
        contact_page = ContactPage(
            title="Contact",
            slug="contact",
            site=new_site,
            first_published_at=timezone.now(),
            live=True,
            owner=default_user,
            seo_title="Contact",
            search_description="Contact",
            show_in_menus=True,
        )
        ## add default contact form to contact page, include first name, last name, email, phone number, message
        ContactPage = apps.get_model("core", "ContactPage")
        ContactPageField = apps.get_model("core", "FormField")
        contact_page = ContactPage(
            title="Contact us",
            slug="contact-us",
            site=new_site,
            first_published_at=timezone.now(),
            live=True,
            owner=default_user,
            seo_title="Contact us",
            search_description="Contact us",
            intro="<p>Please fill out the form below to contact us.</p>",
            thank_you_text="<p>Thank you for your message. We will get back to you soon.</p>",
            show_in_menus=True,
        )

        new_home_page.add_child(instance=contact_page)
        contact_page.content.append(
            ("rich_text", RichText("<p>This is demo body text, please change it.</p>"))
        )
        contact_page.save()
        contact_page_first_name_field = ContactPageField(
            label="First Name",
            field_type="singleline",
            required=True,
            page=contact_page,
            sort_order=1,
        )
        contact_page_first_name_field.save()
        contact_page_last_name_field = ContactPageField(
            label="Last Name",
            field_type="singleline",
            required=True,
            page=contact_page,
            sort_order=2,
        )
        contact_page_last_name_field.save()
        contact_page_email_field = ContactPageField(
            label="Email",
            field_type="email",
            required=True,
            page=contact_page,
            sort_order=3,
        )
        contact_page_email_field.save()
        contact_page_phone_number_field = ContactPageField(
            label="Phone Number",
            field_type="number",
            required=True,
            page=contact_page,
            sort_order=4,
        )
        contact_page_phone_number_field.save()
        contact_page_message_field = ContactPageField(
            label="Message",
            field_type="multiline",
            required=True,
            page=contact_page,
            sort_order=5,
        )
        contact_page_message_field.save()

        # faq page
        FaqPage = apps.get_model("core", "FaqPage")
        faq_page = FaqPage(
            title="FAQ",
            slug="faq",
            site=new_site,
            first_published_at=timezone.now(),
            live=True,
            owner=default_user,
            seo_title="FAQ",
            search_description="FAQ",
            show_in_menus=True,
        )
        new_home_page.add_child(instance=faq_page)
        faq_page.content.append(
            ("rich_text", RichText("<p>This is demo body text, please change it.</p>"))
        )
        faq_page.save()
        # product list page
        ProductListPage = apps.get_model("core", "ProductListPage")
        product_list_page = ProductListPage(
            title="Products",
            slug="products",
            site=new_site,
            first_published_at=timezone.now(),
            live=True,
            owner=default_user,
            seo_title="Products",
            search_description="Products",
            show_in_menus=True,
        )
        new_home_page.add_child(instance=product_list_page)
        product_list_page.content.append(
            ("rich_text", RichText("<p>This is demo body text, please change it.</p>"))
        )
        product_list_page.save()

        # project list page
        ProjectListPage = apps.get_model("core", "ProjectListPage")
        project_list_page = ProjectListPage(
            title="Projects",
            slug="projects",
            site=new_site,
            first_published_at=timezone.now(),
            live=True,
            owner=default_user,
            seo_title="Projects",
            search_description="Projects",
            show_in_menus=True,
        )
        new_home_page.add_child(instance=project_list_page)
        project_list_page.content.append(
            ("rich_text", RichText("<p>This is demo body text, please change it.</p>"))
        )
        project_list_page.save()

        # service list page
        ServiceListPage = apps.get_model("core", "ServiceListPage")
        service_list_page = ServiceListPage(
            title="Services",
            slug="services",
            site=new_site,
            first_published_at=timezone.now(),
            live=True,
            owner=default_user,
            seo_title="Services",
            search_description="Services",
            show_in_menus=True,
        )
        new_home_page.add_child(instance=service_list_page)
        service_list_page.content.append(
            ("rich_text", RichText("<p>This is demo body text, please change it.</p>"))
        )
        service_list_page.save()

        # team list page
        TeamListPage = apps.get_model("core", "TeamListPage")
        team_list_page = TeamListPage(
            title="Team",
            slug="team",
            site=new_site,
            first_published_at=timezone.now(),
            live=True,
            owner=default_user,
            seo_title="Team",
            search_description="Team",
            show_in_menus=True,
        )
        new_home_page.add_child(instance=team_list_page)
        team_list_page.content.append(
            ("rich_text", RichText("<p>This is demo body text, please change it.</p>"))
        )
        team_list_page.save()

        # thank you page
        ThankYouPage = apps.get_model("core", "ThankYouPage")
        thank_you_page = ThankYouPage(
            title="Thank You",
            slug="thank-you",
            site=new_site,
            first_published_at=timezone.now(),
            live=True,
            owner=default_user,
            seo_title="Thank You",
            search_description="Thank You",
            show_in_menus=True,
        )
        new_home_page.add_child(instance=thank_you_page)
        thank_you_page.content.append(
            ("rich_text", RichText("<p>This is demo body text, please change it.</p>"))
        )
        thank_you_page.save()

        # main menu
        MainMenu = apps.get_model("organization_menu", "OrganizationMainMenu")
        main_menu = MainMenu.objects.create(
            site=new_site,
            max_levels=2,
        )

        # main menu items
        MenuItem = apps.get_model("organization_menu", "OrganizationMainMenuItem")
        home_menu_item = MenuItem.objects.create(
            menu=main_menu,
            link_page=new_home_page,
            link_text="Home",
            sort_order=1,
        )
        products_menu_item = MenuItem.objects.create(
            menu=main_menu,
            link_page=product_list_page,
            link_text="Products",
            sort_order=2,
        )
        about_menu_item = MenuItem.objects.create(
            menu=main_menu,
            link_page=about_page,
            link_text="About",
            sort_order=3,
        )

        faq_menu_item = MenuItem.objects.create(
            menu=main_menu,
            link_page=faq_page,
            link_text="FAQ",
            sort_order=4,
        )

        projects_menu_item = MenuItem.objects.create(
            menu=main_menu,
            link_page=project_list_page,
            link_text="Projects",
            sort_order=5,
        )
        services_menu_item = MenuItem.objects.create(
            menu=main_menu,
            link_page=service_list_page,
            link_text="Services",
            sort_order=6,
        )
        team_menu_item = MenuItem.objects.create(
            menu=main_menu,
            link_page=team_list_page,
            link_text="Team",
            sort_order=7,
        )
        contact_menu_item = MenuItem.objects.create(
            menu=main_menu,
            link_page=contact_page,
            link_text="Contact",
            sort_order=8,
        )

    def _create_nginx_config_file(self):

        template = """
        # development
        server {{

            proxy_connect_timeout       300s;
            proxy_send_timeout          300s;
            proxy_read_timeout          300s;
            send_timeout                300s;

            listen 80;
            server_name {domain};
            #server_tokens off;
            root /home/app/;
            client_max_body_size 2048M;

            error_page 500 502 503 504 /50x.html;
            location = /50x.html {{
                root /var/www/error_page;
            }}
            location / {{
            # checks for static file, if not found proxy to app
            try_files $uri @proxy_to_dev;
            }}

            location @proxy_to_dev {{
            proxy_pass http://backend_app:9000;
            proxy_set_header Host $http_host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-Proto $scheme;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header HTTP_X_FORWARDED_FOR $remote_addr;
            # we don't want nginx trying to do something clever with
            # redirects, we set the Host: header above already.
            proxy_redirect off;

            }}


            location /static/ {{
                alias /home/app/static/;
            }}
            location /media/ {{
                alias /home/app/media/;
            }}
            #Css and Js
            location ~* \.(css|js)$ {{
                expires 365d;
            }}
            #Image
            location ~* \.(jpg|jpeg|gif|png|webp|ico)$ {{
                expires 365d;
            }}

            #Video
            location ~* \.(mp4|mpeg|avi)$ {{
                expires 365d;
            }}


            location /.well-known/acme-challenge/ {{
                root /var/www/certbot;
            }}
            location = /favicon.ico {{
                root  /home/app/media/default;
            }}
            access_log /var/log/nginx/{domain}.access.dev.log;
            error_log /var/log/nginx/{domain}.error.dev.log;
        }}

        """
        config = template.format(domain=self.domain)
        with open(
            "/home/tentron/nginx/sites-available/{}.http.conf".format(self.domain), "w"
        ) as f:
            f.write(config)
        chain(
            run_command_in_container.s(
                None,
                "tentron_nginx",
                "ln -s /etc/nginx/sites-available/{}.http.conf /etc/nginx/sites-enabled/".format(
                    self.domain
                ),
            ),
            run_command_in_container.s("tentron_nginx", "nginx -t"),
            run_command_in_container.s("tentron_nginx", "nginx -s reload"),
        ).apply_async()

    def _remove_nginx_config_file(self):
        chain(
            run_command_in_container.s(
                None,
                "tentron_nginx",
                "rm /etc/nginx/sites-enabled/{}.http.conf".format(self.domain),
            ),
            run_command_in_container.s(
                "tentron_nginx",
                "rm /etc/nginx/sites-available/{}.http.conf".format(self.domain),
            ),
            run_command_in_container.s("tentron_nginx", "nginx -t"),
            run_command_in_container.s("tentron_nginx", "nginx -s reload"),
        ).apply_async()

    def _create_nginx_ssl_config_file(self):
        # create ssl config for later use
        template = """
        # production
        server {{

            listen 80;
            server_name  {domain};
            charset     utf-8;

            client_max_body_size 2048M;

            location /.well-known/acme-challenge/ {{
                root /var/www/certbot;
            }}
            
            location / {{
                return 301 https://{domain}$request_uri;
            }}

        }}

        # Production www 443
        server {{

            proxy_connect_timeout       300s;
            proxy_send_timeout          300s;
            proxy_read_timeout          300s;
            send_timeout                300s;

            listen 443 ssl;
            http2 on;
            server_name {domain};
            #server_tokens off;
            root /home/app/;
            client_max_body_size 2048M;

            ssl_certificate /etc/letsencrypt/live/{domain}/fullchain.pem;
            ssl_certificate_key /etc/letsencrypt/live/{domain}/privkey.pem;

            include /etc/letsencrypt/options-ssl-nginx.conf;
            ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem;

            error_page 500 502 503 504 /50x.html;
            location = /50x.html {{
                root /var/www/error_page;
            }}

            location / {{
            # checks for static file, if not found proxy to app
            try_files $uri @proxy_to_prod;
            }}

            location @proxy_to_prod {{
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            proxy_set_header Host $http_host;
            # we don't want nginx trying to do something clever with
            # redirects, we set the Host: header above already.
            proxy_redirect off;
            proxy_pass http://backend_app:9000;
            }}



            location /static/ {{
                alias /home/app/static/;
            }}
            location /media/ {{
                alias /home/app/media/;
            }}
            #Css and Js
            location ~* \.(css|js)$ {{
                expires 365d;
            }}
            #Image
            location ~* \.(jpg|jpeg|gif|png|webp|ico)$ {{
                expires 365d;
            }}

            #Video
            location ~* \.(mp4|mpeg|avi)$ {{
                expires 365d;
            }}


            location /.well-known/acme-challenge/ {{
                root /var/www/certbot;
            }}
            location = /favicon.ico {{
                root  /home/app/media/default;
            }}

            access_log /var/log/nginx/{domain}.https.log;
            error_log /var/log/nginx/{domain}.https.log;
        }}


        """
        config = template.format(domain=self.domain)
        with open(
            "/home/tentron/nginx/sites-available/{}.https.conf".format(self.domain), "w"
        ) as f:
            f.write(config)

    def _remove_nginx_ssl_config_file(self):
        chain(
            run_command_in_container.s(
                None,
                "tentron_nginx",
                "rm /etc/nginx/sites-enabled/{}.https.conf".format(self.domain),
            ),
            run_command_in_container.s(
                "tentron_nginx",
                "rm /etc/nginx/sites-available/{}.https.conf".format(self.domain),
            ),
            run_command_in_container.s("tentron_nginx", "nginx -t"),
            run_command_in_container.s("tentron_nginx", "nginx -s reload"),
            run_command_in_container.s(
                "CertBot",
                "certbot delete --cert-name {} --non-interactive".format(self.domain),
            ),
        ).apply_async()

    def _apply_ssl_certificate(self):
        print("apply ssl certificate")
        # apply ssl certificate
        # For development use --test-cert to avoid rate limit
        if settings.DEBUG:
            test_command = "certbot certonly --webroot -w /var/www/certbot \
                    --test-cert \
                    --register-unsafely-without-email \
                    -d {} \
                    --rsa-key-size 4096 \
                    --agree-tos \
                    --force-renewal".format(
                self.domain
            )
        else:
            # For production use dry-run test network
            test_command = "certbot certonly --webroot -w /var/www/certbot \
                        --dry-run \
                        --register-unsafely-without-email \
                        -d {} \
                        --rsa-key-size 4096 \
                        --agree-tos \
                        --force-renewal".format(
                self.domain
            )
        if settings.DEBUG:
            # For development use --test-cert to avoid rate limit
            apply_command = "certbot certonly --webroot -w /var/www/certbot \
                --test-cert \
                --register-unsafely-without-email \
                -d {} \
                --rsa-key-size 4096 \
                --agree-tos \
                --force-renewal".format(
                self.domain
            )
        else:
            # For production use
            apply_command = "certbot certonly --webroot -w /var/www/certbot \
                --register-unsafely-without-email \
                -d {} \
                --rsa-key-size 4096 \
                --agree-tos \
                --force-renewal".format(
                self.domain
            )
        chain(
            run_command_in_container.s(None, "CertBot", test_command),
            run_command_in_container.s("CertBot", apply_command),
            run_command_in_container.s(
                "tentron_nginx",
                "rm /etc/nginx/sites-enabled/{}.http.conf".format(self.domain),
            ),
            run_command_in_container.s(
                "tentron_nginx",
                "ln -s /etc/nginx/sites-available/{}.https.conf /etc/nginx/sites-enabled/".format(
                    self.domain
                ),
            ),
            run_command_in_container.s("tentron_nginx", "nginx -t"),
            run_command_in_container.s("tentron_nginx", "nginx -s reload"),
        ).apply_async()

    def _renew_ssl_certificate(self):
        print("renew ssl certificate")
        pass

    def _remove_ssl_certificate(self):
        # Remove ssl certificate config files, link to http config file
        chain(
            run_command_in_container.s(
                None,
                "tentron_nginx",
                "rm /etc/nginx/sites-enabled/{}.https.conf".format(self.domain),
            ),
            run_command_in_container.s(
                "tentron_nginx",
                "ln -s /etc/nginx/sites-available/{}.http.conf /etc/nginx/sites-enabled/".format(
                    self.domain
                ),
            ),
            run_command_in_container.s("tentron_nginx", "nginx -t"),
            run_command_in_container.s("tentron_nginx", "nginx -s reload"),
            run_command_in_container.s(
                "CertBot",
                "certbot delete --cert-name {} --non-interactive".format(self.domain),
            ),
        ).apply_async()

    def shutdown_organization(self):

        # remove organization from nginx config file
        run_command_in_container.apply_async(
            (
                None,
                "tentron_nginx",
                "rm /etc/nginx/sites-enabled/{}.http.conf".format(self.domain),
            ),
        )

        run_command_in_container.apply_async(
            (
                None,
                "tentron_nginx",
                "rm /etc/nginx/sites-enabled/{}.https.conf".format(self.domain),
            ),
        )

        run_command_in_container.apply_async((None, "tentron_nginx", "nginx -s reload"))
        # shutdown organization
        self.active_status = False
        self.domain = "deleted-" + uuid.uuid4().hex + "-" + self.domain
        self.save(handle_ssl=False)

    @property
    def lower_name(self):
        return self.name.lower()

    def save(self, handle_ssl=True, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)
        if is_new:
            # if environment is production, use target ip otherwise disable this function for develop.
            if not settings.DEBUG:
                self._check_domain_name()

            self.initialize_organization()

        # Handle SSL certificate only if not a new instance
        elif handle_ssl:
            if self.ssl_enabled:
                self._handle_ssl_certificate()
            else:
                self._remove_ssl_certificate()

    def _check_domain_name(self):
        target_ip = settings.SERVER_IP
        try:
            ip_address = socket.gethostbyname(self.domain)

            if ip_address != target_ip:
                raise ValidationError(
                    "Domain name is not pointed to the correct ip address."
                )
        except (socket.gaierror, Exception) as e:
            print(e)
            logger.error(e)
            raise ValidationError(
                "Domain name is not pointed to the correct ip address."
            )

    def _handle_ssl_certificate(self):
        cert_path = "/etc/letsencrypt/live/{}/fullchain.pem".format(self.domain)
        privkey_path = "/etc/letsencrypt/live/{}/privkey.pem".format(self.domain)

        if os.path.exists(cert_path) and os.path.exists(privkey_path):
            self._renew_ssl_certificate_if_needed(cert_path)
        else:
            self._apply_ssl_certificate()

    def _renew_ssl_certificate_if_needed(self, cert_path):
        if os.path.getmtime(cert_path) < time.time() - 60 * 60 * 24 * 30:
            logger.info("Renewing SSL certificate for %s", self.domain)
            self._renew_ssl_certificate()
        else:
            logger.info("Certificate is not older than 30 days, do nothing")

    def delete(self, *args, **kwargs):
        # delete organization root page
        if self.domain is None:
            raise ValidationError("Domain name is required.")
        try:
            organization_root_page = OrganizationRootPage.objects.get(site=self.site)
            organization_root_page.delete()
        except:
            logger.error("Organization root page not found")
            pass

        # delete main menu
        try:
            MainMenu = apps.get_model("organization_menu", "OrganizationMainMenu")
            main_menu = MainMenu.objects.get(site=self.site)
            main_menu.delete()
        except:
            logger.error("Main menu not found")
            pass

        # delete menu items
        try:
            MenuItem = apps.get_model("organization_menu", "OrganizationMainMenuItem")
            menu_items = MenuItem.objects.filter(menu=main_menu)
            for menu_item in menu_items:
                menu_item.delete()
        except:
            logger.error("Menu items not found")
            pass

        # delete collection
        try:
            Collection.objects.filter(name=self.name).delete()
        except:
            logger.error("Collection not found")
            pass

        # delete user
        try:
            default_group_name = self.lower_name + " admins"
            default_group = Group.objects.get(name=default_group_name)
            default_group.user_set.all().delete()
        except:
            logger.error("Default group not found")
            pass

        # delete organization membership
        try:
            OrganizationMembership.objects.filter(organization=self).delete()
        except:
            logger.error("Organization membership not found")
            pass

        # delete group
        try:
            default_group.delete()
        except:
            logger.error("Default group not found")
            pass

        try:
            self._remove_nginx_config_file()
            self._remove_nginx_ssl_config_file()
        except:
            logger.error("Nginx config file not found")
            pass

        self.name = "deleted-" + uuid.uuid4().hex + "-" + self.name
        self.domain = "deleted-" + uuid.uuid4().hex + "-" + self.domain
        self.save(handle_ssl=False)

        # delete organization
        try:
            super().delete(*args, **kwargs)
        except:
            logger.error("Organization not found")
            pass

        # delete site
        try:
            self.site.delete()
        except:
            logger.error("Site not found")
            pass

    @property
    def default_group(self):
        # get organization group by name
        return Group.objects.get(name=self.lower_name + " admins")

    @property
    def collection(self):
        default_group = self.default_group
        collection_permission = GroupCollectionPermission.objects.filter(
            group=default_group
        ).first()

        if collection_permission is None:
            return None
        return collection_permission.collection

    # def get_organization_root_page(self):
    #     return self.root_pages.first()

    # def get_organization_pages(self):
    #     return self.get_organization_root_page().get_descendants().specific()


class OrganizationMembership(Orderable):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="organization_memberships",
    )
    organization = ParentalKey(
        Organization,
        on_delete=models.CASCADE,
        related_name="memberships",
    )

    panels = [
        FieldPanel("user"),
        FieldPanel("organization"),
    ]

    class Meta:
        verbose_name = "Organization Membership"
        verbose_name_plural = "Organization Memberships"
        unique_together = ("user", "organization")

    def __str__(self):
        return f"{self.user} - {self.organization}"
