from django.db import models

class AbstractCandidate(models.Model):
    first_name = models.CharField(max_length=40)
    middle_name = models.CharField(max_length=40, blank=True)
    last_name = models.CharField(max_length=60)
    email = models.EmailField()
    phone = models.CharField(max_length=25)
    zip_code = models.CharField(max_length=15)
    date_of_birth = models.DateField()

    def get_date_of_birth_display(self):
        return self.date_of_birth.strftime('%Y-%m-%d')
