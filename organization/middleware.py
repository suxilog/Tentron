import logging

from django.core.exceptions import ObjectDoesNotExist
from django.shortcuts import redirect, render

from organization.models import ExtendedSite, Site

logger = logging.getLogger("tentron")


class ExtendedSiteMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_superuser:
            return self.get_response(request)
        current_site = Site.find_for_request(request)
        # get referrer info
        referrer = request.META.get("HTTP_REFERER", None)
        domain = request.get_host()
        try:
            e_site = ExtendedSite.objects.get(site=current_site)
            # if organization active_status is False, redirect to the default site
            if not e_site.organization.active_status:
                logger.debug(
                    "Organization is inactive or expired for %s, redirecting to subscription page",
                    request.get_host(),
                )
                return render(
                    request,
                    "core/subscription.html",
                    {"referrer": referrer, "domain": domain},
                    status=404,
                )

        except ObjectDoesNotExist:
            # if dashboard url, redirect to the default site
            logger.debug(
                "Extended Site not found for %s, redirecting to default site",
                request.get_host(),
            )
            if request.path.startswith("/tadmin/"):
                return self.get_response(request)

            return render(
                request,
                "core/kindly_404.html",
                {"referrer": referrer, "domain": domain},
                status=404,
            )

        response = self.get_response(request)
        return response
