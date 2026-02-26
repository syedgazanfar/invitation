"""
Initial migration for the AI app.

Creates the database tables for:
- PhotoAnalysis: Stores photo analysis results
- GeneratedMessage: Stores AI-generated messages
- AIUsageLog: Tracks API usage for rate limiting
"""

import uuid
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    """
    Initial migration that creates AI app models.
    """

    initial = True

    dependencies = [
        ('invitations', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='AIUsageLog',
            fields=[
                ('id', models.UUIDField(
                    default=uuid.uuid4,
                    editable=False,
                    primary_key=True,
                    serialize=False
                )),
                ('feature_type', models.CharField(
                    choices=[
                        ('photo_analysis', 'Photo Analysis'),
                        ('message_generation', 'Message Generation'),
                        ('template_recommendation', 'Template Recommendation'),
                        ('color_extraction', 'Color Extraction'),
                        ('mood_detection', 'Mood Detection'),
                        ('smart_suggestions', 'Smart Suggestions'),
                    ],
                    max_length=30
                )),
                ('request_data', models.JSONField(blank=True, default=dict)),
                ('response_data', models.JSONField(blank=True, default=dict)),
                ('tokens_used', models.PositiveIntegerField(default=0)),
                ('success', models.BooleanField(default=True)),
                ('error_message', models.TextField(blank=True)),
                ('processing_time_ms', models.PositiveIntegerField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('user', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='ai_usage_logs',
                    to=settings.AUTH_USER_MODEL
                )),
            ],
            options={
                'verbose_name': 'AI Usage Log',
                'verbose_name_plural': 'AI Usage Logs',
                'db_table': 'ai_usage_log',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='GeneratedMessage',
            fields=[
                ('id', models.UUIDField(
                    default=uuid.uuid4,
                    editable=False,
                    primary_key=True,
                    serialize=False
                )),
                ('context', models.JSONField(default=dict)),
                ('generated_options', models.JSONField(default=list)),
                ('style_used', models.CharField(
                    choices=[
                        ('romantic', 'Romantic'),
                        ('formal', 'Formal'),
                        ('casual', 'Casual'),
                        ('funny', 'Funny'),
                        ('poetic', 'Poetic'),
                        ('traditional', 'Traditional'),
                        ('modern', 'Modern'),
                    ],
                    default='romantic',
                    max_length=20
                )),
                ('tokens_used', models.PositiveIntegerField(default=0)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('event', models.ForeignKey(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='generated_messages',
                    to='invitations.order'
                )),
                ('user', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='generated_messages',
                    to=settings.AUTH_USER_MODEL
                )),
            ],
            options={
                'verbose_name': 'Generated Message',
                'verbose_name_plural': 'Generated Messages',
                'db_table': 'ai_generated_message',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='PhotoAnalysis',
            fields=[
                ('id', models.UUIDField(
                    default=uuid.uuid4,
                    editable=False,
                    primary_key=True,
                    serialize=False
                )),
                ('image_url', models.URLField(max_length=500)),
                ('primary_colors', models.JSONField(blank=True, default=dict)),
                ('mood', models.JSONField(blank=True, default=dict)),
                ('style_recommendations', models.JSONField(blank=True, default=list)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('event', models.ForeignKey(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='photo_analyses',
                    to='invitations.order'
                )),
                ('user', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='photo_analyses',
                    to=settings.AUTH_USER_MODEL
                )),
            ],
            options={
                'verbose_name': 'Photo Analysis',
                'verbose_name_plural': 'Photo Analyses',
                'db_table': 'ai_photo_analysis',
                'ordering': ['-created_at'],
            },
        ),
        migrations.AddIndex(
            model_name='aiusagelog',
            index=models.Index(fields=['user', '-created_at'], name='ai_usage_lo_user_id_4f8b95_idx'),
        ),
        migrations.AddIndex(
            model_name='aiusagelog',
            index=models.Index(fields=['feature_type', '-created_at'], name='ai_usage_lo_feature_5e6a40_idx'),
        ),
        migrations.AddIndex(
            model_name='aiusagelog',
            index=models.Index(fields=['success'], name='ai_usage_lo_success_3f8c9a_idx'),
        ),
        migrations.AddIndex(
            model_name='aiusagelog',
            index=models.Index(fields=['created_at'], name='ai_usage_lo_created_7d8e2b_idx'),
        ),
        migrations.AddIndex(
            model_name='generatedmessage',
            index=models.Index(fields=['user', '-created_at'], name='ai_generate_user_id_2a1b3c_idx'),
        ),
        migrations.AddIndex(
            model_name='generatedmessage',
            index=models.Index(fields=['event', '-created_at'], name='ai_generate_event_i_5d6e7f_idx'),
        ),
        migrations.AddIndex(
            model_name='generatedmessage',
            index=models.Index(fields=['style_used'], name='ai_generate_style_u_8g9h0i_idx'),
        ),
        migrations.AddIndex(
            model_name='generatedmessage',
            index=models.Index(fields=['created_at'], name='ai_generate_created_1j2k3l_idx'),
        ),
        migrations.AddIndex(
            model_name='photoanalysis',
            index=models.Index(fields=['user', '-created_at'], name='ai_photo_an_user_id_4m5n6o_idx'),
        ),
        migrations.AddIndex(
            model_name='photoanalysis',
            index=models.Index(fields=['event', '-created_at'], name='ai_photo_an_event_i_7p8q9r_idx'),
        ),
        migrations.AddIndex(
            model_name='photoanalysis',
            index=models.Index(fields=['created_at'], name='ai_photo_an_created_0s1t2u_idx'),
        ),
    ]
