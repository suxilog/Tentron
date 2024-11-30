# Generated by Django 4.1.9 on 2023-06-10 08:16

from django.db import migrations
import wagtail.blocks
import wagtail.fields
import wagtailmodelchooser.blocks


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0006_alter_teamdetailpage_social'),
    ]

    operations = [
        migrations.AddField(
            model_name='aboutpage',
            name='content',
            field=wagtail.fields.StreamField([('testimonials', wagtail.blocks.ListBlock(wagtailmodelchooser.blocks.ModelChooserBlock(target_model='core.testimonialitem')))], blank=True, null=True, use_json_field=True),
        ),
    ]