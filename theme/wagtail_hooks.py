from django.utils.translation import gettext_lazy as _
from wagtail import hooks
from wagtail.contrib.modeladmin.options import ModelAdmin, modeladmin_register
from wagtail.models import Site

from theme.models import Theme


class ThemeAdmin(ModelAdmin):
    model = Theme
    menu_label = _("Themes")
    menu_icon = "folder-open-inverse"
    menu_order = 300
    add_to_settings_menu = False
    exclude_from_explorer = True
    list_display = ("name", "slug", "is_common", "user")
    list_filter = ("is_common", "user")
    search_fields = ("name", "slug", "description")
    # edit_template_name = "theme/theme/edit.html"

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs

        return qs.filter(user=request.user)


modeladmin_register(ThemeAdmin)
