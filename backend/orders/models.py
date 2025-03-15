from django.contrib.postgres.fields import ArrayField
from django.db import models

from core.base_models import AbstractBaseModel


class Order(AbstractBaseModel):
    class OrderStatuses(models.TextChoices):
        PROCESSING = 'PROCESSING', 'в обработке'
        AWAITING_RECEIPT = 'AWAITING_RECEIPT', 'ожидает получения'
        COMPLETED = 'COMPLETED', 'завершен'
        CANCEL = 'CANCEL', 'отменен'

    user = models.ForeignKey('users.User', on_delete=models.CASCADE, related_name='orders')
    status = models.CharField(max_length=50, choices=OrderStatuses.choices, default=OrderStatuses.PROCESSING)
    statuses_history = ArrayField(models.CharField(max_length=200), blank=True, editable=False, default=list)

    class Meta:
        ordering = ('-created_at',)
        verbose_name = 'Заказ'
        verbose_name_plural = 'Заказы'

    def save(self, *args, **kwargs):
        self.full_clean()
        if self.status not in self.statuses_history:
            self.statuses_history.append(self.status)
        return super().save(*args, **kwargs)

    def __str__(self):
        return str(self.id)


class OrderItem(AbstractBaseModel):
    order = models.ForeignKey('orders.Order', on_delete=models.CASCADE, related_name='items')
    total_cost = models.DecimalField('Итоговая стоимость товара', max_digits=10, decimal_places=2, default=0)
    item_sku = models.ForeignKey('shop.ItemSKU', on_delete=models.PROTECT, related_name='order_items')
    count = models.PositiveSmallIntegerField(default=1)

    class Meta:
        ordering = ('-created_at',)
        verbose_name = 'Товар в заказе'
        verbose_name_plural = 'Товары в заказе'
