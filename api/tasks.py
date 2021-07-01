from django.utils import timezone
from django_q.models import Schedule
from .cron import mover_recepcion_a_alm_central

Schedule.objects.create(
    func="api.cron.mover_recepcion_a_alm_central",
    name="Text file creation process",
    minutes=2,
    repeats=1
)