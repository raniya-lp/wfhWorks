# Generated by Django 3.2.8 on 2022-11-17 07:26

from django.db import migrations, models
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='ApiCallDetails',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('latency', models.FloatField()),
                ('error_status', models.BooleanField()),
                ('status_message', models.TextField()),
                ('processed_at', models.DateTimeField(auto_now_add=True)),
                ('ip_address', models.CharField(blank=True, max_length=250, null=True)),
                ('system_name', models.CharField(blank=True, max_length=250, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='ApiDetails',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('api_name', models.CharField(max_length=250)),
            ],
        ),
        migrations.CreateModel(
            name='ApiNotification',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True, null=True)),
                ('updated_at', models.DateTimeField(auto_now=True, null=True)),
                ('action_type', models.CharField(choices=[('create', 'Create'), ('update', 'Update'), ('delete', 'Delete'), ('comment', 'Comment'), ('reply', 'Reply'), ('Product_create', 'product_create'), ('Product_update', 'product_update')], max_length=100)),
                ('action_status', models.CharField(choices=[('seen', 'Seen'), ('unseen', 'Useen')], default='unseen', max_length=100)),
                ('higlight_status', models.CharField(choices=[('seen', 'Seen'), ('unseen', 'Useen')], default='unseen', max_length=100)),
            ],
            options={
                'abstract': False,
            },
        ),
    ]
