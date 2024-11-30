from django.urls import path

from . import views

urlpatterns = [
    path("<int:page_id>/save/", views.save, name="grapejs_save"),
    path("<int:page_id>/load/", views.load, name="grapejs_load"),
    path("load_assets/", views.load_assets, name="grapejs_load_assets"),
    path("upload_asset/", views.upload_asset, name="grapejs_upload_asset"),
    path("delete_asset/", views.delete_asset, name="grapejs_delete_asset"),
    path("search_assets/", views.search_assets, name="grapejs_search_assets"),
]
