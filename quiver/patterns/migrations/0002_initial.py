# Generated by Django 3.2.8 on 2022-11-17 07:26

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('patterns', '0001_initial'),
        ('projects', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='pattershare',
            name='receiver',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='receiver', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='pattershare',
            name='sender',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='patternsubsection',
            name='pattern_section',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='patterns.patternsection'),
        ),
        migrations.AddField(
            model_name='patternsectioncollection',
            name='pattern_section',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='patterns.patternsection'),
        ),
        migrations.AddField(
            model_name='patternsectioncollection',
            name='pattern_sub_section',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='patterns.patternsubsection'),
        ),
        migrations.AddField(
            model_name='patternsection',
            name='pattern',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='patterns.pattern'),
        ),
        migrations.AddField(
            model_name='patternnotification',
            name='action_user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='action_user', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='patternnotification',
            name='comment',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='patterns.pattercomments'),
        ),
        migrations.AddField(
            model_name='patternnotification',
            name='org_user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='patternnotification',
            name='pattern',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='patterns.pattern'),
        ),
        migrations.AddField(
            model_name='patternnotification',
            name='product',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='projects.projects'),
        ),
        migrations.AddField(
            model_name='patternnotification',
            name='reply',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='patterns.pattercommentsreply'),
        ),
        migrations.AddField(
            model_name='pattern',
            name='created_by',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='pattern',
            name='project',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='projects.projects'),
        ),
        migrations.AddField(
            model_name='pattercommentsreply',
            name='pattern_comment',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='reply', to='patterns.pattercomments'),
        ),
        migrations.AddField(
            model_name='pattercommentsreply',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='pattercomments',
            name='pattern',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='patterns.pattern'),
        ),
        migrations.AddField(
            model_name='pattercomments',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='historicalpattern',
            name='created_by',
            field=models.ForeignKey(blank=True, db_constraint=False, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='historicalpattern',
            name='history_user',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='historicalpattern',
            name='project',
            field=models.ForeignKey(blank=True, db_constraint=False, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to='projects.projects'),
        ),
        migrations.AddField(
            model_name='historicalpattercommentsreply',
            name='history_user',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='historicalpattercommentsreply',
            name='pattern_comment',
            field=models.ForeignKey(blank=True, db_constraint=False, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to='patterns.pattercomments'),
        ),
        migrations.AddField(
            model_name='historicalpattercommentsreply',
            name='user',
            field=models.ForeignKey(blank=True, db_constraint=False, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='historicalpattercomments',
            name='history_user',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='historicalpattercomments',
            name='pattern',
            field=models.ForeignKey(blank=True, db_constraint=False, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to='patterns.pattern'),
        ),
        migrations.AddField(
            model_name='historicalpattercomments',
            name='user',
            field=models.ForeignKey(blank=True, db_constraint=False, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to=settings.AUTH_USER_MODEL),
        ),
    ]