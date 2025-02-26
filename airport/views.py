from datetime import datetime

from django.db.models import F, Count
from django.shortcuts import render
from rest_framework import viewsets, mixins, status
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from rest_framework.viewsets import GenericViewSet, ReadOnlyModelViewSet
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response

from airport.models import (
    Airport,
    Airplane,
    AirplaneType,
    Crew,
    Order,
    Flight,
    Route
)
from airport.serializers import (
    AirportSerializer,
    AirplaneSerializer,
    AirplaneTypeSerializer,
    CrewSerializer,
    OrderSerializer,
    FlightSerializer,
    RouteSerializer,
    OrderListSerializer,
    AirplaneReadSerializer,
    RouteReadSerializer, FlightListSerializer, FlightDetailSerializer, AirplaneImageSerializer,
)


class CrewViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    GenericViewSet,
):
    queryset = Crew.objects.all()
    serializer_class = CrewSerializer


class AirplaneTypeViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    GenericViewSet,
):
    queryset = AirplaneType.objects.all()
    serializer_class = AirplaneTypeSerializer


class AirplaneViewSet(
    mixins.CreateModelMixin,
    ReadOnlyModelViewSet,
    GenericViewSet,
):
    queryset = Airplane.objects.select_related("airplane_type")
    serializer_class = AirplaneSerializer

    def get_serializer_class(self):
        if self.action in ["list", "retrieve"]:
            return AirplaneReadSerializer

        if self.action == "upload_image":
            return AirplaneImageSerializer

        return AirplaneSerializer

    @action(
        methods=["POST"],
        detail=True,
        url_path="upload-image",
        permission_classes=[IsAdminUser],
    )
    def upload_image(self, request, pk=None):
        """Endpoint for uploading image to specific airplane"""
        airplane = self.get_object()
        serializer = self.get_serializer(airplane, data=request.data)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def get_queryset(self):
        airplane_type = self.request.query_params.get("airplane_type")
        queryset = self.queryset

        if airplane_type:
            queryset = queryset.filter(airplane_type_id=airplane_type)

        return queryset.distinct()


class AirportViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    GenericViewSet,
):
    queryset = Airport.objects.all()
    serializer_class = AirportSerializer

    def get_queryset(self):
        closest_big_city = self.request.query_params.get("closest_big_city")
        queryset = self.queryset

        if closest_big_city:
            queryset = queryset.filter(closest_big_city__icontains=closest_big_city)

        return queryset.distinct()


class RouteViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    GenericViewSet,
):
    queryset = Route.objects.select_related("source", "destination")
    serializer_class = RouteSerializer

    def get_serializer_class(self):
        if self.action in ["list", "retrieve"]:
            return RouteReadSerializer

        return RouteSerializer

    def get_queryset(self):
        source = self.request.query_params.get("source")
        destination = self.request.query_params.get("destination")
        queryset = self.queryset

        if source:
            queryset = queryset.filter(source_id=source)
        if destination:
            queryset = queryset.filter(destination_id=destination)

        return queryset.distinct()


class FlightViewSet(
    viewsets.ModelViewSet,
):
    queryset = (Flight.objects
                .select_related("route", "airplane")
                .annotate(
                    tickets_available=F("airplane__rows") * F("airplane__seats_in_row") - Count("tickets"),
                    number_of_crew=Count("crew", distinct=True)
                )
                .prefetch_related("crew")
    )
    serializer_class = FlightSerializer

    def get_serializer_class(self):
        if self.action == "list":
            return FlightListSerializer
        elif self.action == "retrieve":
            return FlightDetailSerializer

        return FlightSerializer

    def get_queryset(self):
        airplane = self.request.query_params.get("airplane")
        route = self.request.query_params.get("route")
        arrival_time = self.request.query_params.get("arrival_time")
        departure_time = self.request.query_params.get("departure_time")
        queryset = self.queryset

        if airplane:
            queryset = queryset.filter(airplane_id=airplane)
        if route:
            queryset = queryset.filter(route_id=route)
        if arrival_time:
            arrival_time = datetime.strptime(arrival_time, "%Y-%m-%d").date()
            queryset = queryset.filter(arrival_time__date=arrival_time)
        if departure_time:
            departure_time = datetime.strptime(departure_time, "%Y-%m-%d").date()
            queryset = queryset.filter(departure_time__date=departure_time)

        return queryset.distinct()


class OrderPagination(PageNumberPagination):
    page_size = 10
    max_page_size = 100


class OrderViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    GenericViewSet,
):
    queryset = Order.objects.prefetch_related(
        "tickets__flight__route",
        "tickets__flight__airplane"
    )
    serializer_class = OrderSerializer
    pagination_class = OrderPagination

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user)

    def get_serializer_class(self):
        if self.action == "list":
            return OrderListSerializer

        return OrderSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
