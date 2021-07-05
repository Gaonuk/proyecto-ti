from django.utils import timezone
from django_q.models import Schedule
from .cron import mover_recepcion_a_alm_central, revision_oc, mover_despacho, despachar

Schedule.objects.create(
    func="api.cron.revision_oc",
    name="Revision de Ordenes de Compra Aceptdas",
    minutes=3,
    repeats=-1,
    schedule_type='I'
)

Schedule.objects.create(
    func="api.cron.mover_despacho",
    name="Mover productos a despacho",
    minutes=1,
    repeats=-1,
    schedule_type='I'
)

Schedule.objects.create(
    func="api.cron.despachar",
    name="Despachar productos",
    minutes=2,
    repeats=-1,
    schedule_type='I')

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