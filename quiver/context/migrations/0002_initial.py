# Generated by Django 3.2.8 on 2022-11-17 07:26

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('projects', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('context', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='historicalcanvasmembers',
            name='history_user',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='historicalcanvasmembers',
            name='user_id',
            field=models.ForeignKey(blank=True, db_constraint=False, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='canvastask',
            name='canvas',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='canvas_task', to='context.canvas'),
        ),
        migrations.AddField(
            model_name='canvasshare',
            name='canvas',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='context.canvas'),
        ),
        migrations.AddField(
            model_name='canvasshare',
            name='receiver',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='canvas_receiver', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='canvasshare',
            name='sender',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='canvasnotification',
            name='action_user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='canvas_action_user', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='canvasnotification',
            name='canvas',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='context.canvas'),
        ),
        migrations.AddField(
            model_name='canvasnotification',
            name='comment',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='context.canvascomments'),
        ),
        migrations.AddField(
            model_name='canvasnotification',
            name='org_user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='canvasnotification',
            name='product',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='projects.projects'),
        ),
        migrations.AddField(
            model_name='canvasnotification',
            name='reply',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='context.canvascommentsreply'),
        ),
        migrations.AddField(
            model_name='canvasnotes',
            name='canvas_task',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='canvas_not', to='context.canvastask'),
        ),
        migrations.AddField(
            model_name='canvasnotes',
            name='created_by',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='canvasnotes',
            name='priority',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='priority', to='context.priority'),
        ),
        migrations.AddField(
            model_name='canvasmembers',
            name='canvas',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='context.canvas'),
        ),
        migrations.AddField(
            model_name='canvasmembers',
            name='user_id',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='canvascommentsreply',
            name='canvas_comment',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='reply', to='context.canvascomments'),
        ),
        migrations.AddField(
            model_name='canvascommentsreply',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='canvascomments',
            name='canvas',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='context.canvas'),
        ),
        migrations.AddField(
            model_name='canvascomments',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='canvas',
            name='canvas_type',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='context.canvastype'),
        ),
        migrations.AddField(
            model_name='canvas',
            name='created_by',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='canvas',
            name='project',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='projects.projects'),
        ),
    ]
