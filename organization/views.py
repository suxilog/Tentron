# organizations/views.py

import queue
from functools import lru_cache
from typing import Optional

from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist, PermissionDenied
from django.db import transaction
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.response import TemplateResponse
from django.utils.text import capfirst
from django.utils.translation import gettext as _
from django.views.decorators.http import require_GET
from wagtail.admin import messages
from wagtail.admin.panels import (
    ObjectList,
    TabbedInterface,
    extract_panel_definitions_from_model_class,
)
from wagtail.contrib.modeladmin.views import (
    CreateView,
    EditView,
    ModelFormView,
    WMABaseView,
)
from wagtail.contrib.settings.forms import SiteSwitchForm
from wagtail.contrib.settings.models import BaseGenericSetting, BaseSiteSetting
from wagtail.contrib.settings.permissions import user_can_edit_setting_type
from wagtail.contrib.settings.registry import registry
from wagtail.log_actions import log
from wagtail.models import Site

from .models import ExtendedSite, SiteSettings


@login_required
@user_passes_test(lambda user: user.groups.filter(name__icontains="Admins").exists())
def manage_users(request):
    site = ExtendedSite.find_for_request(request)
    organization = site.organization
    admin_group = organization.admin_group

    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            user.groups.add(admin_group)
            user.save()
            return redirect("manage_users")
    else:
        form = UserCreationForm()

    users = User.objects.filter(groups=admin_group)
    context = {"form": form, "users": users, "organization": organization}
    return render(request, "organizations/manage_users.html", context)


def get_model_from_url_params(app_name, model_name):
    """
    retrieve a content type from an app_name / model_name combo.
    Throw Http404 if not a valid setting type
    """
    model = registry.get_by_natural_key(app_name, model_name)
    if model is None:
        raise Http404
    return model


@lru_cache()
def get_setting_edit_handler(model):
    if hasattr(model, "edit_handler"):
        edit_handler = model.edit_handler
    else:
        if issubclass(model, BaseSiteSetting):
            panels = extract_panel_definitions_from_model_class(model, ["site"])
        elif issubclass(model, BaseGenericSetting):
            panels = extract_panel_definitions_from_model_class(model)
        else:
            raise NotImplementedError

        edit_handler = ObjectList(panels)
    return edit_handler.bind_to_model(model)


def redirect_to_relevant_instance(request, app_name, model_name):
    model = get_model_from_url_params(app_name, model_name)
    if issubclass(model, BaseSiteSetting):
        # Redirect the user to the edit page for the current site
        # (or the current request does not correspond to a site, the first site in the list)
        site_request = Site.find_for_request(request)
        site = site_request or Site.objects.first()
        if not site:
            messages.error(
                request,
                _("This setting could not be opened because there is no site defined."),
            )
            return redirect("wagtailadmin_home")
        return redirect(
            "wagtailsettings_edit",
            app_name,
            model_name,
            site.pk,
        )
    elif issubclass(model, BaseGenericSetting):
        return redirect(
            "wagtailsettings_edit",
            app_name,
            model_name,
            model.load(request_or_site=request).id,
        )
    else:
        raise NotImplementedError


def edit(request, app_name, model_name, pk):
    model = get_model_from_url_params(app_name, model_name)
    if not user_can_edit_setting_type(request.user, model):
        raise PermissionDenied

    setting_type_name = model._meta.verbose_name
    edit_handler = get_setting_edit_handler(model)
    form_class = edit_handler.get_form_class()
    site: Optional[Site] = None
    site_switcher = None

    if issubclass(model, BaseSiteSetting):
        site = get_object_or_404(Site, pk=pk)
        form_id = site.pk
        instance = model.for_site(site)

        if request.method == "POST":
            form = form_class(
                request.POST, request.FILES, instance=instance, for_user=request.user
            )

            if form.is_valid():
                with transaction.atomic():
                    form.save()
                    log(instance, "wagtail.edit")

                messages.success(
                    request,
                    _("%(setting_type)s updated.")
                    % {
                        "setting_type": capfirst(setting_type_name),
                        "instance": instance,
                    },
                )
                return redirect("wagtailsettings_edit", app_name, model_name, site.pk)
            else:
                messages.validation_error(
                    request, _("The setting could not be saved due to errors."), form
                )
        else:
            form = form_class(instance=instance, for_user=request.user)

        edit_handler = edit_handler.get_bound_panel(
            instance=instance, request=request, form=form
        )

        media = form.media + edit_handler.media

        # Show a site switcher form if there are multiple sites
        if Site.objects.count() > 1:
            site_switcher = SiteSwitchForm(site, model)
            media += site_switcher.media

    elif issubclass(model, BaseGenericSetting):
        queryset = model.base_queryset()

        # Create the instance if we haven't already.
        if queryset.count() == 0:
            model.objects.create()

        instance = get_object_or_404(model, pk=pk)
        form_id = instance.pk

        if request.method == "POST":
            form = form_class(
                request.POST, request.FILES, instance=instance, for_user=request.user
            )

            if form.is_valid():
                with transaction.atomic():
                    form.save()
                    log(instance, "wagtail.edit")

                messages.success(
                    request,
                    _("%(setting_type)s updated.")
                    % {
                        "setting_type": capfirst(setting_type_name),
                        "instance": instance,
                    },
                )
                return redirect("wagtailsettings_edit", app_name, model_name)
            else:
                messages.validation_error(
                    request, _("The setting could not be saved due to errors."), form
                )
        else:
            form = form_class(instance=instance, for_user=request.user)

        edit_handler = edit_handler.get_bound_panel(
            instance=instance, request=request, form=form
        )

        media = form.media + edit_handler.media

    else:
        raise NotImplementedError
    # permission helper
    permission_access = False
    try:

        organization = site.extendedsite.organization
        # check if user in organization.memberships.all()
        if (
            organization.memberships.filter(user=request.user).exists()
            or request.user.is_superuser
        ):
            permission_access = True
    except Exception as e:

        permission_access = False
        if request.user.is_superuser:
            permission_access = True

    if not permission_access:
        raise PermissionDenied

    return TemplateResponse(
        request,
        "wagtailsettings/edit.html",
        {
            "opts": model._meta,
            "setting_type_name": setting_type_name,
            "instance": instance,
            "edit_handler": edit_handler,
            "form": form,
            "site": site,
            "site_switcher": site_switcher,
            "tabbed": isinstance(edit_handler.panel, TabbedInterface),
            "media": media,
            "form_id": form_id,
        },
    )


class SiteSettingsIndexView(WMABaseView):
    def dispatch(self, request, *args, **kwargs):
        site = Site.find_for_request(request)
        # get site site_settings, if not exist create one
        site_settings = SiteSettings.for_site(site)
        return redirect(
            self.url_helper.get_action_url("edit", site_settings.id)
        )  # redirect to edit view


@require_GET
def robotstxt(request):
    site = Site.find_for_request(request)
    site_settings = SiteSettings.for_site(site)
    # get site setting robots.txt
    robots_txt = site_settings.robots_txt
    return HttpResponse(robots_txt, content_type="text/plain")
