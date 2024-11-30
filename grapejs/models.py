from bs4 import BeautifulSoup
from django.db import models
from django.forms.widgets import HiddenInput
from wagtail.admin.panels import FieldPanel
from wagtail.fields import StreamField

from core.blocks import CustomPageBlock

# Create your models here.
from organization.models import BasePage


class CustomPage(BasePage):
    css_content = models.TextField(blank=True, null=True)
    html_content = models.TextField(blank=True, null=True)
    json_content = models.JSONField(blank=True, null=True)
    content_panels = BasePage.content_panels + [
        # hide json_content
        FieldPanel(
            "json_content",
            permission="change_custompage",
            widget=HiddenInput,
            classname="hidden",
        ),
        FieldPanel("html_content", widget=HiddenInput, classname="hidden"),
        FieldPanel(
            "css_content",
            widget=HiddenInput,
            permission="change_custompage",
            classname="hidden",
        ),
    ]
    template = "content.html"

    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request, *args, **kwargs)
        # Parse the HTML
        soup = BeautifulSoup(self.html_content, "html.parser")

        # Extract the body tag
        body = soup.find("body")

        # Extract the contents of the body tag
        body_contents = body.contents

        # Convert the body contents back into a string
        body_contents_str = "".join(str(item) for item in body_contents)

        # Update the HTML content to be the body contents
        context["html_content"] = body_contents_str
        context["css_content"] = self.css_content
        context["json_content"] = self.json_content
        return context
