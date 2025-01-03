# Generated by Django 4.1.9 on 2023-06-13 13:48

from django.db import migrations
import wagtail.blocks
import wagtail.fields
import wagtail.images.blocks


class Migration(migrations.Migration):

    dependencies = [
        ('home', '0003_homepage_breadcrumb_background_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='homepage',
            name='content',
            field=wagtail.fields.StreamField([('default_slider', wagtail.blocks.StructBlock([('background', wagtail.images.blocks.ImageChooserBlock(required=True)), ('heading', wagtail.blocks.CharBlock(required=False)), ('subheading', wagtail.blocks.CharBlock(required=False)), ('context', wagtail.blocks.RichTextBlock(required=False)), ('button_text', wagtail.blocks.CharBlock(required=False)), ('button_link', wagtail.blocks.CharBlock(required=False))])), ('swiper_slider', wagtail.blocks.StructBlock([('sliders', wagtail.blocks.ListBlock(wagtail.blocks.StructBlock([('background', wagtail.images.blocks.ImageChooserBlock(required=True)), ('heading', wagtail.blocks.CharBlock(required=False)), ('subheading', wagtail.blocks.CharBlock(required=False)), ('context', wagtail.blocks.RichTextBlock(required=False)), ('button_text', wagtail.blocks.CharBlock(required=False)), ('button_link', wagtail.blocks.CharBlock(required=False)), ('slider_type', wagtail.blocks.ChoiceBlock(choices=[('default', 'Default'), ('swiper', 'Swiper')]))])))]))], blank=True, null=True, use_json_field=True),
        ),
    ]
