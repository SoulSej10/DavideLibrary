# ============================================================================================================================================
# =================================================================___IMPORTS__===============================================================
# ============================================================================================================================================
#MARK: Imports
from django import forms
from django.contrib.auth.models import User, Group
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.core.exceptions import ValidationError
from django.forms import ModelForm
from .models import Borrower, BookInventory, BorrowSlip, Attendance, CustomUser, Category
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth import authenticate
from django.contrib.auth import authenticate
from django.utils.translation import gettext_lazy as _




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
            'role': forms.Select(choices=CustomUser.ROLE_CHOICES, attrs={'id': 'role-field'}),  # Add 'id' here
        }
        

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
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])  # Ensure password is set correctly
        user.is_staff = user.role == 'Head Librarian'  # Set is_staff for head librarians
        if commit:
            user.save()
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
        ('others', 'Others'),
    ]
    grade_level = forms.ChoiceField(choices=GRADE_CHOICES, required=False)

    class Meta:
        model = Borrower
        exclude = ['borrower_uid', 'borrower_name','qr_code', 'date_issued']
    
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

        return super().save(commit)
        
        


#MARK: Inventory/Book
# ============================================================================================================================================
# ==============================================================___BOOK FORM___===============================================================
# ============================================================================================================================================
class BookInventoryForm(forms.ModelForm):
    firstname = forms.CharField(max_length=100, required=False)
    middle_initial = forms.CharField(max_length=2, required=False)
    lastname = forms.CharField(max_length=100, required=False)
    
    class Meta:
        model = BookInventory
        fields = ['class_field', 'book_title', 'edition', 'volume', 'pages', 'quantity', 'fund_source', 'price', 'publisher', 'year', 'category', 'remark', 'location']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
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
        firstname = self.cleaned_data.get('firstname', '').strip()
        middle_initial = self.cleaned_data.get('middle_initial', '').strip()
        lastname = self.cleaned_data.get('lastname', '').strip()
        
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
class BorrowSlipForm(forms.ModelForm):
    class Meta:
        model = BorrowSlip
        fields = ['book_number', 'date_borrow', 'borrower_uid_number', 'due_date', 'librarian_name']
        widgets = {
            'date_borrow': forms.TextInput(attrs={'readonly': 'readonly'}),
            'due_date': forms.TextInput(attrs={'readonly': 'readonly'}),
            'librarian_name': forms.TextInput(attrs={'readonly': 'readonly'}),
        }

    book_number = forms.CharField(max_length=20)
    borrower_uid_number = forms.CharField(max_length=20)

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super(BorrowSlipForm, self).__init__(*args, **kwargs)
        if user:
            full_name = f"{user.first_name} {user.middle_name[0] if user.middle_name else ''}. {user.last_name}"
            self.fields['librarian_name'].initial = full_name
        if not self.instance.pk:
            self.fields['date_borrow'].initial = timezone.now().date()
            self.fields['due_date'].initial = timezone.now().date() + timedelta(days=3)

    def save(self, commit=True):
        instance = super().save(commit=False)
        if not instance.pk:
            instance.date_borrow = self.cleaned_data.get('date_borrow', timezone.now().date())
            instance.due_date = self.cleaned_data.get('due_date', timezone.now().date() + timedelta(days=3))
        if commit:
            instance.save()
        return instance

        



#MARK: Attendance
# ============================================================================================================================================
# ===============================================================___LOG FORM___===============================================================
# ============================================================================================================================================
# class AttendanceForm(forms.ModelForm):
#     class Meta:
#         model = Attendance
#         fields = ['borrower_uid_number']

#     def clean_borrower_uid_number(self):
#         borrower_uid = self.cleaned_data.get('borrower_uid_number')
#         if not borrower_uid.startswith('hpdsnhs'):
#             raise forms.ValidationError("Invalid Borrower UID format")
#         return borrower_uid

class AttendanceForm(forms.ModelForm):
    class Meta:
        model = Attendance
        fields = ['borrower_uid_number']
        widgets = {
            'borrower_uid_number': forms.PasswordInput(attrs={
                'class': 'input',  # Add your custom class for styling
                'placeholder': 'Enter your Borrower UID',  # Placeholder text
                'style': 'padding-left: 40px;',  # Inline styles, if needed
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
# class PenaltyForm(forms.Form):
#     ACTION_CHOICES = [
#         ('replace', 'Replace Book'),
#         ('ban', 'Ban Student'),
#     ]
#     action = forms.ChoiceField(choices=ACTION_CHOICES, label="Choose an action")
#     ban_duration = forms.IntegerField(required=False, label="Ban Duration (days)", help_text="Only required if banning the student")
class PenaltyForm(forms.Form):
    ACTION_CHOICES = [
        ('replace', 'Replace Book'),
        ('ban', 'Ban Student'),
    ]
    
    action = forms.ChoiceField(choices=ACTION_CHOICES, required=True)
    ban_duration = forms.IntegerField(required=False, min_value=1, label="Ban Duration (days)")

    def clean(self):
        cleaned_data = super().clean()
        action = cleaned_data.get('action')
        ban_duration = cleaned_data.get('ban_duration')

        if action == 'ban' and not ban_duration:
            self.add_error('ban_duration', 'Ban duration is required when banning a student.')

        return cleaned_data