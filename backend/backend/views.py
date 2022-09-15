from django.http import HttpResponse

def home(req, *args, **kwargs):
    return HttpResponse("Hello")