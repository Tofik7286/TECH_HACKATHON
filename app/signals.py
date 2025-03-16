# from django.db import transaction
# from django.db.models.signals import post_save
# from django.dispatch import receiver
# from .models import Asset, Maintenance
# from datetime import timedelta

# @receiver(post_save, sender=Asset)
# def create_maintenance_entry(sender, instance, created, **kwargs):
#     if created:  # Only when a new Asset is created
#         # Use transaction.atomic to ensure the creation is handled properly
#         with transaction.atomic():
#             # Create a related Maintenance object
#             Maintenance.objects.create(
#                 asset=instance,
#                 last_maintenance_date=instance.purchase_date,  # Initial maintenance date
#                 next_maintenance_date=instance.purchase_date + timedelta(days=180),  # Example maintenance schedule
#                 maintenance_cost='0',
#             )
