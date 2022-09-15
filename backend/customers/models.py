from django.db import models



class Customer(models.Model):
    timestamp   = models.DateTimeField(auto_now=True, blank=False, null=False)
    user_id     = models.IntegerField(unique=True, blank=False, null=False)
    is_banned   = models.BooleanField(default=False, null=False)
    balance     = models.IntegerField(default=0, blank=False, null=False)

    def __str__(self):
        return f"Customer({self.user_id})"




class Bill(models.Model):
    timestamp   = models.DateTimeField(auto_now=True, blank=False, null=False)
    customer    = models.ForeignKey(Customer, null=True, blank=True, on_delete=models.CASCADE)
    # идентификатор вашего сайта в системе Qiwi
    site_id     = models.CharField(max_length=200, blank=False, null=False)
    # идентификатор счета
    bill_id     = models.CharField(unique=True, max_length=200, blank=False, null=False)
    # сумма счета
    amount      = models.DecimalField(max_digits=20, decimal_places=2, blank=False, null=False)
    # валюта счета
    currency    = models.CharField(max_length=3, blank=False, null=False)
    # статус счета
    status      = models.CharField(max_length=8, blank=False, null=False)
    # время создания счета
    creation    = models.CharField(max_length=100, blank=False, null=False)
    # время закрытия счета
    expiration  = models.CharField(max_length=100, blank=False, null=False)
    # URL-адрес для оплаты
    pay_url     = models.CharField(max_length=200, blank=False, null=False)
    # comment: комментарий
    comment     = models.TextField(blank=True, null=False)
    # исходный словарь Qiwi
    response    = models.JSONField(blank=False, null=False)
    # ссылка с проксированием через сервер для установки заголовка referer
    alt_url     = models.CharField(max_length=200, blank=True, null=False)

    def __str__(self):
        return f"Bill({self.customer}, {self.timestamp})"