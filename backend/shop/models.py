from django.db import models

from core.base_models import AbstractBaseModel, Genders
from core.utils import slugify, get_random_string


class Brand(models.Model):
    name = models.CharField('Название', max_length=300, db_index=True)
    slug = models.SlugField(max_length=300, unique=True)
    is_show = models.BooleanField('Показывать на сайте', default=True, db_index=True)
    description = models.TextField('Описание', blank=True)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        self.slug = slugify(self.name)
        if Brand.objects.filter(slug=self.slug).exists():
            self.slug = f'{self.slug}_{get_random_string()}'
        return super().save(*args, **kwargs)

    class Meta:
        ordering = ('name',)
        verbose_name = 'Бренд'
        verbose_name_plural = 'Бренды'


class Style(models.Model):
    name = models.CharField('Название', max_length=400, unique=True)
    slug = models.SlugField(max_length=400, unique=True)
    is_show = models.BooleanField('Показывать на сайте', default=True, db_index=True)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        self.slug = slugify(self.name)
        if Style.objects.filter(slug=self.slug).exists():
            self.slug = f'{self.slug}_{get_random_string()}'
        return super().save(*args, **kwargs)

    class Meta:
        ordering = ('name',)
        verbose_name = 'Стиль'
        verbose_name_plural = 'Стили'


class Category(models.Model):
    name = models.CharField('Название', max_length=400, unique=True)
    slug = models.SlugField(max_length=400, unique=True)
    is_show = models.BooleanField('Показывать на сайте', default=True, db_index=True)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        self.slug = slugify(self.name)
        if Category.objects.filter(slug=self.slug).exists():
            self.slug = f'{self.slug}_{get_random_string()}'
        return super().save(*args, **kwargs)

    class Meta:
        ordering = ('name',)
        verbose_name = 'Категория'
        verbose_name_plural = 'Категории'


class CatalogItemManager(models.Manager):

    def get_queryset(self):
        return super().get_queryset().select_related('brand').prefetch_related('styles')


class PropertyKey(models.Model):
    name = models.CharField('Название ключа', max_length=300, unique=True)

    def __str__(self):
        return self.name


class Property(models.Model):
    class Types(models.IntegerChoices):
        COLOR = 0, 'цвет'
        SIZE = 1, 'размер'
        OPTION = 2, 'вариант'
        OTHER = 3, 'другое'

    key = models.ForeignKey(PropertyKey, verbose_name='Ключ', on_delete=models.PROTECT)
    value = models.CharField('Значение', max_length=300)
    type = models.PositiveSmallIntegerField('Тип', choices=Types.choices, default=Types.OTHER)

    def __str__(self):
        return f'{self.key} {self.value}'

    class Meta:
        verbose_name = 'Свойство товара'
        verbose_name_plural = 'Свойства товаров'
        constraints = [
            models.UniqueConstraint(fields=['key', 'value', 'type'], name='unique_property'),
        ]


class Image(models.Model):
    image = models.ImageField(upload_to='images/', blank=True, null=True, max_length=500)

    class Meta:
        verbose_name = 'Изображение товара'
        verbose_name_plural = 'Изображения товаров'

    def delete(self, *args, **kwargs):
        super().delete(*args, **kwargs)
        if self.image:
            self.image.delete()

    def __str__(self):
        return self.image.name


class CatalogItem(AbstractBaseModel):
    name = models.CharField('Название', max_length=400, db_index=True)
    slug = models.SlugField(max_length=400, unique=True)
    styles = models.ManyToManyField(Style, related_name='items')
    categories = models.ManyToManyField(Category, related_name='items')

    gender = models.IntegerField('Пол', choices=Genders.choices, db_index=True)
    description = models.TextField('Описание', blank=True, max_length=1000)
    article = models.CharField('Артикль', max_length=30)
    brand = models.ForeignKey(Brand, related_name='items', on_delete=models.CASCADE, verbose_name='Бренд')

    score = models.IntegerField('Популярность', default=0, db_index=True)
    store_address = models.CharField('Где забрать (адрес)', max_length=250)
    properties = models.ManyToManyField(Property, verbose_name='Свойства товара', related_name='items', blank=True)
    main_image = models.ImageField('Картинка в каталоге', upload_to='main_images/')
    images = models.ManyToManyField(Image, related_name='items', blank=True)
    objects = CatalogItemManager()

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        self.slug = slugify(self.name)
        if CatalogItem.objects.filter(slug=self.slug).exists():
            self.slug = f'{self.slug}_{get_random_string()}'
        return super().save(*args, **kwargs)

    class Meta:
        ordering = ('name',)
        verbose_name = 'Товар'
        verbose_name_plural = 'Товары'


class ItemSKU(AbstractBaseModel):
    item = models.ForeignKey(CatalogItem, related_name='skus', on_delete=models.CASCADE, verbose_name='Товар')
    price = models.DecimalField('Цена', max_digits=10, decimal_places=2, default=0)
    discount = models.PositiveSmallIntegerField('Размер скидки в %', default=0)
    properties = models.ManyToManyField(Property, verbose_name='Свойства модели товара', related_name='skus',
                                        blank=True)
    available = models.BooleanField('В наличии', default=True)
    images = models.ManyToManyField(Image, related_name='skus', blank=True)

    def __str__(self):
        return str(self.id)

    class Meta:
        verbose_name = 'Модель товара'
        verbose_name_plural = 'Модели товаров'


class Favorite(AbstractBaseModel):
    item = models.ForeignKey(CatalogItem, on_delete=models.CASCADE, related_name='favorites')
    user = models.ForeignKey('users.User', on_delete=models.CASCADE, related_name='favorites')

    class Meta:
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранное пользователей'
        constraints = [models.UniqueConstraint(fields=('user', 'item'), name='unique_favorite')]


class ShoppingCart(AbstractBaseModel):
    item_sku = models.ForeignKey(ItemSKU, on_delete=models.CASCADE, related_name='shopping_carts')
    user = models.ForeignKey('users.User', on_delete=models.CASCADE, related_name='shopping_carts')
    count = models.PositiveSmallIntegerField(default=1)

    class Meta:
        verbose_name = 'Корзина'
        verbose_name_plural = 'Корзины пользователей'
        constraints = [models.UniqueConstraint(fields=('user', 'item_sku'), name='unique_shopping_cart')]


class UserStyle(models.Model):
    style = models.ForeignKey(Style, on_delete=models.CASCADE, related_name='user_styles')
    user = models.ForeignKey('users.User', on_delete=models.CASCADE, related_name='user_styles')


class LifeStyle(models.Model):
    image = models.ImageField(upload_to='lifestyles/')
    description = models.TextField()
    styles = models.ManyToManyField(Style, related_name='lifestyles')

    class Meta:
        verbose_name = 'Образ'
        verbose_name_plural = 'Образы'


class UserLifeStyle(models.Model):
    style = models.ForeignKey(LifeStyle, on_delete=models.CASCADE, related_name='user_lifestyles')
    user = models.ForeignKey('users.User', on_delete=models.CASCADE, related_name='user_lifestyles')
    liked = models.BooleanField(default=False)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['user', 'style'], name='unique_user_lifestyle')
        ]


class BrandSubscription(AbstractBaseModel):
    user = models.ForeignKey('users.User', related_name='brands', on_delete=models.CASCADE)
    brand = models.ForeignKey(Brand, related_name='users', on_delete=models.CASCADE)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['user', 'brand'], name='unique_brand_subscription')
        ]
