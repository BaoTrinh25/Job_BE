# Generated by Django 4.2.11 on 2024-09-15 14:02

import cloudinary.models
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('jobs', '0027_usergoogle'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='jobapplication',
            options={'ordering': ['date', 'id']},
        ),
        migrations.RenameField(
            model_name='company',
            old_name='position',
            new_name='total_staff',
        ),
        migrations.RemoveField(
            model_name='job',
            name='reported',
        ),
        migrations.AddField(
            model_name='company',
            name='logo',
            field=cloudinary.models.CloudinaryField(blank=True, max_length=255, null=True, verbose_name='logo'),
        ),
        migrations.AddField(
            model_name='jobapplication',
            name='company',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='jobs.company'),
        ),
        migrations.AddField(
            model_name='jobapplication',
            name='user',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='jobseeker',
            name='applied_job',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='jobseekers', to='jobs.job'),
        ),
        migrations.AlterField(
            model_name='career',
            name='name',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='employmenttype',
            name='type',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AlterField(
            model_name='job',
            name='gender',
            field=models.IntegerField(blank=True, choices=[(0, 'Male'), (1, 'Female'), (2, 'N/A')], default=0, null=True),
        ),
        migrations.AlterField(
            model_name='jobapplication',
            name='jobseeker',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='jobs.jobseeker'),
        ),
        migrations.AlterField(
            model_name='status',
            name='role',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='user',
            name='gender',
            field=models.IntegerField(blank=True, choices=[(0, 'Male'), (1, 'Female'), (2, 'N/A')], null=True),
        ),
        migrations.DeleteModel(
            name='UserGoogle',
        ),
    ]
