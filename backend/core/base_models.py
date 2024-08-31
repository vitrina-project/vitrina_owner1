from django.contrib.gis.db import models as gis_models
from django.contrib.gis.db.models.functions import Distance
from django.contrib.gis.geos import Point
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import F, Value


def validate_geopoint_interval(value):
    if value < -90.0 or value > 90.0:
        raise ValidationError(f"{value} must be in the range [-90.0, 90.0]")


class LocationQuerySet(models.QuerySet):
    def distance(self, point=None):
        if point is None:
            point = [44.893844, 37.616726]
        return self.annotate(
            distance=Distance(F("coords"), Value(Point(point[::1], srid=4326)))
        )


class AbstractBaseAddress(gis_models.Model):
    lat = gis_models.FloatField('Широта', validators=[validate_geopoint_interval], db_index=True)
    lon = gis_models.FloatField('Долгота', validators=[validate_geopoint_interval], db_index=True)
    city = gis_models.CharField('Город', max_length=255, blank=True)
    street = gis_models.CharField('Улица', max_length=255, blank=True, null=True)
    building = gis_models.CharField('Строение', max_length=255, blank=True, null=True)
    block = gis_models.CharField('Корпус', max_length=255, blank=True, null=True)
    floor = gis_models.CharField('Этаж', max_length=255, blank=True, null=True)
    apartment = gis_models.CharField('Квартира', max_length=255, blank=True, null=True)
    entrance = gis_models.CharField('Вход', max_length=255, blank=True, null=True)
    elevator = gis_models.CharField('Лифт', max_length=255, blank=True, null=True)
    region = gis_models.CharField('Регион', max_length=255, blank=True, null=True)
    area = gis_models.CharField('Область', max_length=255, blank=True, null=True)
    door_phone = gis_models.CharField('Код двери', max_length=255, blank=True, null=True)
    comment = gis_models.CharField('Комментарий', max_length=255, blank=True, null=True)

    coords = gis_models.PointField(geography=True)
    objects = LocationQuerySet.as_manager()

    @property
    def full_address(self):
        address = f'{self.city}, {self.street}, {self.building}'
        if self.block:
            address += f', {self.block}'
        if self.floor:
            address += f', {self.floor}'
        if self.apartment:
            address += f', {self.apartment}'
        return address

    @property
    def short_address(self):
        return f'{self.street} {self.building}'

    def __str__(self):
        return self.full_address

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        self.coords = Point(self.lat, self.lon)
        return super().save(*args, **kwargs)


class AbstractBaseModel(models.Model):
    created_at = models.DateTimeField("Дата создания", auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField("Дата последнего обновления", auto_now=True, db_index=True)

    class Meta:
        abstract = True
        ordering = ('-created_at',)

    objects = models.Manager()
