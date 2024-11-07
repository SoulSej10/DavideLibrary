from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Borrower, BookInventory, BorrowSlip, Attendance, CustomUser, Category

# Borrower Admin
class BorrowerAdmin(admin.ModelAdmin):
    list_display = ('pk_display', 'borrower_name', 'age', 'grade_level', 'section', 'adviser', 'date_issued')
    
    def pk_display(self, obj):
        return obj.borrower_uid
    pk_display.short_description = '[PK] Borrower UID'

admin.site.register(Borrower, BorrowerAdmin)

# Book Inventory Admin
class BookInventoryAdmin(admin.ModelAdmin):
    list_display = ('pk_display', 'book_title', 'author', 'quantity')
    
    def pk_display(self, obj):
        return obj.book_number
    pk_display.short_description = '[PK] Book UID'

admin.site.register(BookInventory, BookInventoryAdmin)

# Borrow Slip Admin
class BorrowSlipAdmin(admin.ModelAdmin):
    list_display = ('pk_display', 'book_number', 'book_title', 'borrower_uid_number', 'borrower_name', 'date_borrow', 'due_date', 'status')
    
    def pk_display(self, obj):
        return obj.slip_number
    pk_display.short_description = '[PK] Slip Number'

admin.site.register(BorrowSlip, BorrowSlipAdmin)

# Attendance Admin
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ('pk_display', 'borrower_uid_number', 'borrower_name', 'date_time')
    
    def pk_display(self, obj):
        return obj.attendance_number
    pk_display.short_description = '[PK] Log Number'

admin.site.register(Attendance, AttendanceAdmin)

# Custom User Admin
class CustomUserAdmin(UserAdmin):
    list_display = ('pk_display', 'username', 'first_name', 'last_name', 'is_staff', 'is_superuser', 'role')

    def pk_display(self, obj):
        return obj.id
    pk_display.short_description = '[PK] AutoID'

    # Override the fieldsets to include only the relevant fields for CustomUser
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal Info', {'fields': ('first_name', 'middle_name', 'last_name', 'admin_id', 'role')}),
        ('Permissions', {'fields': ('is_staff', 'is_active', 'is_superuser', 'groups', 'user_permissions')}),
    )

    # Override add_fieldsets to match the CustomUser model
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'password1', 'password2', 'first_name', 'middle_name', 'last_name', 'admin_id', 'role', 'is_staff', 'is_active', 'is_superuser'),
        }),
    )

# Register CustomUser with the customized admin
admin.site.register(CustomUser, CustomUserAdmin)

# Category Admin
admin.site.register(Category)
