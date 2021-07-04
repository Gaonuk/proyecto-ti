from django.utils import timezone
from django_q.models import Schedule
from .cron import mover_recepcion_a_alm_central, mover_pulmon_a_alm_recepcion

Schedule.objects.create(
    func="api.cron.mover_recepcion_a_alm_central",
    name="Mover almacen recepción a central",
    minutes=5,
    schedule_type='I'
)

Schedule.objects.create(
    func="api.cron.mover_pulmon_a_alm_recepcion",
    name="Mover almacen pulmón a recepción",
    minutes=10,
    schedule_type='I'
)