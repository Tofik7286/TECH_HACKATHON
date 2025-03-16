from datetime import datetime
from django.shortcuts import render, redirect
from datetime import timedelta
from .models import Asset, AssetSubCategory, AssetCategory
from django.core.exceptions import ObjectDoesNotExist
from datetime import datetime, timedelta
from django.shortcuts import render, redirect, get_object_or_404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from app.models import *
from rest_framework.decorators import api_view
from rest_framework import status
from django.contrib.auth import login as django_login
from django.contrib.auth import login as django_login
from .serializers import ProductSerializer, LoginSerializer, AssignSerializer, AssetSerializer, UserSerializer, BarcodeUpdateSerializer, RequestAssetSerializer, SubcategorySerializer, AllocationSerializer
from django.utils import timezone
from datetime import datetime
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.serializers.json import DjangoJSONEncoder
from geopy.geocoders import Nominatim
from django.db.models import Count
import json
import csv
from django.http import HttpResponse
from django.core.files.storage import FileSystemStorage
import pandas as pd
from django.db import transaction


@api_view(['POST'])
def login_view(request):
    # print(f"Received data: {request.data}")  # Print raw request data

    # Check if request contains data
    # if not request.data:
    #     print("No data received.")

    # Deserialize the incoming data
    serializer = LoginSerializer(data=request.data)
    print(f"Serializer is valid: {serializer.is_valid()}")

    if serializer.is_valid():
        username = serializer.validated_data['username']
        password = serializer.validated_data['password']

        # Debugging step: print received username and password
        # print(f"Username: {username}")
        # print(f"Password: {password}")

        try:
            # Check if user exists
            user = UserDetails.objects.get(username=username)

            # Debugging step: print the stored password
            # print(f"Stored password: {user.password}")

            if user.password == password:
                user.last_login = timezone.now()
                user.save()  # Save the updated last_login time

                # request.session['user_id'] = user.user_id
                request.session['username'] = user.username
                # Example custom field
                request.session['role'] = user.role.role
                request.session['full_name'] = user.first_name

                # Log the user in
                django_login(request, user)

                return Response({
                    'message': 'Login successful',
                    'session_id': request.session.session_key,
                    'username': user.username,
                    'role': user.role.role,
                }, status=status.HTTP_200_OK)
            else:
                return Response({'error': 'Invalid password'}, status=status.HTTP_400_BAD_REQUEST)
        except UserDetails.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

    # If the serializer is not valid, return the errors
    print(f"Serializer errors: {serializer.errors}")
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
def get_categories(request):
    categories = AssetCategory.objects.all()
    data = []
    for category in categories:
        subcategories = AssetSubCategory.objects.filter(category=category)
        data.append({
            "category_id": category.category_id,
            "category_name": category.category_name,
            "subcategories": [
                {
                    "sub_category_id": sub.sub_category_id,
                    "sub_category_name": sub.sub_category_name
                }
                for sub in subcategories
            ]
        })
    return Response(data, status=200)


@api_view(['GET'])
def get_condition_choices(request):
    conditions = [condition[0] for condition in CONDITION_CHOICES]
    return Response(conditions)


