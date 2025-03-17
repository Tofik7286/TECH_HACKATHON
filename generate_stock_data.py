from app.models import Asset, StockHistory
import os
import django
import random
from datetime import datetime, timedelta

# ✅ Ensure Django settings are loaded
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "djangoIntegration.settings")
django.setup()  # ✅ Initialize Django before importing models

# ✅ Import models AFTER Django setup


def generate_fake_stock_data():
    """Generate 6 months of fake stock history for all assets."""

    # ✅ Fetch all assets
    assets = Asset.objects.all()
    if not assets:
        print("❌ No assets found. Add assets first.")
        return

    today = datetime.now().date()
    stock_entries = []  # Bulk insert optimization

    for asset in assets:
        print(f"📌 Generating stock data for: {asset.asset_name}")

        stock_level = random.randint(10, 50)  # Initial stock level
        start_date = today - timedelta(days=180)  # 6 months of data

        for _ in range(180):  # Generate data for 180 days
            stock_change = random.randint(-3, 5)  # Random increase/decrease
            # Ensure stock is not negative
            stock_level = max(0, stock_level + stock_change)

            stock_entries.append(StockHistory(
                asset=asset,
                date=start_date,
                stock_level=stock_level
            ))

            start_date += timedelta(days=1)  # Move to next day

    # ✅ Bulk insert for better performance
    StockHistory.objects.bulk_create(stock_entries)
    print(
        f"✅ Successfully inserted {len(stock_entries)} stock records for all assets!")


# ✅ Ensure script runs only when executed directly
if __name__ == "__main__":
    generate_fake_stock_data()
