from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.response import TemplateResponse
from taggit.models import Tag, TagBase
from wagtail import hooks
from wagtail.admin.utils import get_valid_next_url_from_request
from wagtail.admin.views.generic.chooser import ChooseResultsView, ChooseView
from wagtail.admin.viewsets.chooser import ChooserViewSet
from wagtail.contrib.forms.views import FormPagesListView
from wagtail.contrib.modeladmin.views import IndexView, WMABaseView
from wagtail.models import Locale, Page, Site

from organization.models import SiteSettings

from .models import FaqPage, ProductPage, ProductType

# def homepage(request):
#     try:
#         site = Site.find_for_request(request)
#         print("site", site)

#         site_settings = SiteSettings.for_site(site)
#         template_folder = site_settings.site_settings_theme.first().template_folder
#         print("template_folder", template_folder)

#         return render(request, f"{template_folder}/index.html", {"site": site})
#     except Exception as e:
#         print("error", e)
#         return render(request, "default/homepage.html")


def add_subpage(request, parent_page_id):
    parent_page = get_object_or_404(Page, id=parent_page_id).specific
    if not parent_page.permissions_for_user(request.user).can_add_subpage():
        raise PermissionDenied

    current_site = Site.find_for_request(request)
    # current_organization = current_site.extendedsite.organization
    page_types = [
        (
            model.get_verbose_name(),
            model._meta.app_label,
            model._meta.model_name,
            model.get_page_description(),
        )
        for model in type(parent_page).creatable_subpage_models()
        if model.can_create_at(parent_page)
        and model.can_create_for_site(request.user, current_site)
    ]
    # sort by lower-cased version of verbose name
    page_types.sort(key=lambda page_type: page_type[0].lower())
    # if organizationrootpage in page_types, delete it.
    page_types = [item for item in page_types if "organizationrootpage" not in item]
    if len(page_types) == 1:
        # Only one page type is available - redirect straight to the create form rather than
        # making the user choose
        verbose_name, app_label, model_name, description = page_types[0]
        return redirect("wagtailadmin_pages:add", app_label, model_name, parent_page.id)
    # Base on the organization of the request site and user, we will filter the page_types by the organization and max_count_per_site

    return TemplateResponse(
        request,
        "wagtailadmin/pages/add_subpage.html",
        {
            "parent_page": parent_page,
            "page_types": page_types,
            "next": get_valid_next_url_from_request(request),
        },
    )


def product_type(request, slug):
    site = Site.find_for_request(request)
    category = get_object_or_404(ProductType, slug=slug)
    products = ProductPage.objects.filter(
        product_types__type__in=[category], site=site
    ).specific()
    site_settings = SiteSettings.for_site(site)
    template_folder = site_settings.site_settings_theme.first().template_folder
    paginator = Paginator(products, 2)

    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    return render(
        request,
        f"{template_folder}/product.html",
        {"category": category, "page_obj": page_obj},
    )


class TentronFormPagesListView(FormPagesListView):
    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(object_list=object_list, **kwargs)
        return context


def kindly_404(request):
    return render(request, "core/kindly_404.html", status=404)


def autocomplete(request, app_name=None, model_name=None):
    print("autocomplete")
    site = Site.find_for_request(request)
    print("site", site)
    if app_name and model_name:
        try:
            content_type = ContentType.objects.get_by_natural_key(app_name, model_name)
        except ContentType.DoesNotExist:
            raise Http404

        tag_model = content_type.model_class()
        if not issubclass(tag_model, TagBase):
            raise Http404

    else:
        tag_model = Tag

    term = request.GET.get("term", None)
    if term:
        tags = tag_model.objects.filter(name__istartswith=term, site=site).order_by(
            "name"
        )
        if request.user.is_superuser:
            tags = tag_model.objects.filter(name__istartswith=term).order_by("name")

    else:
        tags = tag_model.objects.none()

    return JsonResponse([tag.name for tag in tags], safe=False)


class FaqPageIndexView(IndexView):
    def dispatch(self, request, *args, **kwargs):
        if request.user.is_superuser:
            return super().dispatch(request, *args, **kwargs)
        site = Site.find_for_request(request)
        # get site site_settings, if not exist create one
        faq_page = FaqPage.objects.filter(site=site).first()
        return redirect(
            self.url_helper.get_action_url("edit", faq_page.id)
        )  # redirect to edit view
