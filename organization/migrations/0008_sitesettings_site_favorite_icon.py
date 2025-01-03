# Generated by Django 4.1.9 on 2023-06-08 14:57

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('wagtailimages', '0025_alter_image_file_alter_rendition_file'),
        ('organization', '0007_sitesettings_contact_address_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='sitesettings',
            name='site_favorite_icon',
            field=models.ForeignKey(blank=True, help_text='The favorite icon of the site.', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to='wagtailimages.image'),
        ),
    ]
