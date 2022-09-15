from django.contrib import admin

from .models import Customer, Bill

admin.site.register(Customer)
admin.site.register(Bill)
