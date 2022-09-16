"""backend URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include

from .views import (
    home, 
    get_logs_zip, 
    get_customers_csv,
    get_bills_csv,
)


urlpatterns = [
    path('admin/', admin.site.urls),
    path("", home),
    path("logs.zip", get_logs_zip),
    path("customers.csv", get_customers_csv),
    path("bills.csv", get_bills_csv),
    path('customers/', include("customers.urls"))
]
