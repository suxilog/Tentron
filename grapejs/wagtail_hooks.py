from django.shortcuts import render
from wagtail import hooks
from wagtail.admin.views.pages.create import CreateView
from wagtail.contrib.modeladmin.options import (
    ModelAdmin,
    ModelAdminGroup,
    modeladmin_register,
)

from grapejs.models import CustomPage

from .views import CustomPageCreateView

# class GrapeJsAdmin(ModelAdmin):
#     model = CustomPage
#     menu_label = "GrapeJs"
#     menu_icon = "help"
#     menu_order = 230
#     list_display = ("title",)
#     search_fields = ("title",)


# modeladmin_register(GrapeJsAdmin)
