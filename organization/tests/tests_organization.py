from django.contrib.auth.models import Group, Permission
from django.test import TestCase
from wagtail.models import Page, Site

from ..models import ExtendedSite, OrganizationRootPage
from .factories import (
    OrganizationFactory,
    OrganizationRootPageFactory,
    SiteFactory,
    UserFactory,
)


class BasePageTestCase(TestCase):
    def setUp(self):
        self.organization = OrganizationFactory()

        self.organization_group = Group.objects.get(
            name=self.organization.lower_name + " admins"
        )

        self.user_is_superuser = UserFactory(is_superuser=True)
        self.user_with_access = self.organization_group.user_set.first()
        self.user_without_access = UserFactory(groups=["users"])

        self.organization_root_page = OrganizationRootPage.objects.get(
            title=self.organization.lower_name + " root"
        )

    def test_user_can_view(self):
        self.assertTrue(
            self.organization_root_page.user_can_view(self.user_is_superuser)
        )
        self.assertTrue(
            self.organization_root_page.user_can_view(self.user_with_access)
        )
        self.assertFalse(
            self.organization_root_page.user_can_view(self.user_without_access)
        )
