# Generated by Django 3.2.8 on 2022-11-17 07:26

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('blueprint', '0001_initial'),
        ('projects', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='sections',
            name='created_by',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='historicalblueprint',
            name='created_by',
            field=models.ForeignKey(blank=True, db_constraint=False, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='historicalblueprint',
            name='history_user',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='historicalblueprint',
            name='project',
            field=models.ForeignKey(blank=True, db_constraint=False, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to='projects.projects'),
        ),
        migrations.AddField(
            model_name='historicalblueprint',
            name='updated_by',
            field=models.ForeignKey(blank=True, db_constraint=False, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='blueprintshare',
            name='blueprint',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='blueprint.blueprint'),
        ),
        migrations.AddField(
            model_name='blueprintshare',
            name='receiver',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='blueprint_receiver', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='blueprintshare',
            name='sender',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='blueprintnotification',
            name='action_user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='blueprint_action_user', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='blueprintnotification',
            name='blueprint',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='blueprint.blueprint'),
        ),
        migrations.AddField(
            model_name='blueprintnotification',
            name='comment',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='blueprint.blueprintcomments'),
        ),
        migrations.AddField(
            model_name='blueprintnotification',
            name='org_user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='blueprintnotification',
            name='product',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='projects.projects'),
        ),
        migrations.AddField(
            model_name='blueprintnotification',
            name='reply',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='blueprint.blueprintcommentsreply'),
        ),
        migrations.AddField(
            model_name='blueprintcommentsreply',
            name='blueprint_comment',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='reply', to='blueprint.blueprintcomments'),
        ),
        migrations.AddField(
            model_name='blueprintcommentsreply',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='blueprintcomments',
            name='blueprint',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='blueprint.blueprint'),
        ),
        migrations.AddField(
            model_name='blueprintcomments',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='blueprint',
            name='created_by',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='blueprint',
            name='project',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='projects.projects'),
        ),
        migrations.AddField(
            model_name='blueprint',
            name='updated_by',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='updated_user', to=settings.AUTH_USER_MODEL),
        ),
    ]
