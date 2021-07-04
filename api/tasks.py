from django.utils import timezone
from django_q.models import Schedule
from .cron import mover_recepcion_a_alm_central, revision_oc, mover_despacho, despachar

Schedule.objects.create(
    func="api.cron.mover_recepcion_a_alm_central",
    name="Text file creation process",
    minutes=2,
    repeats=1
)
Schedule.objects.create(
    func="api.cron.revision_oc",
    name="Revision de Ordenes de Compra Aceptdas",
    minutes=3,
    repeats=-1
)

Schedule.objects.create(
    func="api.cron.mover_despacho",
    name="Mover productos a despacho",
    minutes=1,
    repeats=-1
)

Schedule.objects.create(
    func="api.cron.despachar",
    name="Despachar productos",
    minutes=2,
    repeats=-1
)