@api_view(['POST'])
def add_product(request):
    serializer = ProductSerializer(data=request.data)
    print(request.data)

    if not serializer.is_valid():
        print("Validation Errors:", serializer.errors)
        return Response(serializer.errors, status=400)

    else:
        # Extract validated data from the request
        assetName = serializer.validated_data['asset_name']
        assetValue = serializer.validated_data['asset_value']
        barcode = serializer.validated_data['barcode']
        category = serializer.validated_data['category']
        condition = serializer.validated_data['condition']
        # Format: 'longitude,latitude'
        location = serializer.validated_data['location']
        purchaseDate = serializer.validated_data['purchase_date']
        # Assuming this is passed as subcategory_id
        subcategory = serializer.validated_data['subcategory']
        print(location)
        # Convert location coordinates into a readable name
        try:
            latitude, longitude = map(float, location.split(','))
            geolocator = Nominatim(user_agent="asset_management")
            location_name = geolocator.reverse(
                (latitude, longitude)).raw['address']
            print(location_name)
            road_name = location_name.get('road')
            city_name = location_name.get('state_district')
            district_name = location_name.get('city_district')
            specific_area_name = road_name + ', ' + city_name + ', ' + district_name
            print(specific_area_name)
        except Exception as e:
            return Response({"error": f"Failed to resolve location name: {str(e)}"}, status=400)

        # Get the AssetSubCategory instance based on the provided subcategory_id
        try:
            subcategory = AssetSubCategory.objects.get(
                sub_category_name=subcategory)
        except AssetSubCategory.DoesNotExist:
            return Response({"error": "Subcategory not found"}, status=404)

        # Create a new Asset instance with the related subcategory
        asset = Asset.objects.create(
            asset_name=assetName,
            barcode=barcode,
            asset_category=subcategory,  # This is the ForeignKey relation
            purchase_date=purchaseDate,
            asset_value=assetValue,
            condition=condition,
            location=specific_area_name  # Save the specific area name
        )

        # Uncomment if maintenance needs to be created
        Maintenance.objects.create(
            asset=asset,
            last_maintenance_date=asset.purchase_date,
            next_maintenance_date=asset.purchase_date +
            timedelta(days=180),  # Example: 180 days after purchase
            maintenance_cost='N/A',  # Set a default cost or pass it from the request
        )

        return Response({"message": "Product added successfully!", "location_name": specific_area_name}, status=201)

    return Response(serializer.errors, status=400)


@api_view(['GET'])
def user_list_view(request):
    users = UserDetails.objects.all()  # Get all users
    serializer = UserSerializer(users, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['GET'])
def AssetListView(request):
    filter_type = request.query_params.get('filter')
    subcategory = request.GET.get('subcategory', None)

    if filter_type == 'available':
        assets = Asset.objects.filter(asset_status='available')
    elif filter_type == 'in-use':
        assets = Asset.objects.filter(asset_status='in-use')
    elif filter_type == 'in-maintenance':
        assets = Asset.objects.filter(asset_status='in-maintenance')
    elif filter_type == 'expired':
        assets = Asset.objects.filter(asset_status='expired')
    elif filter_type == 'barcode-remaining':
        assets = Asset.objects.filter(barcode__isnull=True)
    elif subcategory:
        assets = Asset.objects.filter(asset_category=subcategory)
    else:
        assets = Asset.objects.all()

    serializer = AssetSerializer(assets, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['GET'])
def UserAssetListView(request):
    """
    Retrieve products based on the username.
    Query parameter: `username`
    """
    username = request.query_params.get('username', None)
    filter = request.query_params.get('filter', None)

    if username:
        if filter == 'Due Soon':
            # Fetch allocations where the `expected_return_date` is within the next 7 days
            today = datetime.today().date()
            next_seven_days = today + timedelta(days=7)
            products = Allocation.objects.filter(
                user__username=username,
                expected_return_date__gte=today,
                expected_return_date__lte=next_seven_days
            )
            serializer = AllocationSerializer(products, many=True)
            print(serializer.data)
        elif filter == 'Returned':
            products = ReturnedProducts.objects.filter(user__username=username)
            serializer = AssetSerializer(products, many=True)
        else:
            products = Asset.objects.filter(assign_to__username=username)
            serializer = AssetSerializer(products, many=True)
    else:
        return Response(
            {"detail": "Username query parameter is required."},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Return the serialized data as a response
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['GET'])
def SubcategoryListAPIView(request, id):
    print(id)  # To ensure the ID is passed correctly
    subcategories = AssetSubCategory.objects.filter(category__category_id=id)
    serializer = SubcategorySerializer(subcategories, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)


