from django.db import transaction
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

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


class CrewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Crew
        fields = ("id", "first_name", "last_name", "full_name")


class AirplaneTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = AirplaneType
        fields = ("id", "name")


class AirplaneReadSerializer(serializers.ModelSerializer):
    airplane_type = serializers.CharField(source="airplane_type.name", read_only=True)

    class Meta:
        model = Airplane
        fields = ("id", "name", "airplane_type", "rows", "seats_in_row", "capacity", "image")


class AirplaneSerializer(serializers.ModelSerializer):
    class Meta:
        model = Airplane
        fields = ("id", "name", "airplane_type", "rows", "seats_in_row", "capacity")


class AirplaneImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Airplane
        fields = ("id", "image")


class AirportSerializer(serializers.ModelSerializer):
    routes_to = serializers.SerializerMethodField()

    class Meta:
        model = Airport
        fields = ("id", "name", "closest_big_city", "routes_to")

    def get_routes_to(self, obj):
        routes = obj.routes_from.all()
        return [route.destination.name for route in routes]


class RouteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Route
        fields = ("id", "source", "destination", "distance")

    def validate(self, attrs):
        route = Route(**attrs)
        route.clean()
        return attrs


class RouteReadSerializer(RouteSerializer):
    source = serializers.CharField(source="source.name", read_only=True)
    destination = serializers.CharField(source="destination.name", read_only=True)


class TicketSerializer(serializers.ModelSerializer):
    def validate(self, attrs):
        data = super(TicketSerializer, self).validate(attrs=attrs)
        Ticket.validate_ticket(
            attrs["row"],
            attrs["seat"],
            attrs["flight"].airplane,
            ValidationError
        )
        return data

    class Meta:
        model = Ticket
        fields = ("id", "row", "seat", "flight")


class TicketSeatsSerializer(TicketSerializer):
    class Meta:
        model = Ticket
        fields = ("row", "seat")


class FlightSerializer(serializers.ModelSerializer):
    class Meta:
        model = Flight
        fields = ("id", "route", "airplane", "departure_time", "arrival_time", "flight_time", "crew")


class FlightListSerializer(FlightSerializer):
    route = RouteReadSerializer(many=False, read_only=True)
    airplane_name = serializers.CharField(
        source="airplane.name", read_only=True
    )
    airplane_capacity = serializers.IntegerField(
        source="airplane.capacity", read_only=True
    )
    airplane_image = serializers.ImageField(source="airplane.image", read_only=True)
    tickets_available = serializers.IntegerField(read_only=True)
    number_of_crew = serializers.IntegerField(read_only=True)

    class Meta:
        model = Flight
        fields = (
            "id",
            "route",
            "departure_time",
            "arrival_time",
            "airplane_name",
            "airplane_capacity",
            "airplane_image",
            "tickets_available",
            "number_of_crew"
        )


class FlightDetailSerializer(serializers.ModelSerializer):
    route = RouteReadSerializer(many=False, read_only=True)
    flight_time = serializers.CharField(read_only=True)
    airplane = AirplaneReadSerializer(many=False, read_only=True)
    taken_places = TicketSeatsSerializer(source="tickets", many=True, read_only=True)
    crew = CrewSerializer(many=True, read_only=True)

    class Meta:
        model = Flight
        fields = (
            "id",
            "route",
            "departure_time",
            "arrival_time",
            "flight_time",
            "airplane",
            "taken_places",
            "crew"
        )


class TicketListSerializer(TicketSerializer):
    flight = FlightListSerializer(many=False, read_only=True)


class OrderSerializer(serializers.ModelSerializer):
    tickets = TicketSerializer(many=True, read_only=False, allow_empty=False)

    class Meta:
        model = Order
        fields = ("id", "tickets", "created_at")

    def create(self, validated_data):
        with transaction.atomic():
            tickets_data = validated_data.pop("tickets")
            order = Order.objects.create(**validated_data)
            for ticket_data in tickets_data:
                Ticket.objects.create(order=order, **ticket_data)
            return order


class OrderListSerializer(OrderSerializer):
    tickets = TicketListSerializer(many=True, read_only=True)
