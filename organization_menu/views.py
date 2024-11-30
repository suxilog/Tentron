from re import I

from django.shortcuts import get_object_or_404, redirect, render
from wagtail.contrib.modeladmin.views import (
    CreateView,
    EditView,
    ModelFormView,
    WMABaseView,
)
from wagtail.models import Site

from organization.models import FooterMenu


class FooterMenuIndexView(WMABaseView):
    def dispatch(self, request, *args, **kwargs):
        site = Site.find_for_request(request)
        # get site site_settings, if not exist create one
        site_settings = FooterMenu.for_site(site)
        return redirect(
            self.url_helper.get_action_url("edit", site_settings.id)
        )  # redirect to edit view
