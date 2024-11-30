from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend
from django.core.exceptions import ObjectDoesNotExist
from wagtail.models import Site


class DomainBasedModelBackend(ModelBackend):
    def user_has_domain_access(self, user, request):
        if user.is_authenticated:
            print("user is authenticated")
            try:

                current_site = Site.find_for_request(request)
                if (
                    current_site
                    and current_site.extendedsite.organization
                    in user.organizations.all()
                ):
                    return True
            except ObjectDoesNotExist as e:
                print(e)
        return False

    def authenticate(self, request, username=None, password=None, **kwargs):
        user = super().authenticate(request, username, password, **kwargs)
        if user:
            if user.is_superuser:
                return user
            if self.user_has_domain_access(user, request):
                return user
            else:
                messages.error(request, "You do not have access to this organization.")
        return None
