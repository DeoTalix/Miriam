# Прототип обработки http запросов
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from .models import Customer, Bill




def get_customer_by_id(req, user_id, *args, **kwargs):

    try:
        customer = Customer.objects.get(user_id=user_id)
        
        return JsonResponse({
            "timestamp": customer.timestamp,
            "user_id": customer.user_id,
            "is_banned": customer.is_banned,
            "balance": customer.balance
        }, status=200)

    except Customer.DoesNotExist:

        return JsonResponse({
            "message": "Customer was not found."
        }, status=404)




@csrf_exempt
def create_customer(req, *args, **kwargs):
    
    if req.method == "POST":
        user_id = req.POST.get("user_id")

        if user_id is None:
            return JsonResponse({
                "message": "Failed to create new Customer: user_id is missing."
            }, status=400)

        customer = None

        try:
            customer = Customer.objects.get(user_id=user_id)
        except Customer.DoesNotExist:

            try:
                Customer.objects.create(user_id=user_id)
                customer = Customer.objects.get(user_id=user_id)
            except Exception as e:

                return JsonResponse({
                    "message": f"Failed to create new Customer: {e}."
                }, status=400)

        if customer is not None:

            return JsonResponse({
                "message": "Customer succesfully created."
            }, status=201)

    return JsonResponse({}, status=400)




@csrf_exempt
def update_customer_balance(req, *args, **kwargs):

    if req.method == "POST":

        user_id = req.POST.get("user_id")
        print(user_id, type(user_id))
        if user_id is None:
            return JsonResponse({
                "message": "Failed to update Customer: user_id is missing."
            }, status=400)

        customer = None

        try:
            customer = Customer.objects.get(user_id=user_id)

        except Customer.DoesNotExist:

            return JsonResponse({
                "message": "Customer was not found."
            }, status=404)

        amount = req.POST.get("amount")

        if amount is None:
            return JsonResponse({
                "message": "Failed to update Customer: amount is missing."
            }, status=400)

        customer.balance += int(float(amount))
        customer.save()

        return JsonResponse({
            "message": "Customer updated successfully."
        }, status=200)

    return JsonResponse({}, status=400)

        



@csrf_exempt
def create_bill(req, *args, **kwargs):

    if req.method == "POST":
        bill_json = dict(req.POST).get("bill")
        
        if bill_json is None:
            return JsonResponse({
                "message": "Failed to create new Bill: bill_data is missing."
            }, status=400)

        bill_data = json.loads(bill_json[0])
        user_id = req.POST.get("user_id")

        if user_id is None:
            return JsonResponse({
                "message": "Failed to create new Bill: user_id is missing."
            }, status=400)

        customer = None

        try:
            customer = Customer.objects.get(user_id=user_id)
        except Customer.DoesNotExist:
            return JsonResponse({
                "message": "Failed to create new Bill: customer was not found."
            }, status=404)

        try:
            Bill.objects.create(
                customer=customer,
                bill_id = bill_data["bill_id"],
                amount = bill_data["amount"],
                currency = bill_data["currency"],
                status = bill_data["status"],
                creation = bill_data["creation"],
                expiration = bill_data["expiration"],
                pay_url = bill_data["pay_url"],
                site_id = bill_data["site_id"],
                alt_url = bill_data["alt_url"],
                comment = bill_data["comment"],
                response = bill_data["response"]
            )

            return JsonResponse({
                "message": "Bill successfully created."
            }, status=201)

        except Exception as e:
            print(bill_data)
            return JsonResponse({
                "message": f"Failed to create new Bill: {e}."
            }, status=400)

    return JsonResponse({}, status=400)