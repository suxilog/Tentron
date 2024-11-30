# init a grapejs block

from email.policy import default

from django.apps import apps
from django.template.loader import render_to_string
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _
from modelcluster.fields import ParentalKey, ParentalManyToManyField
from modelcluster.models import ClusterableModel
from wagtail import blocks
from wagtail.blocks import StructValue
from wagtail.contrib.table_block.blocks import TableBlock
from wagtail.contrib.typed_table_block.blocks import TypedTableBlock
from wagtail.documents.blocks import DocumentChooserBlock
from wagtail.images.blocks import ImageChooserBlock
from wagtail.models import Site
from wagtail.snippets.blocks import SnippetChooserBlock
from wagtailmodelchooser.blocks import ModelChooserBlock

from organization.models import SiteSettings


class LinkStructValue(StructValue):
    def url(self):
        external_url = self.get("external_url")
        page = self.get("page")
        if page:
            return page.url
        elif external_url:
            return external_url


class BlockTempateMixin:
    def get_template(self, context=None):
        if context is not None and "request" in context:
            current_site = Site.find_for_request(context["request"])
            site_settings = SiteSettings.for_site(current_site)
            template_folder = site_settings.site_settings_theme.first().template_folder
            template_name = f"{template_folder}/{getattr(self.meta, 'template', None)}"
        else:
            # Use the default template if context is None or doesn't contain 'request'
            template_name = getattr(self.meta, "template", None)

        return template_name

    def render(self, value, context=None):
        """
        Return a text rendering of 'value', suitable for display on templates. By default, this will
        use a template (with the passed context, supplemented by the result of get_context) if a
        'template' property is specified on the block, and fall back on render_basic otherwise.
        """
        template = self.get_template(context=context)
        print(template)
        if not template:
            return self.render_basic(value, context=context)

        if context is None:
            new_context = self.get_context(value)
        else:
            new_context = self.get_context(value, parent_context=dict(context))

        return mark_safe(render_to_string(template, new_context))


class CustomPageBlock(BlockTempateMixin, blocks.StructBlock):
    json_content = blocks.TextBlock(required=False)

    class Meta:
        template = "grapejs/grapejs_block.html"
        icon = "help"
        label = "Custom Page Block"


class SocialBlock(BlockTempateMixin, blocks.StructBlock):
    social_name = blocks.CharBlock(required=False)
    social_link = blocks.CharBlock(required=True)
    icon = blocks.CharBlock(
        required=True, help_text="Font Awesome Icon", default="fab fa-facebook-f"
    )

    class Meta:
        template = "core/blocks/social_block.html"
        icon = "help"
        label = _("Social Block")


class TestimonialBlock(BlockTempateMixin, blocks.StructBlock):
    heading = blocks.CharBlock(required=False)
    subheading = blocks.CharBlock(required=False)

    testimonials = blocks.ListBlock(ModelChooserBlock("core.TestimonialItem"))

    class Meta:
        template = "blocks/testimonial_block.html"
        icon = "help"
        label = _("Testimonial Block")


class BlockQuoteBlock(BlockTempateMixin, blocks.StructBlock):
    quote = blocks.CharBlock(required=True)
    author = blocks.CharBlock(required=False)
    author_title = blocks.CharBlock(required=False)
    quotation_link = blocks.CharBlock(required=False)
    footer_text = blocks.CharBlock(required=False)

    class Meta:
        template = "blocks/blockquote_block.html"
        icon = "help"
        label = _("Block Quote Block")


class ImageBlock(BlockTempateMixin, blocks.StructBlock):
    image = ImageChooserBlock(required=True)
    caption = blocks.CharBlock(required=False)

    class Meta:
        template = "blocks/image_block.html"
        icon = "help"
        label = _("Image Block")


class ImageContentBlock(BlockTempateMixin, blocks.StructBlock):
    image = ImageChooserBlock(required=True)
    caption = blocks.CharBlock(required=False)
    content = blocks.RichTextBlock(required=False)

    class Meta:
        template = "blocks/image_content_block.html"
        icon = "help"
        label = _("Image Content Block")


# Blog blocks
class AudioBlock(BlockTempateMixin, blocks.StructBlock):
    file = DocumentChooserBlock(required=True)

    class Meta:
        template = "blocks/audio_block.html"
        icon = "media"
        label = _("Audio Block")


class CarouselBlock(BlockTempateMixin, blocks.StructBlock):
    images = blocks.ListBlock(ImageChooserBlock(required=True))

    class Meta:
        template = "blocks/carousel_block.html"
        icon = "image"
        label = _("Carousel Block")


class HomeDefaultSliderBlock(BlockTempateMixin, blocks.StructBlock):
    background = ImageChooserBlock(required=True)
    heading = blocks.CharBlock(required=False)
    subheading = blocks.CharBlock(required=False)
    context = blocks.RichTextBlock(required=False)
    button_text = blocks.CharBlock(required=False)
    external_url = blocks.URLBlock(label="External URL", required=False)
    page = blocks.PageChooserBlock(
        label="Page",
        required=False,
    )

    class Meta:
        template = "blocks/home_default_slider_block.html"
        icon = "image"
        label = _("Home Default Slider Block")
        value_class = LinkStructValue


class SwiperSliderBlock(BlockTempateMixin, blocks.StructBlock):
    background = ImageChooserBlock(required=True)
    heading = blocks.CharBlock(required=False)
    subheading = blocks.CharBlock(required=False)
    context = blocks.RichTextBlock(required=False)
    button_text = blocks.CharBlock(required=False)
    external_url = blocks.URLBlock(label="External URL", required=False)
    page = blocks.PageChooserBlock(
        label="Page",
        required=False,
    )

    class Meta:
        value_class = LinkStructValue


class HomeSwiperSliderBlock(BlockTempateMixin, blocks.StructBlock):
    sliders = blocks.ListBlock(SwiperSliderBlock())

    class Meta:
        template = "blocks/home_swiper_slider_block.html"
        icon = "image"
        label = _("Home Swiper Slider Block")


# End Blog blocks

# Custom Blocks


class TentronTableBlock(BlockTempateMixin, TableBlock):
    def render(self, value, context=None):
        template = self.get_template(context=context)
        if template and value:
            table_header = (
                value["data"][0]
                if value.get("data", None)
                and len(value["data"]) > 0
                and value.get("first_row_is_table_header", False)
                else None
            )
            first_col_is_header = value.get("first_col_is_header", False)

            if context is None:
                new_context = {}
            else:
                new_context = dict(context)

            new_context.update(
                {
                    "self": value,
                    self.TEMPLATE_VAR: value,
                    "table_header": table_header,
                    "first_col_is_header": first_col_is_header,
                    "html_renderer": self.is_html_renderer(),
                    "table_caption": value.get("table_caption"),
                    "data": value["data"][1:]
                    if table_header
                    else value.get("data", []),
                }
            )

            if value.get("cell"):
                new_context["classnames"] = {}
                for meta in value["cell"]:
                    if "className" in meta:
                        new_context["classnames"][(meta["row"], meta["col"])] = meta[
                            "className"
                        ]

            return render_to_string(template, new_context)
        else:
            return self.render_basic(value or "", context=context)

    class Meta:
        template = "blocks/table.html"
        icon = "table"
        label = _("Table")


class TentronTypedTableBlock(BlockTempateMixin, TypedTableBlock):
    class Meta:
        template = "blocks/typed_table_block.html"
        icon = "table"
        label = _("Typed table")
