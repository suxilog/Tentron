from wagtail.images.apps import WagtailImagesAppConfig


# lazy load image
class CustomImagesAppConfig(WagtailImagesAppConfig):
    default_attrs = {"decoding": "async", "loading": "lazy"}
