# Generated by Django 4.2.11 on 2024-05-18 15:59

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('jobs', '0015_remove_notification_is_read_remove_notification_user_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='recruitmentpost',
            name='area',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.RESTRICT, to='jobs.area'),
        ),
    ]