import os, io, zipfile
from django.http import HttpResponse
from django.conf import settings

from customers.models import Customer, Bill



def home(req, *args, **kwargs):
    if req.user.is_authenticated:
        return HttpResponse(f"Hello, {req.user.username}!")
    else:
        return HttpResponse("You are not authenticated.")


def get_logs_zip(req, *args, **kwargs):
    if req.user.is_authenticated:
        file_name = "logs.zip"
        logs_path = settings.BASE_DIR / "logs"

        try:
            buffer = io.BytesIO()

            with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                for root, dirs, files in os.walk(logs_path):
                    for file in files:
                        zip_file.write(
                            os.path.join(root, file), 
                            os.path.relpath(
                                os.path.join(root, file), 
                                os.path.join(logs_path, '..')
                            )
                        )

            response = HttpResponse(buffer.getvalue(), 
                                    content_type='application/zip', 
                                    status=200)
            response['Content-Disposition'] = f'attachment; filename={file_name}'
            
            return response

        except Exception as e:
            return HttpResponse("Something went wrong", status=500)
    else:
        return HttpResponse("You are not authenticated.")



def get_customers_csv(req, *args, **kwargs):
    if req.user.is_authenticated:

        file_name = "customers.csv"
        keys = "user_id", "balance", "is_banned", "timestamp"

        try:
            customers = Customer.objects.all()

            with io.StringIO() as buffer:

                record = ";".join(keys) + '\n'
                buffer.write(record)
                
                for customer in customers:
                    row = []

                    for key in keys:
                        data = getattr(customer, key)
                        row.append(str(data))

                    record = ";".join(row) + '\n'
                    buffer.write(record)

                response = HttpResponse(buffer.getvalue(), 
                                        content_type='text/csv', 
                                        status=200)
                response['Content-Disposition'] = f'attachment; filename={file_name}'
            
            return response

        except Exception as e:
            print(e)
            return HttpResponse("Something went wrong", status=500)
    else:
        return HttpResponse("You are not authenticated.")




def get_bills_csv(req, *args, **kwargs):
    if req.user.is_authenticated:
        
        file_name = "bills.csv"
        keys = "site_id", "bill_id", "amount", "currency", "status", "creation", "expiration", "comment", "timestamp"

        try:
            bills = Bill.objects.all()

            with io.StringIO() as buffer:

                record = ";".join(keys) + '\n'
                buffer.write(record)
                
                for bill in bills:
                    row = []

                    for key in keys:
                        data = getattr(bill, key)
                        row.append(str(data))

                    record = ";".join(row) + '\n'
                    buffer.write(record)

                response = HttpResponse(buffer.getvalue(), 
                                        content_type='text/csv', 
                                        status=200)
                response['Content-Disposition'] = f'attachment; filename={file_name}'
            
            return response

        except Exception as e:
            return HttpResponse("Something went wrong", status=500)
    else:
        return HttpResponse("You are not authenticated.")