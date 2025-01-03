# Generated by Django 4.1.9 on 2023-06-10 06:46

from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import wagtail.blocks
import wagtail.fields


class Migration(migrations.Migration):

    dependencies = [
        ('wagtailimages', '0025_alter_image_file_alter_rendition_file'),
        ('wagtailcore', '0083_workflowcontenttype'),
        ('core', '0004_alter_contactpage_sub_title'),
    ]

    operations = [
        migrations.RenameField(
            model_name='teamdetailpage',
            old_name='body',
            new_name='content',
        ),
        migrations.AddField(
            model_name='teamdetailpage',
            name='address',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='teamdetailpage',
            name='designation',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='teamdetailpage',
            name='email',
            field=models.EmailField(blank=True, max_length=254, null=True),
        ),
        migrations.AddField(
            model_name='teamdetailpage',
            name='image',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to='wagtailimages.image'),
        ),
        migrations.AddField(
            model_name='teamdetailpage',
            name='name',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='teamdetailpage',
            name='phone',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='teamdetailpage',
            name='social',
            field=wagtail.fields.StreamField([('socials', wagtail.blocks.StructBlock([('social_name', wagtail.blocks.CharBlock(required=False)), ('social_link', wagtail.blocks.CharBlock(required=True)), ('icon', wagtail.blocks.CharBlock(default='fa fa-facebook', help_text='Font Awesome Icon', required=True))]))], blank=True, null=True, use_json_field=True),
        ),
        migrations.CreateModel(
            name='TestimonialItem',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('deleted_at', models.DateTimeField(blank=True, default=None, null=True)),
                ('name', models.CharField(max_length=255)),
                ('content', wagtail.fields.RichTextField()),
                ('position', models.CharField(max_length=255)),
                ('company', models.CharField(max_length=255)),
                ('image', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to='wagtailimages.image')),
                ('site', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='wagtailcore.site')),
            ],
            options={
                'abstract': False,
            },
        ),
    ]
