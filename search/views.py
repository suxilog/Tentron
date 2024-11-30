from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.template.response import TemplateResponse
from wagtail.models import Page, Site
from wagtail.search.models import Query

from organization.models import ExtendedSite, SiteSettings


def search(request):
    current_site = Site.find_for_request(request)

    site_settings = SiteSettings.for_site(current_site)
    template_folder = site_settings.site_settings_theme.first().template_folder

    template_name = f"{template_folder}/search.html"

    search_query = request.GET.get("query", None)
    page = request.GET.get("page", 1)

    # Search
    if search_query:
        search_results = Page.objects.live().search(search_query)
        query = Query.get(search_query)

        # Record hit
        query.add_hit()
    else:
        search_results = Page.objects.none()

    # Pagination
    paginator = Paginator(search_results, 10)
    try:
        search_results = paginator.page(page)
    except PageNotAnInteger:
        search_results = paginator.page(1)
    except EmptyPage:
        search_results = paginator.page(paginator.num_pages)

    return TemplateResponse(
        request,
        template_name,
        {
            "search_query": search_query,
            "search_results": search_results,
        },
    )