def index(request):
    userCount = UserDetails.objects.count()
    assetCount = Asset.objects.count()
    availableAsset = Asset.objects.filter(assign_to__isnull=True).count()
    inUseAsset = Asset.objects.filter(assign_to__isnull=False).count()

    condition_queryset = Asset.objects.values(
        'condition').annotate(total=Count('asset_id')).order_by()
    condition_data = list(condition_queryset)

    stations_data = (
        # Replace "station_name" with the actual field in UserDetails
        Asset.objects.values("assign_to__station__station_name")
        .annotate(total_products=Count("assign_to"))
        .filter(assign_to__isnull=False)  # Only consider allocated assets
    )

    station_names = [data["assign_to__station__station_name"]
                     for data in stations_data]
    total_products = [data["total_products"] for data in stations_data]

    return render(request, 'index.html', {
        'userCount': userCount,
        'assetCount': assetCount,
        'availableAsset': availableAsset,
        'inUseAsset': inUseAsset,
        # Serialize to JSON
        'station_names': json.dumps(station_names),
        # Serialize to JSON
        'total_products': json.dumps(total_products),
        'condition_data': json.dumps(condition_data),

    })


@api_view(['PUT'])
def update_barcode(request, asset_id):
    try:
        asset = Asset.objects.get(asset_id=asset_id)
    except Asset.DoesNotExist:
        return Response({"error": "Asset not found"}, status=status.HTTP_404_NOT_FOUND)

    serializer = BarcodeUpdateSerializer(data=request.data)
    print(request.data)
    if serializer.is_valid():
        asset.barcode = serializer.validated_data['barcode']
        asset.save()
        return Response({"message": "Barcode updated successfully"}, status=status.HTTP_200_OK)
    print(serializer.errors)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
