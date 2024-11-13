from django.contrib import admin
from .models import Income, Expense, Category, UserProfile 

admin.site.register(Income)
admin.site.register(Expense)
admin.site.register(Category)
admin.site.register(UserProfile)
