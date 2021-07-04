from django.contrib import admin
from .models import SentOC, RecievedOC, Log
# Register your models here.
admin.site.register(SentOC)
admin.site.register(RecievedOC)
admin.site.register(Log)