# from django.contrib.postgres.fields import ArrayField
# from django.db import models
#
# from core.base_models import AbstractBaseModel
#
#
# class Order(AbstractBaseModel):
#     class OrderStatuses(models.TextChoices):
#         PROCESSING = 'PROCESSING', 'в обработке'
#         AWAITING_SPLIT_PAID = 'AWAITING_SPLIT_PAID', 'ожидает полную оплату'
#         AWAITING_SEND = 'AWAIT_DELIVERED', 'ожидает отправку'
#         ACCEPT_DELIVERY = 'ACCEPT_DELIVERY', 'принят в доставку'
#         ON_THE_ROAD = 'ON_THE_ROAD', 'в пути'
#         AWAITING_RECEIPT = 'AWAITING_RECEIPT', 'ожидает получения'
#         COMPLETED = 'COMPLETED', 'завершен'
#         CANCEL = 'CANCEL', 'отменен'
#
#     class DeliveredTypes(models.TextChoices):
#         PICKUP = 'PICKUP', 'самовывоз'
#
#     user = models.ForeignKey('users.User', on_delete=models.CASCADE, related_name='orders')
#     user_phone = models.BigIntegerField('Номер телефона', blank=True, null=True)
#     user_full_name = models.CharField('ФИО', max_length=200, blank=True, null=True)
#     user_email = models.EmailField('Email', blank=True, null=True)
#     total_cost = models.DecimalField('Итоговая стоимость товара', max_digits=10, decimal_places=2, default=0)
#     status = models.CharField(max_length=50, choices=OrderStatuses.choices, default=OrderStatuses.AWAITING_PAYMENT)
#     item_sku = models.ForeignKey('shop.ItemSKU', on_delete=models.SET_NULL, null=True, related_name='order_items')
#     count = models.PositiveSmallIntegerField(default=1)
#     city = models.CharField('Город', max_length=300, blank=True, null=True)
#     address = models.CharField('Адрес доставки', max_length=200, blank=True, null=True)
#
#     delivery_type = models.CharField('Способ доставки', max_length=50, choices=DeliveredTypes.choices)
#
#     total_cost_without_promo_code_and_bonuses = models.FloatField(
#         'Цена без скидки и бонусов', null=True
#     )
#     statuses_history = ArrayField(models.CharField(max_length=200), blank=True, editable=False, default=list)
#
#     class Meta:
#         ordering = ('-created_at',)
#         verbose_name = 'Заказ'
#         verbose_name_plural = 'Заказы'
#
#     def save(self, *args, **kwargs):
#         self.full_clean()
#         if self.status not in self.statuses_history:
#             self.statuses_history.append(self.status)
#         return super().save(*args, **kwargs)
#
#     def __str__(self):
#         return str(self.id)
#
