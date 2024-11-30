import factory
import wagtail_factories
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import Group
from factory.django import DjangoModelFactory
from wagtail.documents import get_document_model
from wagtail.images import get_image_model
from wagtail.images.models import Image
from wagtail.models import Collection, Page, Site

from organization.models import BasePage, Organization, OrganizationRootPage

User = get_user_model()


class PageFactory(DjangoModelFactory):
    title = factory.Sequence(lambda n: f"Page {n}")

    class Meta:
        model = Page


class SiteFactory(DjangoModelFactory):
    hostname = factory.Sequence(lambda n: f"tentron{n}.localhost")
    port = factory.Sequence(lambda n: 81 + n)
    root_page = factory.SubFactory(PageFactory)
    is_default_site = False
    site_name = factory.Sequence(lambda n: f"tentron{n} Site")

    class Meta:
        model = Site


class UserFactory(DjangoModelFactory):
    username = factory.Sequence(lambda n: f"user{n}")
    password = factory.LazyFunction(lambda: make_password("password"))
    is_superuser = False

    @factory.post_generation
    def groups(self, create, extracted, **kwargs):
        if not create:
            return
        if extracted:
            for group_name in extracted:
                self.groups.add(Group.objects.get_or_create(name=group_name)[0])

    class Meta:
        model = User


class OrganizationRootPageFactory(DjangoModelFactory):
    site = factory.SubFactory(SiteFactory)
    title = "Tentrons root"
    breadcrumb_background = factory.SubFactory(wagtail_factories.ImageFactory)

    class Meta:
        model = OrganizationRootPage


class OrganizationFactory(DjangoModelFactory):
    name = factory.Sequence(lambda n: f"Tentron{n}")

    class Meta:
        model = Organization
