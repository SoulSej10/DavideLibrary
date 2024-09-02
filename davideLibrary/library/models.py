# ============================================================================================================================================
# ==============================================================___IMPORTS___=================================================================
# ============================================================================================================================================
from django.db import models
from django.contrib.auth.models import User
import qrcode
from io import BytesIO
from django.core.files import File
from PIL import Image
from django.db import models
from django.core.files.base import ContentFile
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.graphics.barcode import code128
from reportlab.lib.units import inch
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.utils.translation import gettext_lazy as _
from .utils import generate_qr_code
from django.utils import timezone




# ============================================================================================================================================
# ==============================================================___USER MODEL___==============================================================
# ============================================================================================================================================
class CustomUserManager(BaseUserManager):
    def create_user(self, username, password=None, **extra_fields):
        if not username:
            raise ValueError(_('The Username field must be set'))
        user = self.model(username=username, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(username, password, **extra_fields)

class CustomUser(AbstractBaseUser, PermissionsMixin):
    username = models.CharField(max_length=150, unique=True)
    first_name = models.CharField(max_length=30)
    middle_name = models.CharField(max_length=30, blank=True)
    last_name = models.CharField(max_length=30)
    password = models.CharField(max_length=128)
    
    # Additional fields
    admin_id = models.CharField(max_length=255, unique=True)
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_superuser = models.BooleanField(default=False)
    
    objects = CustomUserManager()

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['first_name', 'last_name', 'admin_id']

    def __str__(self):
        return self.username





# ============================================================================================================================================
# ==============================================================___BORROWER MODEL___==========================================================
# ============================================================================================================================================
class Borrower(models.Model):
    borrower_uid = models.CharField(max_length=20, primary_key=True, unique=True)
    borrower_name = models.CharField(max_length=100)
    age = models.IntegerField()
    grade_level = models.CharField(max_length=2)
    section = models.CharField(max_length=100, blank=True)
    adviser = models.CharField(max_length=100, blank=True)
    date_issued = models.DateTimeField()
    qr_code = models.ImageField(upload_to='qr_codes', blank=True)

    def save(self, *args, **kwargs):
        if not self.borrower_uid:
            max_id = Borrower.objects.all().aggregate(max_id=models.Max('borrower_uid'))['max_id']
            if max_id:
                new_id = int(max_id.replace('hpdsnhs', '')) + 1
            else:
                new_id = 1
            self.borrower_uid = f"hpdsnhs{new_id:06d}"

        super().save(*args, **kwargs)

        # Generate QR code after saving the borrower
        qr_image = qrcode.make(self.borrower_uid)
        qr_offset = Image.new('RGB', (qr_image.pixel_size, qr_image.pixel_size), 'white')
        qr_offset.paste(qr_image)
        stream = BytesIO()
        qr_offset.save(stream, format="PNG")
        self.qr_code.save(f'{self.borrower_uid}.png', File(stream), save=False)

        super().save(*args, **kwargs)

    def __str__(self):
        return self.borrower_name

class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name





# ============================================================================================================================================
# ==============================================================___BOOK MODEL___==============================================================
# ============================================================================================================================================
class BookInventory(models.Model):
    book_number = models.CharField(max_length=10, primary_key=True)
    record_date = models.DateTimeField(auto_now_add=True)
    class_field = models.CharField(max_length=100, blank=True, null=True)
    author = models.CharField(max_length=200, blank=True, null=True)
    book_title = models.CharField(max_length=200)
    edition = models.CharField(max_length=50, blank=True, null=True)
    volume = models.CharField(max_length=50, blank=True, null=True)
    pages = models.IntegerField(blank=True, null=True)
    quantity = models.PositiveIntegerField(default=1)
    fund_source = models.CharField(max_length=100, blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    publisher = models.CharField(max_length=200, blank=True, null=True)
    year = models.IntegerField(blank=True, null=True)
    remark = models.TextField(blank=True, null=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    location = models.TextField(blank=True, null=True)
    qr_code = models.ImageField(upload_to='qr_codes/', blank=True, null=True)

    def __str__(self):
        return self.book_title

    def save(self, *args, **kwargs):
        if not self.book_number:
            category_prefix = self.get_category_prefix()
            latest_book_number = BookInventory.objects.filter(book_number__startswith=category_prefix).order_by('-book_number').first()
            next_number = 1

            if latest_book_number:
                last_number = int(latest_book_number.book_number.split('-')[1])
                next_number = last_number + 1

            self.book_number = f"{category_prefix}-{next_number:03d}"

        # Generate QR code if not present
        if not self.qr_code:
            qr_code_file = generate_qr_code(self.book_number)
            self.qr_code.save(f"{self.book_number}.png", qr_code_file, save=False)

        super().save(*args, **kwargs)

    def get_category_prefix(self):
        category_prefix_map = {category.name: chr(65 + i) for i, category in enumerate(Category.objects.all())}
        return category_prefix_map.get(self.category.name, 'X')






# ============================================================================================================================================
# ==============================================================___SLIP MODEL___==============================================================
# ============================================================================================================================================
class BorrowSlip(models.Model):
    slip_number = models.AutoField(primary_key=True)
    book_number = models.CharField(max_length=20, blank=True)
    book_title = models.CharField(max_length=200, blank=True)
    author = models.CharField(max_length=200, blank=True)
    category_number = models.IntegerField(blank=True, null=True)
    date_borrow = models.DateTimeField()
    borrower_uid_number = models.CharField(max_length=20)
    borrower_name = models.CharField(max_length=100, blank=True)
    due_date = models.DateTimeField()
    librarian_name = models.CharField(max_length=100)

    status = models.CharField(max_length=50, default='Borrowed')
    returned = models.BooleanField(default=False)  # Add this line
    penalty = models.CharField(max_length=255, blank=True, null=True)

    def save(self, *args, **kwargs):
        # Automatically populate book_title and author from BookInventory
        if self.book_number:
            try:
                book = BookInventory.objects.get(book_number=self.book_number)
                self.book_title = book.book_title
                self.author = book.author
                
            except BookInventory.DoesNotExist:
                self.book_title = ""
                self.author = ""
                self.category_number = None
        
        # Automatically populate borrower_name from Borrower
        if self.borrower_uid_number:
            try:
                borrower = Borrower.objects.get(borrower_uid=self.borrower_uid_number)
                self.borrower_name = borrower.borrower_name
            except Borrower.DoesNotExist:
                self.borrower_name = ""
        
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Borrow Slip #{self.slip_number}"

    




# ============================================================================================================================================
# ==============================================================___LOG MODEL___===============================================================
# ============================================================================================================================================
class Attendance(models.Model):
    attendance_number = models.AutoField(primary_key=True)
    date_time = models.DateTimeField(auto_now_add=True)
    borrower_uid_number = models.CharField(max_length=20)
    borrower_name = models.CharField(max_length=100)
    grade_level = models.IntegerField(null=True, blank=True)
    section = models.CharField(max_length=100, null=True, blank=True)

    def __str__(self):
        return f"Attendance #{self.attendance_number}"









# ============================================================================================================================================
# ==============================================================___MONITORING MODEL___========================================================
# ============================================================================================================================================
# class BorrowedBook(models.Model):
#     book = models.ForeignKey(BookInventory, on_delete=models.CASCADE)
#     borrower = models.ForeignKey(Borrower, on_delete=models.CASCADE)
#     borrow_date = models.DateTimeField(default=timezone.now)
#     due_date = models.DateTimeField()
#     return_date = models.DateTimeField(null=True, blank=True)
#     status = models.CharField(max_length=20, default='Borrowed')

#     def save(self, *args, **kwargs):
#         if self.pk is None:
#             self.book.quantity -= 1
#             self.book.save()
#         super().save(*args, **kwargs)

#     def return_book(self):
#         self.return_date = timezone.now()
#         self.status = 'Returned'
#         self.book.quantity += 1
#         self.book.save()
#         self.save()

#     def __str__(self):
#         return f"{self.book.book_title} borrowed by {self.borrower.borrower_name}"