"""
Add current_plan field to User model
"""
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0001_initial'),
        ('plans', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='current_plan',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='subscribed_users',
                to='plans.plan',
                help_text='User\'s current locked plan. Can only be changed by admin.'
            ),
        ),
        migrations.AddField(
            model_name='user',
            name='plan_change_requested',
            field=models.BooleanField(
                default=False,
                help_text='User has requested a plan change'
            ),
        ),
        migrations.AddField(
            model_name='user',
            name='plan_change_requested_at',
            field=models.DateTimeField(
                blank=True,
                null=True
            ),
        ),
    ]
