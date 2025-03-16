from django.contrib import admin
from .models import *

class AdminUser(admin.ModelAdmin):
    list_display=("barcode", "asset_name", "asset_category", "asset_status")
# Register your models here.

admin.site.register(Asset, AdminUser)
admin.site.register(UserDetails)
admin.site.register(role)
admin.site.register(AssetCategory)
admin.site.register(AssetSubCategory)
admin.site.register(stationDetails)
admin.site.register(Allocation)
admin.site.register(RequestAsset)
admin.site.register(Maintenance)
admin.site.register(ExpiredProduct)