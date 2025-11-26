from django.core.management.base import BaseCommand
from racional_api.models import User, Transaction
from faker import Faker

class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        fake = Faker()
        users = User.objects.all()
        for user in users:
            total_amount = 0
            for _ in range(5):
                amount = fake.random_number(digits=5)
                Transaction.objects.create(
                    user=user,
                    amount=amount,
                    transaction_type=Transaction.DEPOSIT,
                    execution_date=fake.date_this_year(),
                )
                total_amount += amount
            user.money += total_amount
            user.save()
            
            for _ in range(4):
                amount = fake.random_number(digits=5)
                if amount > user.money:
                    amount = user.money
                    
                if amount == 0:
                    continue
                Transaction.objects.create(
                    user=user,
                    amount=amount,
                    transaction_type=Transaction.WITHDRAW,
                    execution_date=fake.date_this_year(),
                )
                user.money -= amount
                user.save()
        self.stdout.write(self.style.SUCCESS("Created Transaction for users"))
