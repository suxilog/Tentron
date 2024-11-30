from django.conf import settings
from django.conf.urls.i18n import i18n_patterns
from django.contrib import admin
from django.shortcuts import get_object_or_404
from django.urls import include, path
from django.views import defaults as default_views
from wagtail import urls as wagtail_urls
from wagtail.admin import urls as wagtailadmin_urls
from wagtail.admin.views.pages.create import CreateView
from wagtail.admin.views.pages.edit import EditView
from wagtail.contrib.sitemaps.views import sitemap
from wagtail.documents import urls as wagtaildocs_urls
from wagtail.models import Page

from core.views import (
    TentronFormPagesListView,
    add_subpage,
    autocomplete,
    kindly_404,
    product_type,
)
from grapejs.models import CustomPage
from grapejs.views import CustomPageCreateView, CustomPageEditView
from organization.search import search as organization_search
from organization.views import edit as settings_edit
from organization.views import manage_users
from organization.views import (
    redirect_to_relevant_instance as settings_redirect_to_relevant_instance,
)
from organization.views import robotstxt
from search import views as search_views


def page_create_view(
    request, content_type_app_name, content_type_model_name, parent_page_id
):

    if content_type_model_name == "custompage":
        print("CustomPage")
        return CustomPageCreateView.as_view()(
            request, content_type_app_name, content_type_model_name, parent_page_id
        )
    else:
        print("page_create_view")

        return CreateView.as_view()(
            request, content_type_app_name, content_type_model_name, parent_page_id
        )


def page_edit_view(request, page_id):

    page = get_object_or_404(Page.objects.prefetch_workflow_states(), id=page_id)
    if isinstance(page.specific, CustomPage):
        print("CustomPage")
        return CustomPageEditView.as_view()(request, page_id)
    else:
        print("page_edit_view")
        return EditView.as_view()(request, page_id)


urlpatterns = [
    path(
        "tadmin/forms/", TentronFormPagesListView.as_view(), name="form_pages_list_view"
    ),
    path(
        "tadmin/settings/<slug:app_name>/<slug:model_name>/<int:pk>/",
        settings_edit,
        name="wagtailsettings_edit",
    ),
    path(
        "tadmin/settings/<slug:app_name>/<slug:model_name>/",
        settings_redirect_to_relevant_instance,
        name="wagtailsettings_edit",
    ),
    path(
        "tadmin/pages/<int:parent_page_id>/add_subpage/",
        add_subpage,
        name="add_subpage",
    ),
    # http://dev.sufob.com/admin/pages/add/grapejs/grapejspage/4/
    path(
        "tadmin/pages/add/<str:content_type_app_name>/<str:content_type_model_name>/<int:parent_page_id>/",
        page_create_view,
        name="page_create_view",
    ),
    path("tadmin/pages/<int:page_id>/edit/", page_edit_view, name="page_edit_view"),
    # path("django-admin/", admin.site.urls),
    path("manage-users/", manage_users, name="manage_users"),
    path("documents/", include(wagtaildocs_urls)),
    path("grapesjs/", include("grapejs.urls")),
    path("product/category/<slug:slug>/", product_type, name="product_type"),
    path("robots.txt", robotstxt, name="robotstxt"),
    path("kindly-404/", kindly_404, name="kindly_404"),
    path(
        "tadmin/tag-autocomplete/", autocomplete, name="wagtailadmin_tag_autocomplete"
    ),
    path(
        "tadmin/tag-autocomplete/<slug:app_name>/<slug:model_name>/",
        autocomplete,
        name="wagtailadmin_tag_model_autocomplete",
    ),
    path("tadmin/pages/search/", organization_search, name="wagtailsearch_search"),
    path("tadmin/message/", include("message.urls", namespace="message")),
]
# Translatable URLs
# These will be available under a language code prefix. For example /en/search/
urlpatterns += i18n_patterns(
    path("tadmin/", include(wagtailadmin_urls)),
    path("search/", search_views.search, name="search"),
    path("sitemap.xml", sitemap),
    path("", include(wagtail_urls)),
    prefix_default_language=False,
)

if settings.DEBUG:
    import debug_toolbar
    from django.conf.urls.static import static
    from django.contrib.staticfiles.urls import staticfiles_urlpatterns

    urlpatterns = [
        path("__debug__/", include(debug_toolbar.urls)),
        path(
            "404/",
            default_views.page_not_found,
            kwargs={"exception": Exception("Page not Found")},
        ),
        path("500/", default_views.server_error),
    ] + urlpatterns

    # Serve static and media files from development server
    urlpatterns += staticfiles_urlpatterns()
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

urlpatterns = urlpatterns + [
    # For anything not caught by a more specific rule above, hand over to
    # Wagtail's page serving mechanism. This should be the last pattern in
    # the list:
    path("", include(wagtail_urls)),
    # Alternatively, if you want Wagtail pages to be served from a subpath
    # of your site, rather than the site root:
    #    path("pages/", include(wagtail_urls)),
]
