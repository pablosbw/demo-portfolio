from django.core.management.base import BaseCommand
from django.utils import timezone
from racional_api.models import Stock, StockPrice
from faker import Faker
from datetime import datetime, timedelta

dict_simbol_names = {
    "AAPL": "Apple Inc.",
    "GOOGL": "Alphabet Inc.",
    "MSFT": "Microsoft Corporation",
    "AMZN": "Amazon.com, Inc.",
    "TSLA": "Tesla, Inc.",
    "FB": "Meta Platforms, Inc.",
    "NVDA": "NVIDIA Corporation",
    "JPM": "JPMorgan Chase & Co.",
    "V": "Visa Inc.",
    "DIS": "The Walt Disney Company",
    "CASH": "CASH",
}


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        fake = Faker()
        start_date = datetime.strptime("2020-01-01", "%Y-%m-%d")
        end_date = datetime.strptime("2025-12-31", "%Y-%m-%d")
        
        for symbol, name in dict_simbol_names.items():
            stock = Stock.objects.filter(symbol=symbol).exists()
            # Check if stock already exists to avoid overpopulation
            if stock:
                continue 

            stock = Stock.objects.create(
                symbol=symbol,
                name=name
            )
            value = 100
            current_date = start_date
            
            while current_date <= end_date:
                if symbol == "CASH":
                    value = 1.0
                else:
                    value = value + fake.random_int(min=-2, max=3)
                aware_date = timezone.make_aware(current_date)
                StockPrice.objects.create(
                    stock=stock,
                    value=value,
                    date=aware_date
                )
                current_date += timedelta(days=1)
        self.stdout.write(self.style.SUCCESS("Example stocks created!"))