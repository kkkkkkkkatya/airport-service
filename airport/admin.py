from django.contrib import admin

from airport.models import (
    Airport,
    Airplane,
    AirplaneType,
    Crew,
    Ticket,
    Order,
    Flight,
    Route
)

admin.site.register(Airport)
admin.site.register(AirplaneType)
admin.site.register(Crew)
admin.site.register(Ticket)
admin.site.register(Order)
admin.site.register(Flight)
admin.site.register(Route)
admin.site.register(Airplane)
