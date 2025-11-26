from django.core.management.base import BaseCommand
from racional_api.models import User
from faker import Faker

class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        amount = User.objects.count()
        if amount > 0:
            return
        
        fake = Faker()
        for _ in range(20):
            User.objects.create(
                first_name=fake.first_name(),
                last_name=fake.last_name(),
                phone_number=fake.phone_number(),
                email=fake.unique.email(),
            )
        self.stdout.write(self.style.SUCCESS("20 example users created!"))
