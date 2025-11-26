from django.db import models


class SoftDeleteModel(models.Model):
    # Ensure that no data is lost when erasing records
    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def delete(self, using=None, keep_parents=False):
        """Soft delete instead of removing the row."""
        self.is_deleted = True
        self.save(update_fields=["is_deleted", "updated_at"])

        return (1, {self.__class__.__name__: 1})

    class Meta:
        abstract = True


class User(SoftDeleteModel):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    phone_number = models.CharField(max_length=50)
    email = models.EmailField(unique=True)
    money = models.DecimalField(max_digits=14, decimal_places=2, default=0.0)
    def __str__(self):
        return f"{self.first_name} {self.last_name}"


