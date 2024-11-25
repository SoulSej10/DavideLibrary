# ============================================================================================================================================
# =================================================================___IMPORTS__===============================================================
# ============================================================================================================================================
#MARK: Imports
from django import forms
from django.contrib.auth.models import User, Group
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.core.exceptions import ValidationError
from django.forms import ModelForm
from .models import Borrower, BookInventory, BorrowSlip, Attendance, CustomUser, Category, Location, BookReservation
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth import authenticate
from django.contrib.auth import authenticate
from django.utils.translation import gettext_lazy as _
# from django.contrib.auth.forms import SetPasswordForm
from django.contrib.auth.forms import PasswordChangeForm
import hashlib
import datetime


#MARK: User
# ============================================================================================================================================
# ==============================================================___USER FORM___===============================================================
# ============================================================================================================================================
class CustomUserCreationForm(UserCreationForm):
    password1 = forms.CharField(widget=forms.PasswordInput, label="Password")
    password2 = forms.CharField(widget=forms.PasswordInput, label="Confirm Password")

    class Meta:
        model = CustomUser
        fields = ['username', 'first_name', 'middle_name', 'last_name', 'admin_id', 'password1', 'password2', 'role']
        widgets = {
            'role': forms.Select(choices=CustomUser.ROLE_CHOICES, attrs={'id': 'role-field'}),
            'admin_id': forms.TextInput(attrs={'readonly': 'readonly'})  # Make admin_id readonly
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Automatically set the admin_id field value for new users
        if not self.instance.pk:
            self.fields['admin_id'].initial = CustomUser.generate_next_admin_id()

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if len(username) < 8:
            raise forms.ValidationError("Username must be at least 8 characters long.")
        if not any(char.isdigit() for char in username):
            raise forms.ValidationError("Username must contain at least one number.")
        if not any(char.isupper() for char in username):
            raise forms.ValidationError("Username must contain at least one uppercase letter.")
        return username

    def save(self, commit=True):
        # Ensure admin_id is populated (for new users)
        if not self.instance.admin_id:
            self.instance.admin_id = CustomUser.generate_next_admin_id()

        user = super().save(commit=False)  # Create user but don't save yet

        # Ensure password is set correctly
        user.set_password(self.cleaned_data["password1"])

        # Automatically handle the `is_staff` field based on role
        user.is_staff = user.role == 'Head Librarian'  

        # Commit to save the user
        if commit:
            user.save()

            # If role is Assistant Librarian, assign to appropriate group
            if user.role == 'Assistant Librarian':
                assistant_group, _ = Group.objects.get_or_create(name='Assistant Librarian')
                user.groups.add(assistant_group)

        return user

class CustomAuthenticationForm(AuthenticationForm):
    admin_id = forms.CharField(max_length=255, required=True)

    def clean(self):
        cleaned_data = super().clean()
        username = cleaned_data.get('username')
        password = cleaned_data.get('password')
        admin_id = cleaned_data.get('admin_id')

        if username and password and admin_id:
            user = authenticate(username=username, password=password, admin_id=admin_id)
            if user is None:
                raise forms.ValidationError("Invalid credentials or admin ID.")
        return cleaned_data

class CustomPasswordResetForm(forms.Form):
    new_password1 = forms.CharField(
        label="New Password",
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        min_length=8,  # or your preferred min length
    )
    new_password2 = forms.CharField(
        label="Confirm New Password",
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        min_length=8,
    )

    def clean_new_password2(self):
        password1 = self.cleaned_data.get("new_password1")
        password2 = self.cleaned_data.get("new_password2")
        if password1 != password2:
            raise forms.ValidationError("The two password fields must match.")
        return password2

#MARK: Student
# ============================================================================================================================================
# ==================================================___STUDENT/BORROWER FORM___===============================================================
# ============================================================================================================================================
class BorrowerForm(forms.ModelForm):
    firstname = forms.CharField(max_length=100, required=True)
    middle_initial = forms.CharField(max_length=2, required=False)
    lastname = forms.CharField(max_length=100, required=False)
    GRADE_CHOICES = [
        ('', 'All Grades'),  # Add an option for all grades
        ('7', '7'),
        ('8', '8'),
        ('9', '9'),
        ('10', '10'),
        ('11', '11'),
        ('12', '12'),
    ]
    grade_level = forms.ChoiceField(choices=GRADE_CHOICES, required=False)

    class Meta:
        model = Borrower
        exclude = ['borrower_uid', 'borrower_name', 'qr_code', 'date_issued', 'status']  # Exclude status here
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            name_parts = self.instance.borrower_name.split()
            if len(name_parts) >= 3:
                self.fields['firstname'].initial = ' '.join(name_parts[:-2])
                self.fields['middle_initial'].initial = name_parts[-2]
                self.fields['lastname'].initial = name_parts[-1]
            elif len(name_parts) == 2:
                self.fields['firstname'].initial = name_parts[0]
                self.fields['lastname'].initial = name_parts[1]
            elif len(name_parts) == 1:
                self.fields['firstname'].initial = name_parts[0]

    def save(self, commit=True):
        firstname = self.cleaned_data.get('firstname', '').strip()
        middle_initial = self.cleaned_data.get('middle_initial', '').strip()
        lastname = self.cleaned_data.get('lastname', '').strip()
        
        # Concatenate the names with careful handling of extra spaces
        if middle_initial:
            self.instance.borrower_name = f"{firstname} {middle_initial} {lastname}".strip()
        else:
            self.instance.borrower_name = f"{firstname} {lastname}".strip()
        
        self.instance.status = 'Normal'  # Set the status to 'Normal' by default
        
        return super().save(commit)

        
        


#MARK: Inventory/Book
# ============================================================================================================================================
# ==============================================================___BOOK FORM___===============================================================
# ============================================================================================================================================
class BookInventoryForm(forms.ModelForm):
    firstname = forms.CharField(max_length=100, required=False)
    middle_initial = forms.CharField(max_length=2, required=False)
    lastname = forms.CharField(max_length=100, required=False)
    new_location = forms.CharField(max_length=200, required=False, label="New Location")  # Field for new location

    class Meta:
        model = BookInventory
        fields = ['class_field', 'book_title', 'edition', 'volume', 'pages', 'quantity', 
                  'fund_source', 'price', 'publisher', 'year', 'category', 'remark', 
                  'location', 'book_type']
        widgets = {
            'class_field': forms.TextInput(attrs={'autofocus': 'autofocus'}),  # Add autofocus here
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            # Split the author into firstname, middle_initial, and lastname
            name_parts = self.instance.author.split()
            if len(name_parts) >= 3:
                self.fields['firstname'].initial = ' '.join(name_parts[:-2])
                self.fields['middle_initial'].initial = name_parts[-2]
                self.fields['lastname'].initial = name_parts[-1]
            elif len(name_parts) == 2:
                self.fields['firstname'].initial = name_parts[0]
                self.fields['lastname'].initial = name_parts[1]
            elif len(name_parts) == 1:
                self.fields['firstname'].initial = name_parts[0]

    def save(self, commit=True):
        # Process author fields
        firstname = self.cleaned_data.get('firstname', '').strip()
        middle_initial = self.cleaned_data.get('middle_initial', '').strip()
        lastname = self.cleaned_data.get('lastname', '').strip()
        
        # Handle saving a new location
        new_location_name = self.cleaned_data.get('new_location')
        if new_location_name:
            location, created = Location.objects.get_or_create(name=new_location_name)
            self.instance.location = location

        # Concatenate the names with careful handling of extra spaces
        if middle_initial:
            self.instance.author = f"{firstname} {middle_initial} {lastname}".strip()
        else:
            self.instance.author = f"{firstname} {lastname}".strip()

        return super().save(commit)




#MARK: Slip
# ============================================================================================================================================
# ==============================================================___SLIP FORM___===============================================================
# ============================================================================================================================================
from django import forms
from django.utils import timezone
from .models import BorrowSlip

class BorrowSlipForm(forms.ModelForm):
    class Meta:
        model = BorrowSlip
        fields = ['book_number', 'date_borrow', 'borrower_uid_number', 'due_date', 'librarian_name']
        widgets = {
            'book_number': forms.TextInput(attrs={'autofocus': True}),
            'date_borrow': forms.TextInput(attrs={'readonly': 'readonly'}),
            'due_date': forms.TextInput(attrs={'readonly': 'readonly'}),
            'librarian_name': forms.TextInput(attrs={'readonly': 'readonly'}),
        }

    book_number = forms.CharField(max_length=20)
    borrower_uid_number = forms.CharField(max_length=20)

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super(BorrowSlipForm, self).__init__(*args, **kwargs)

        # Set the librarian name
        if user:
            full_name = f"{user.first_name} {user.middle_name[0] if user.middle_name else ''}. {user.last_name}"
            self.fields['librarian_name'].initial = full_name
        
        # Set default date_borrow as the current date, timezone-aware
        if not self.instance.pk:
            self.fields['date_borrow'].initial = timezone.now()  # Using timezone-aware now()

        # No need to set the due_date here anymore, it's handled by JS

    def save(self, commit=True):
        instance = super().save(commit=False)

        # Make sure the `date_borrow` is timezone-aware before saving
        if timezone.is_naive(instance.date_borrow):
            instance.date_borrow = timezone.make_aware(instance.date_borrow, timezone.get_current_timezone())

        # The `due_date` is handled by JS, so no need to modify it here
        if timezone.is_naive(instance.due_date):
            instance.due_date = timezone.make_aware(instance.due_date, timezone.get_current_timezone())

        if commit:
            instance.save()
        return instance




class BookReservationForm(forms.ModelForm):
    class Meta:
        model = BookReservation
        fields = ['book_number', 'borrower_uid_number', 'due_date', 'librarian_name']
        widgets = {
            'book_number': forms.TextInput(attrs={'autofocus': True}),
            'due_date': forms.TextInput(attrs={'readonly': 'readonly'}),
            'librarian_name': forms.TextInput(attrs={'readonly': 'readonly'}),
        }

    book_number = forms.CharField(max_length=20)
    borrower_uid_number = forms.CharField(max_length=20)

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super(BookReservationForm, self).__init__(*args, **kwargs)

        # Set the librarian name as usual
        if user:
            full_name = f"{user.first_name} {user.middle_name[0] if user.middle_name else ''}. {user.last_name}"
            self.fields['librarian_name'].initial = full_name

    def save(self, commit=True):
        instance = super().save(commit=False)

        # Ensure reservation_date, collected_date, and due_date are timezone-aware
        if not instance.reservation_date:
            instance.reservation_date = timezone.now()

        if instance.collected_date and timezone.is_naive(instance.collected_date):
            instance.collected_date = timezone.make_aware(instance.collected_date, timezone.get_current_timezone())

        if instance.due_date and timezone.is_naive(instance.due_date):
            instance.due_date = timezone.make_aware(instance.due_date, timezone.get_current_timezone())

        if commit:
            instance.save()
        return instance


        



#MARK: Attendance
# ============================================================================================================================================
# ===============================================================___LOG FORM___===============================================================
# ============================================================================================================================================

class AttendanceForm(forms.ModelForm):
    class Meta:
        model = Attendance
        fields = ['borrower_uid_number']
        widgets = {
            'borrower_uid_number': forms.PasswordInput(attrs={
                'class': 'input',  # Add your custom class for styling
                'placeholder': 'Enter your Borrower UID',  # Placeholder text
                'style': 'padding-left: 40px;',  # Inline styles, if needed
                'autofocus': True,
            }),
        }

    def clean_borrower_uid_number(self):
        borrower_uid = self.cleaned_data.get('borrower_uid_number')
        if not borrower_uid.startswith('hpdsnhs'):
            raise forms.ValidationError("Invalid Borrower UID format")
        return borrower_uid





#MARK: Monitoring
# ============================================================================================================================================
# ===============================================================___MONITORING FORM___========================================================
# ============================================================================================================================================

class PenaltyForm(forms.Form):
    ACTION_CHOICES = [
        ('warning', 'Issue Warning'),
        ('ban', 'Ban Borrower'),
        ('community_service', 'Community Service')
    ]
    
    action = forms.ChoiceField(choices=ACTION_CHOICES, required=True)
    ban_duration = forms.IntegerField(required=False, min_value=1, label="Ban Duration (days)")

    def clean(self):
        cleaned_data = super().clean()
        action = cleaned_data.get('action')
        ban_duration = cleaned_data.get('ban_duration')

        # Check for ban duration requirement if 'ban' action is selected
        if action == 'ban' and not ban_duration:
            self.add_error('ban_duration', 'Ban duration is required when banning a borrower.')

        return cleaned_data
