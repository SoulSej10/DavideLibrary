# Generated by Django 5.0.6 on 2024-09-17 14:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('library', '0020_customuser_role'),
    ]

    operations = [
        migrations.AlterField(
            model_name='customuser',
            name='password',
            field=models.CharField(max_length=128, verbose_name='password'),
        ),
    ]
