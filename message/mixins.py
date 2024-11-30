from django.utils.translation import gettext_lazy as _
from wagtail.admin.panels import (
    FieldPanel,
    InlinePanel,
    MultiFieldPanel,
    ObjectList,
    TabbedInterface,
)


class BaseAdminMixin:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def get_queryset(self, request):
        self.request = request
        return super().get_queryset(request)


class TentronAdminMixin(BaseAdminMixin):

    default_panels = [
        FieldPanel("sender"),
        FieldPanel("recipient"),
        FieldPanel("content"),
        FieldPanel("send_to_all"),
    ]

    default_edit_handler = TabbedInterface(
        [
            ObjectList(default_panels, heading="Message"),
        ]
    )
