# Generated by Django 3.2.9 on 2021-12-15 06:07

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0003_auto_20211214_2207'),
    ]

    operations = [
        migrations.RenameField(
            model_name='product',
            old_name='color_size',
            new_name='color',
        ),
        migrations.AddField(
            model_name='product',
            name='size',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
    ]
