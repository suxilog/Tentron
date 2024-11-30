# Generated by Django 4.1.9 on 2023-06-16 07:17

from django.db import migrations
import wagtail.fields
import wagtailmodelchooser.blocks


class Migration(migrations.Migration):

    dependencies = [
        ('organization', '0010_footermenu'),
    ]

    operations = [
        migrations.AlterField(
            model_name='footermenu',
            name='footer_menu',
            field=wagtail.fields.StreamField([('column', wagtailmodelchooser.blocks.ModelChooserBlock(target_model='organization_menu.organizationflatmenu'))], blank=True, help_text='The footer menu of the site, you need add footer menu items first.', null=True, use_json_field=True),
        ),
    ]