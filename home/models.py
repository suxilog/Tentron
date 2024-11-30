from django.db import models
from django.utils.translation import gettext_lazy as _
from wagtail.admin.panels import FieldPanel
from wagtail.fields import StreamField
from wagtail.models import Site

from core import blocks as tentron_blocks
from organization.models import BasePage, SiteSettings


class HomePage(BasePage):
    template = "index.html"
    parent_page_types = ["organization.OrganizationRootPage"]
    content = StreamField(
        [
            ("default_slider", tentron_blocks.HomeDefaultSliderBlock()),
            ("swiper_slider", tentron_blocks.HomeSwiperSliderBlock()),
        ],
        null=True,
        blank=True,
        use_json_field=True,
        max_num=1,
        min_num=1,
    )

    content_panels = BasePage.content_panels + [
        FieldPanel("content"),
    ]
