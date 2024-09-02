from django.contrib import admin
from .models import  Borrower, BookInventory, BorrowSlip, Attendance, CustomUser
from django.contrib.auth.admin import UserAdmin

admin.site.register(Borrower)
admin.site.register(BookInventory)
admin.site.register(BorrowSlip)
admin.site.register(Attendance)
# admin.site.register(BorrowedBook)
admin.site.register(CustomUser)