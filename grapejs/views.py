import json

from django.contrib.auth.models import Group
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from wagtail.admin.views.pages.create import CreateView
from wagtail.admin.views.pages.edit import EditView
from wagtail.documents.models import Document
from wagtail.images.models import Image
from wagtail.images.views.serve import generate_image_url
from wagtail.models import Site

from organization.models import ExtendedSite, Organization

from .models import CustomPage


@csrf_exempt
def save(request, page_id):
    if request.method == "POST":
        # make sure request.body is json
        data = json.loads(request.body)

        page = CustomPage.objects.get(id=page_id)
        html_css_data = data.get("pagesHtml")
        page.html_content = html_css_data[0]["html"]
        page.css_content = html_css_data[0]["css"]
        page.json_content = data.get("data")
        page.save()
        return JsonResponse({"status": "ok"})


def load(request, page_id):
    try:

        page = CustomPage.objects.get(id=page_id)
    except CustomPage.DoesNotExist:
        return JsonResponse({"data": {}})
    return JsonResponse({"data": page.json_content})


def load_assets(request):
    # find request user and filter images and documents by user organization collection
    # if request user is not authenticated, return empty list

    req_user = request.user
    if not req_user.is_authenticated:
        return JsonResponse({"data": {}})
    current_site = Site.find_for_request(request)
    extended_site = ExtendedSite.objects.filter(site=current_site).first()
    if extended_site is None:
        return JsonResponse({"data": {}})

    organization = extended_site.organization

    # Make sure the user is a member of the organization
    if organization not in req_user.organizations.all():
        return JsonResponse({"data": {}})
    collection = organization.collection
    images = Image.objects.filter(collection=collection)

    assets = [
        {
            "type": "image",
            "src": image.file.url,
            "id": image.id,
            "width": image.width,
            "height": image.height,
            "name": image.title,
        }
        for image in images
    ]

    return JsonResponse(assets, safe=False)


def upload_asset(request):
    # 请根据您的需求实现文件上传功能。
    pass


def delete_asset(request):
    # 请根据您的需求实现文件删除功能。
    pass


def search_assets(request):
    # 请根据您的需求实现文件搜索功能。
    pass


class CustomPageCreateView(CreateView):
    template_name = "grapejs/create.html"


class CustomPageEditView(EditView):
    def get_template_names(self):
        return ["grapejs/edit.html"]
