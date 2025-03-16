"""
URL configuration for djangoIntegration project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
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

from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('', views.index, name='index'),
    path('api/login/', views.login_view, name='login'),
    path('api/categories/', views.get_categories, name='get-categorys'),
    path('api/conditions/', views.get_condition_choices, name='get_condition_choices'),
    path('api/add_product/', views.add_product, name='addProduct'),  # Update this line
    path('api/users/', views.user_list_view, name='userlist'),
    path('api/totals/', views.get_totals, name='get_totals'),
    path('api/user/totals/', views.get_user_totals, name='get_user_totals'),
    path('api/assign_product/', views.assign_product, name='assignProduct'),
    path('api/asset/', views.AssetListView, name='asset-list'),
    path('api/user/asset/', views.UserAssetListView, name='user-asset-list'),
    path('api/products/by-subcategory', views.AssetListView, name='asset_list'),
    path('api/categories/<int:id>/', views.SubcategoryListAPIView, name='subcategory_list'),
    path('api/products/<str:barcode>/', views.get_product_by_barcode, name='get_product_by_barcode'),# Update this line
    # path('api/assets/', views.AssetList, name='asset-list'),
    path('api/update-barcode/<str:asset_id>/', views.update_barcode, name='update-barcode'),
    path('api/requests/', views.get_requests, name='get_requests'),

    
    path('signin',views.signin, name='signin'),
    path('logout',views.logout, name='logout'),


    path('productlist', views.productlist, name='productlist'),
    path('addproduct', views.addproduct, name='addproduct'),
    path('editproduct/<int:id>', views.editproduct, name='editproduct'),
    path('productdetails/<int:id>', views.productdetails, name='productdetails'),


    path('categorylist', views.categorylist, name='categorylist'),
    path('addcategory', views.addcategory, name='addcategory'),
    path('subcategorylist', views.subcategorylist, name='subcategorylist'),
    path('addsubcategory', views.addsubcategory, name='addsubcategory'),
    path('editcategory', views.editcategory, name='editcategory'),
    path('editsubcategory', views.editsubcategory, name='editsubcategory'),

    # path('importproduct', views.importproduct, name='importproduct'),
    # path('barcode', views.barcode, name='barcode'),

    path('issuedproducts', views.issuedproducts, name='issuedproducts'),
    path('addissuedproducts', views.addissuedproducts, name='addissuedproducts'),
    # path('deleteissued/<int:id>', views.deleteissued, name='deleteissued'),


    path('maintenanceproducts', views.maintenanceproducts, name='maintenanceproducts'),
    path('editmaintenanceproducts/<int:id>', views.editmaintenanceproducts, name='editmaintenanceproducts'),
    path('addmaintenanceproducts', views.addmaintenanceproducts, name='addmaintenanceproducts'),
    path('deletemaintenance/<int:id>', views.deletemaintenance, name='deletemaintenance'),


    path('expiredproducts', views.expiredproducts, name='expiredproducts'),
    path('editexpiredproducts/<int:id>', views.editexpiredproducts, name='editexpiredproducts'),
    path('addexpiredproducts', views.addexpiredproducts, name='addexpiredproducts'),
    path('deleteexpired/<int:id>', views.deleteexpired, name='deleteexpired'),


    path('returnproducts', views.returnproducts, name='returnproducts'),
    path('editreturnproducts', views.editreturnproducts, name='editreturnproducts'),
    path('addreturnproducts', views.addreturnproducts, name='addreturnproducts'),


    path('newuser', views.newuser, name='newuser'),
    path('userlists', views.userlists, name='userlists'),
    path('edituser', views.edituser, name='edituser'),


    path('expenselist',views.expenseList, name='expenseList'),
    path('createexpense',views.createExpense, name='createExpense'),
    path('editexpense',views.editExpense, name='editExpense'),
    path('expensecategory',views.expenseCategory, name='expenseCategory'),
    path('quotationlist',views.quotationList, name='quotationList'),
    path('addquotation',views.addquotation, name='addquotation'),
    path('newstation',views.newstation, name='newstation'),
    path('stationlist',views.stationlist, name='stationlist'),
    path('editstation/<int:id>',views.editstation, name='editstation'),
    path('deletestation/<int:id>',views.deletestation, name='deletestation'),

    path('editquotation',views.editQuotation, name='editQuotation'),
    path('editexpense',views.editExpense, name='editExpense'),
    path('profile',views.profile, name='profile'),
    path('generalsettings',views.generalSettings, name='generalSettings'),
    path('forgetpassword',views.forgetpassword, name='forgetpassword'),
    path('signup',views.signup, name='signup'),
 
    path('api/assign_product/', views.assign_product, name='assignProduct'),  # Update this line
    # path('api/assets/', views.AssetList, name='asset-list'),
    path('api/assets/', views.AssetListView, name='asset-list'),
    # path('pie_chart_view', views.pie_chart_view, name='pie_chart_view-list'),
    # path('generate_pie_chart', views.generate_pie_chart, name='generate_pie_chart-list'),

]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)