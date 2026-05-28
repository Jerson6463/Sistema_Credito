import uuid

import django.db.models.deletion
import django_fsm
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Event',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=255)),
                ('start_time', models.DateTimeField()),
                (
                    'status',
                    models.CharField(
                        choices=[
                            ('programado', 'Programado'),
                            ('en_vivo', 'En vivo'),
                            ('finalizado', 'Finalizado'),
                            ('suspendido', 'Suspendido'),
                            ('anulado', 'Anulado'),
                        ],
                        default='programado',
                        max_length=20,
                    ),
                ),
            ],
            options={
                'ordering': ['start_time'],
            },
        ),
        migrations.CreateModel(
            name='Market',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                (
                    'type',
                    models.CharField(
                        choices=[('1X2', '1X2')],
                        default='1X2',
                        max_length=32,
                    ),
                ),
                ('is_active', models.BooleanField(default=True)),
                (
                    'event',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='markets',
                        to='betting.event',
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name='Selection',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=100)),
                ('current_odds', models.DecimalField(decimal_places=4, max_digits=18)),
                (
                    'market',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='selections',
                        to='betting.market',
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name='Bet',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('stake', models.DecimalField(decimal_places=4, max_digits=18)),
                ('locked_odds', models.DecimalField(decimal_places=4, max_digits=18)),
                (
                    'status',
                    django_fsm.FSMField(
                        choices=[
                            ('accepted', 'Accepted'),
                            ('won', 'Won'),
                            ('lost', 'Lost'),
                            ('refunded', 'Refunded'),
                            ('cashed_out', 'Cashed out'),
                        ],
                        default='accepted',
                        max_length=50,
                        protected=True,
                    ),
                ),
                ('transaction_id', models.UUIDField(default=uuid.uuid4, editable=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                (
                    'selection',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name='bets',
                        to='betting.selection',
                    ),
                ),
                (
                    'user',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='bets',
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
        migrations.AlterUniqueTogether(
            name='market',
            unique_together={('event', 'type')},
        ),
        migrations.AlterUniqueTogether(
            name='selection',
            unique_together={('market', 'name')},
        ),
    ]