def get_requests(request):
    try:
        requests = RequestAsset.objects.all()
        serializer = RequestAssetSerializer(requests, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
def get_totals(request):
    try:
        total_products = Asset.objects.count()
        total_users = UserDetails.objects.count()

        data = {
            "total_products": total_products,
            "total_users": total_users,
        }
        return Response(data, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
def get_user_totals(request):

    username = request.query_params.get('username', None)
    print(username)
    try:
        total_products = Asset.objects.filter(
            assign_to__user__username=username).count()
        print(total_products)
        data = {
            "total_products": total_products
        }
        return Response(data, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
def get_product_by_barcode(request, barcode):
    try:
        # Try to find the product with the given barcode
        product = Asset.objects.get(barcode=barcode)

        serializer = AssetSerializer(product, many=False)

        print(serializer.data)  # Debugging log to verify data
        return Response(serializer.data, status=status.HTTP_200_OK)
    except Asset.DoesNotExist:
        # If no product is found with the given barcode
        return JsonResponse({'status': 'error', 'message': 'Product not found with this barcode.'})


def signin(request):
    if "email" in request.session:
        # Redirect to the appropriate page for logged-in users
        return redirect('index')

    if request.method == 'POST':
        email = request.POST['email']
        password = request.POST['password']
        try:
            # Fetch user by email
            uid = UserDetails.objects.get(email=email)
            print(email)
            # Check password match
            if uid.password == password:
                # Set session only if the password is correct
                request.session['email'] = uid.email
                # Redirect to the dashboard or homepage
                return redirect("index")
            else:
                # Invalid password
                con = {"e_msg": "Invalid password"}
                return render(request, "signin.html", con)
        except UserDetails.DoesNotExist:
            # User does not exist
            con = {'e_msg': 'User does not exist'}
            return render(request, 'signin.html', con)

    return render(request, 'signin.html')


def logout(request):
    if 'email' in request.session:
        del request.session['email']
        return redirect('signin')
    else:
        return redirect('signin')


def forgetpassword(request):
    return render(request, 'forgetpassword.html')


def productlist(request):
    filter = request.GET.get('filter')
    print(filter)
    if filter:  # Check if a filter is provided
        # Filter assets where the assigned user's station matches the filter value
        assets = Asset.objects.filter(assign_to__station__station_name=filter)
        print(assets)
    else:
        assets = Asset.objects.all()
        # If no filter is provided, fetch all assets

    return render(request, 'productlist.html', {'asset': assets})


def editproduct(request, id):
    assets = Asset.objects.get(asset_id=id)
    if request.method == 'POST':
        # Get data from the form
        asset_name = request.POST.get('asset_name')
        barcode = request.POST.get('barcode')
        category_id = request.POST.get('category')  # Pass category ID
        condition = request.POST.get('condition')
        asset_value = request.POST.get('asset_value')
        asset_maintenance_date = request.POST.get('asset_maintenance_date')

        # Update asset fields
        assets.asset_name = asset_name
        assets.barcode = barcode
        assets.asset_value = asset_value
        assets.asset_maintenance_date = asset_maintenance_date

        # Update related fields (category and condition)
        if category_id:
            assets.asset_category_id = category_id  # Assuming category uses a foreign key
        assets.condition = condition

        assets.save()  # Save the updated object
        # Redirect to product list after editing
        return redirect('productlist')

    # Fetch categories for the dropdown
    categories = AssetCategory.objects.all()

    return render(request, 'editproduct.html', {'asset': assets, 'categories': categories})


def productdetails(request, id):
    # Retrieve the product with the given id or return a 404 if it doesn't exist
    asset = get_object_or_404(Asset, asset_id=id)

    # Pass the asset to the template context
    context = {'asset': asset}
    return render(request, 'productdetails.html', context)


# def addproduct(request):
#     if request.method == 'POST':
#         # Get data from the form
#         product_name = request.POST.get('productname')
#         # Assume you pass category ID
#         category = request.POST.get('category_name')
#         purchase_date = request.POST.get('purchasedate')
#         asset_value = request.POST.get('productvalue')
#         condition = request.POST.get('condition')
#         maintenance_date = request.POST.get('maintenance_date')

#         print(product_name)

#         categoryGet = AssetSubCategory.objects.get(sub_category_name=category)

#         Asset.objects.create(
#             asset_name=product_name,
#             asset_category=categoryGet,
#             purchase_date=purchase_date,
#             asset_value=asset_value,
#             condition=condition,
#             asset_maintenance_date=maintenance_date,
#         )

#         return redirect('productlist')
#     categories = AssetSubCategory.objects.all()
#     return render(request, 'addproduct.html', {'categories': categories})


def addproduct(request):
    if request.method == 'POST':
        product_name = request.POST.get('productname')
        sub_category_name = request.POST.get('category_name')
        purchase_date = request.POST.get('purchasedate')
        asset_value = request.POST.get('productvalue')
        condition = request.POST.get('condition')
        maintenance_date = request.POST.get('maintenance_date')

        # Validate and parse dates
        try:
            if purchase_date:
                purchase_date = datetime.strptime(
                    purchase_date, '%Y-%m-%d').date()
            else:
                purchase_date = None
            if maintenance_date:
                maintenance_date = datetime.strptime(
                    maintenance_date, '%Y-%m-%d').date()
            else:
                maintenance_date = None
        except ValueError as e:
            return HttpResponse(f'Invalid date format: {e}', status=400)

        try:
            sub_category = AssetSubCategory.objects.get(
                sub_category_name=sub_category_name)
        except AssetSubCategory.DoesNotExist:
            category_name = request.POST.get('category_name')
            category, created = AssetCategory.objects.get_or_create(
                category_name=category_name)
            sub_category = AssetSubCategory(
                sub_category_name=sub_category_name, category=category)
            sub_category.save()

        Asset.objects.create(
            asset_name=product_name,
            asset_category=sub_category,
            purchase_date=purchase_date,
            asset_value=asset_value,
            condition=condition,
            asset_maintenance_date=maintenance_date,
        )
        return redirect('productlist')

    categories = AssetSubCategory.objects.all()
    return render(request, 'addproduct.html', {'categories': categories})


def categorylist(request):
    catList = AssetCategory.objects.all()
    print(catList)
    return render(request, 'categorylist.html')


def addcategory(request):
    return render(request, 'addcategory.html')


def subcategorylist(request):
    return render(request, 'subcategorylist.html')


def addsubcategory(request):
    return render(request, 'subaddcategory.html')


def editcategory(request):
    return render(request, 'editcategory.html')


def editsubcategory(request):
    return render(request, 'editsubcategory.html')


def importproduct(request):
    return render(request, 'importproduct.html')


def barcode(request):
    return render(request, 'barcode.html')

# def importproduct(request):
#     return render(request,'importproduct.html')
#     return render(request,'barcode.html')


def issuedproducts(request):
    issuedproducts_id = Allocation.objects.all()
    con = {'issuedproducts_id': issuedproducts_id}
    return render(request, 'issuedproducts.html', con)


# def deleteissued(request):
#     issuedproducts_id = Allocation.objects.get(issuedproducts_id=id)
#     issuedproducts_id.delete()
#     return render(request,'issuedproducts.html')

def addissuedproducts(request):
    if request.method == "POST":
        asset_name = request.POST['asset_name']
        barcode = request.POST['barcode']
        user = request.POST['user']
        issue_date = request.POST['issue_date']
        return_date = request.POST['return_date']
        Allocation.objects.create(asset_name=asset_name, barcode=barcode,
                                  user=user, issue_date=issue_date, return_date=return_date)
        return render("issuedproducts")
    return render(request, 'addissuedproducts.html')


def maintenanceproducts(request):
    maintenance_id = Maintenance.objects.all()
    con = {'maintenance_id': maintenance_id}
    return render(request, 'maintenanceproducts.html', con)


def editmaintenanceproducts(request, id):
    maintenance_id = Maintenance.objects.get(maintenance_id=id)
    if request.method == 'POST':
        asset_name = request.POST['asset_name']
        barcode = request.POST['barcode']
        last_maintenance_date = request.POST['last_maintenance_date']
        next_maintenance_date = request.POST['next_maintenance_date']
        return_date = request.POST['return_date']
        maintenance_cost = request.POST['maintenance_cost']
        # print(last_maintenance_date)

        try:
            asset = Asset.objects.get(barcode=barcode)
            maintenance_id.asset = asset
            maintenance_id.last_maintenance_date = last_maintenance_date
            maintenance_id.next_maintenance_date = next_maintenance_date
            maintenance_id.return_date = return_date
            maintenance_id.maintenance_cost = maintenance_cost
            maintenance_id.save()

            return redirect('maintenanceproducts')

        except Asset.DoesNotExist:
            return render(request, 'editmaintenanceproducts.html', {
                'i': maintenance_id,
                'error': "Asset with the given name and barcode does not exist."
            })

    return render(request, 'editmaintenanceproducts.html', {'i': maintenance_id})


def addmaintenanceproducts(request):
    if request.method == 'POST':
        asset_name = request.POST['asset_name']
        barcode = request.POST['barcode']
        last_maintenance_date = request.POST['last_maintenance_date']
        next_maintenance_date = request.POST['next_maintenance_date']
        return_date = request.POST['return_date']
        maintenance_cost = request.POST['maintenance_cost']
        Maintenance.objects.create(asset_name=asset_name, barcode=barcode, last_maintenance_date=last_maintenance_date,
                                   next_maintenance_date=next_maintenance_date, return_date=return_date, maintenance_cost=maintenance_cost)
        return redirect("maintenanceproducts")
    return render(request, 'addmaintenanceproducts.html')


def deletemaintenance(request):
    maintenance_id = Maintenance.objects.get(maintenance_id=id)
    maintenance_id.delete()
    return render(request, 'maintenanceproducts')


def expiredproducts(request):
    expired_id = ExpiredProduct.objects.all()
    con = {'expired_id': expired_id}
    return render(request, 'expiredproducts.html', con)


def editexpiredproducts(request, id):
    expired_id = ExpiredProduct.objects.get(expired_id=id)
    if request.method == 'POST':
        asset_name = request.POST['asset_name']
        barcode = request.POST['barcode']
        expiration_date = request.POST['expiration_date']
        reason = request.POST['reason']

        try:
            asset = Asset.objects.get(barcode=barcode)
            expired_id.asset = asset
            expired_id.expiration_date = expiration_date
            expired_id.reason = reason
            expired_id.save()
            return redirect('expiredproducts')

        except Asset.DoesNotExist:
            return render(request, 'editexpiredproducts.html', {
                'i': expired_id,
                'error': "Asset with the given name and barcode does not exist."
            })

    return render(request, 'editexpiredproducts.html', {'i': expired_id})


def addexpiredproducts(request):
    return render(request, 'addexpiredproducts.html')


def deleteexpired(request, id):
    expired_id = ExpiredProduct.objects.get(expired_id=id)
    expired_id.delete()
    return redirect('expiredproducts')


def returnproducts(request):
    return render(request, 'returnproducts.html')


def editreturnproducts(request):
    return render(request, 'editreturnproducts.html')


def addreturnproducts(request):
    return render(request, 'addreturnproducts.html')


def aa(request):
    return render(request, 'aa.html')


def newuser(request):
    if request.method == 'POST':
        # Get data from the POST request
        username = request.POST.get('username')
        role_name = request.POST.get('role_name')
        email = request.POST.get('email')
        password = request.POST.get('password')
        station_name = request.POST.get('station_name')
        mobile = request.POST.get('mobile')
        print(username)
        print(station_name)
        print(email)
        # Get related Role and Station objects
        roleGet = role.objects.get(role=role_name)
        station = stationDetails.objects.get(station_name=station_name)

        UserDetails.objects.create(
            username=username,
            role=roleGet,
            email=email,
            password=password,
            station=station,
            contact_number=mobile,
            full_name="amaan shaikh"
        )

        return redirect('newuser')

    roles = role.objects.all()
    station = stationDetails.objects.all()

    return render(request, 'newuser.html', {'roles': roles, 'station': station})


def userlists(request):
    users = UserDetails.objects.all()
    return render(request, 'userlists.html', {'users': users})


def edituser(request):
    return render(request, 'edituser.html')


def expenseList(request):
    return render(request, 'expenselist.html')


def createExpense(request):
    return render(request, 'createexpense.html')


def editExpense(request):
    return render(request, 'editexpense.html')


def expenseCategory(request):
    return render(request, 'expenseCategory.html')


def quotationList(request):
    return render(request, 'quotationList.html')


def addquotation(request):
    return render(request, 'addquotation.html')


def stationlist(request):
    station_id = stationDetails.objects.all()

    con = {"station_id": station_id}
    return render(request, 'stationlist.html', con)


def newstation(request):
    if request.POST:
        station_name = request.POST['station_name']
        station_code = request.POST['station_code']
        station_address = request.POST['station_address']
        stationDetails.objects.create(
            station_name=station_name, station_code=station_code, station_address=station_address)
        return redirect('stationlist')
    return render(request, 'newstation.html')


def editstation(request, id):
    station_id = stationDetails.objects.get(station_id=id)
    if request.POST:
        station_name = request.POST['station_name']
        station_code = request.POST['station_code']
        station_address = request.POST['station_address']

        station_id.station_name = station_name
        station_id.station_code = station_code
        station_id.station_address = station_address

        station_id.save()

        return redirect('stationlist')
    return render(request, 'editstation.html', {'i': station_id})


def deletestation(request, id):
    station_id = stationDetails.objects.get(station_id=id)
    station_id.delete()

    return redirect('stationlist')


def editQuotation(request):
    return render(request, 'editquotation.html')


def editExpense(request):
    return render(request, 'editExpense.html')


def profile(request):
    return render(request, 'profile.html')


def generalSettings(request):
    return render(request, 'editexpense.html')


def signup(request):
    return render(request, 'signup.html')


@api_view(['POST'])
def assign_product(request):
    # Deserialize the incoming data
    serializer = AssignSerializer(data=request.data)
    print(request.data)
    if serializer.is_valid():
        # Extract the necessary fields
        barcode = serializer.validated_data['barcode']
        returnDate = serializer.validated_data['return_date']
        user = serializer.validated_data['username']
        location = serializer.validated_data['location']
        print(location)
        print(user)

        latitude, longitude = map(float, location.split(','))
        geolocator = Nominatim(user_agent="asset_management")
        location_name = geolocator.reverse(
            (latitude, longitude)).raw['address']
        print(location_name)
        road_name = location_name.get('road')
        city_name = location_name.get('state_district')
        district_name = location_name.get('city_district')
        specific_area_name = road_name + ', ' + city_name + ', ' + district_name
        print(specific_area_name)

        try:
            # Fetch the asset from the database
            asset = Asset.objects.get(barcode=barcode)

            if asset.assign_to is None:
                user = UserDetails.objects.get(username=user)
                # Create a new Allocation object and save it to the database
                allocation = Allocation.objects.create(
                    asset=asset,
                    user=user,
                    expected_return_date=returnDate,
                    assign_location=specific_area_name
                )

                asset.assign_to = user
                asset.asset_status = 'in-use'
                asset.save()

                return Response({"message": "Product assigned successfully!", "allocation_id": allocation.allocation_id}, status=201)
            else:
                return Response({"message": "Product is already assigned!"}, status=400)
        except ObjectDoesNotExist:
            return Response({"message": "Product not found with barcode!"}, status=404)
    else:
        print("Validation Errors:", serializer.errors)
        return Response(serializer.errors, status=400)


# import and export product
# Function to import products
def import_products_html(req):
    return render(req, 'import-products.html')


@csrf_exempt
def import_products(request):
    if request.method == 'POST' and request.FILES['file']:
        file = request.FILES['file']
        if not (file.name.endswith('.csv') or file.name.endswith('.xlsx')):
            return HttpResponse('Invalid file type. Please upload a CSV or Excel file.', status=400)

        try:
            if file.name.endswith('.csv'):
                df = pd.read_csv(file)
            elif file.name.endswith('.xlsx'):
                df = pd.read_excel(file)
        except Exception as e:
            print(f'Error reading file: {e}')
            return HttpResponse(f'Error reading file: {e}', status=400)

        def parse_date(date_value):
            try:
                if pd.isna(date_value):
                    return None
                if isinstance(date_value, pd.Timestamp):
                    date_value = date_value.strftime('%Y-%m-%d')
                return datetime.strptime(date_value, '%Y-%m-%d').date()
            except ValueError:
                return None

        try:
            with transaction.atomic():
                for index, row in df.iterrows():
                    # Print the contents of each row for debugging
                    print(f'Row {index}: {row}')
                    asset_name = row.get('asset_name')
                    barcode = row.get('barcode')
                    # category_name = row.get('category_name')
                    sub_category_name = row.get('sub_category_name')
                    purchase_date = parse_date(row.get('purchase_date'))
                    asset_value = row.get('asset_value')
                    condition = row.get('condition')

                    if not all([asset_name, barcode, asset_value, condition]):
                        print(f'Missing required fields in row {index}')
                        continue

                    if purchase_date is None:
                        print(f'Invalid date format in row {index}')
                        continue

                    # Ensure the sub_category and category are saved before creating the asset
                    # category, created = AssetCategory.objects.get_or_create(
                    #     category_name=category_name)
                    # sub_category, created = AssetSubCategory.objects.get_or_create(
                    #     sub_category_name=sub_category_name,
                    #     defaults={'category': category}
                    # )

                    print(f'Creating asset: {asset_name}')
                    Asset.objects.create(
                        asset_name=asset_name,
                        barcode=barcode,
                        asset_category=sub_category_name,
                        purchase_date=purchase_date,
                        asset_value=asset_value,
                        condition=condition,
                    )

            print('Products imported successfully')
            return HttpResponse('Products imported successfully')
        except Exception as e:
            print(f'Error saving products: {e}')
            return HttpResponse(f'Error saving products: {e}', status=500)

    print('Invalid request')
    return HttpResponse('Invalid request. Please upload a CSV or Excel file.', status=400)


def export_products(request):
    assets = Asset.objects.all()
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="products.csv"'

    writer = csv.writer(response)
    writer.writerow(['asset_name', 'barcode', 'category_name',
                    'purchase_date', 'asset_value', 'condition'])
    for asset in assets:
        writer.writerow([
            asset.asset_name,
            asset.barcode,
            asset.asset_category.category.category_name if asset.asset_category and asset.asset_category.category else '',
            asset.purchase_date,
            asset.asset_value,
            asset.condition,
        ])

    return response


# delete products
def deleteproduct(request, id):
    asset = Asset.objects.get(id=id)
    asset.delete()
    return redirect('productlist')
