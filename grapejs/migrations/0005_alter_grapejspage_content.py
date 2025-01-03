# Generated by Django 4.1.8 on 2023-05-11 05:44

from django.db import migrations
import wagtail.blocks
import wagtail.fields


class Migration(migrations.Migration):

    dependencies = [
        ('grapejs', '0004_grapejspage_content_alter_grapejspage_json_content'),
    ]

    operations = [
        migrations.AlterField(
            model_name='grapejspage',
            name='content',
            field=wagtail.fields.StreamField([('custom_page_block', wagtail.blocks.StructBlock([('json_content', wagtail.blocks.TextBlock(required=False))]))], blank=True, use_json_field=True),
        ),
    ]
