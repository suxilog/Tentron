from tabnanny import verbose

from django.db import models
from django.utils import timezone, translation
from django.utils.translation import gettext_lazy as _
from modelcluster.fields import ParentalKey
from wagtail.admin.panels import (
    FieldPanel,
    FieldRowPanel,
    InlinePanel,
    MultiFieldPanel,
    PageChooserPanel,
)
from wagtail.images import get_image_model_string
from wagtail.models import Page, Site
from wagtailmenus.conf import settings
from wagtailmenus.models import (
    AbstractFlatMenu,
    AbstractFlatMenuItem,
    AbstractMainMenu,
    AbstractMainMenuItem,
)
from wagtailmenus.panels import FlatMenuItemsInlinePanel
from wagtailmodelchooser import Chooser, register_model_chooser

from organization.models import OrganizationRootPage


class OrganizationMainMenu(AbstractMainMenu):
    """A menu that is specific to an organization."""

    class Meta:
        verbose_name = _("Organization Main Menu")
        verbose_name_plural = _("Organization Main Menus")


class OrganizationMainMenuItem(AbstractMainMenuItem):
    """
    A menu item that is specific to an organization.
    """

    menu = ParentalKey(
        OrganizationMainMenu,
        on_delete=models.CASCADE,
        related_name=settings.MAIN_MENU_ITEMS_RELATED_NAME,
    )

    image = models.ForeignKey(
        get_image_model_string(),
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )

    hover_description = models.CharField(
        _("Hover Description"),
        max_length=250,
        blank=True,
    )

    panels = [
        PageChooserPanel("link_page", can_choose_root=False),
        FieldPanel("link_url"),
        FieldPanel("url_append"),
        FieldPanel("link_text"),
        FieldPanel("handle"),
        FieldPanel("allow_subnav"),
        FieldPanel("image"),
        FieldPanel("hover_description"),
    ]


class OrganizationFlatMenu(AbstractFlatMenu):
    content_panels = (
        MultiFieldPanel(
            heading=_("Menu details"),
            children=(
                FieldPanel("title"),
                FieldPanel("site", permission="is_superuser"),
                FieldPanel("handle"),
                FieldPanel("heading"),
            ),
            classname="collapsible",
        ),
        FlatMenuItemsInlinePanel(),
    )

    class Meta:
        verbose_name = _("Flat Menu")
        verbose_name_plural = _("Flat Menus")


class OrganizationFlatMenuItem(AbstractFlatMenuItem):
    """A custom menu item model to be used by ``TranslatedFlatMenu``"""

    menu = ParentalKey(
        OrganizationFlatMenu,  # we can use the model from above
        on_delete=models.CASCADE,
        related_name=settings.FLAT_MENU_ITEMS_RELATED_NAME,
    )
    image = models.ForeignKey(
        get_image_model_string(),
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )

    hover_description = models.CharField(
        _("Hover Description"),
        max_length=250,
        blank=True,
    )
    panels = (
        PageChooserPanel("link_page"),
        FieldPanel("link_url"),
        FieldPanel("url_append"),
        FieldPanel("handle"),
        FieldPanel("link_text"),
        FieldPanel("allow_subnav"),
        FieldPanel("image"),
        FieldPanel("hover_description"),
    )


@register_model_chooser
class OrganizationFlatMenuChooser(Chooser):
    model = OrganizationFlatMenu
    model_template = "wagtailmodelchooser/modal.html"
    modal_results_template = "wagtailmodelchooser/results.html"

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        site = Site.find_for_request(request)
        return qs.filter(site=site)
