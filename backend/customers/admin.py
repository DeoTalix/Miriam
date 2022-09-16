from django.contrib import admin

from .models import Customer, Bill



admin.site.site_header = "Backend Admin Panel"


class CustomerAdmin(admin.ModelAdmin):
    list_display = "user_id", "balance", "is_banned", "timestamp"
    list_filter = "timestamp", "is_banned"

    change_list_template = "admin/customers/customers_change_list.html"


class BillAdmin(admin.ModelAdmin):
    list_display = "bill_id", "amount", "currency", "status", "creation", "expiration", "comment", "site_id"
    list_filter = "currency", "status", "timestamp"

    change_list_template = "admin/customers/bills_change_list.html"


admin.site.register(Customer, CustomerAdmin)
admin.site.register(Bill, BillAdmin)
