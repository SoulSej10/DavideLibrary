# ============================================================================================================================================
# ==========================================================___IMPORTS___====================++++++===========================================
# ============================================================================================================================================
#MARK: Imports
import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from .forms import CustomUserCreationForm, CustomAuthenticationForm
import os
from django.http import HttpResponse
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib.units import inch  
from reportlab.pdfgen import canvas
from reportlab.platypus import Table, TableStyle
from reportlab.lib import colors
from django.conf import settings
from django.db import models
from .models import  Borrower, BookInventory, BorrowSlip, Attendance, Category, CustomUser, Location, BookReservation
from .forms import  BorrowerForm, BookInventoryForm, BorrowSlipForm, AttendanceForm, PenaltyForm, BookReservationForm
from django.contrib import messages
from datetime import datetime
from django.utils import timezone  
from io import BytesIO
from django.template.loader import get_template
from django.db.models import Q, Count, Sum
from django.utils.timezone import now
from django.http import JsonResponse
import qrcode
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Image
from django.core.files.storage import default_storage
from django.http import FileResponse
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponseRedirect
import matplotlib
matplotlib.use('Agg')  # Set the backend to 'Agg' for non-interactive plotting
import matplotlib.pyplot as plt
import base64
import time
import uuid
from django.contrib.auth.decorators import login_required, user_passes_test
from django.urls import reverse
from django.contrib.auth.models import Group 
from django.http import HttpResponseForbidden
import calendar
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.views import LoginView
from django.urls import reverse_lazy
from django.contrib.auth.hashers import make_password
from django.core.files import File
from django.core.files.base import ContentFile
from datetime import timedelta
# from django.shortcuts import render, redirect
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.contrib.sites.shortcuts import get_current_site
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.template.loader import render_to_string
import random
import string
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import update_session_auth_hash
from django.shortcuts import render, redirect
from .forms import CustomPasswordResetForm
from django.db.models import ExpressionWrapper, F, IntegerField, DurationField
import datetime
from datetime import datetime 
#MARK: Landing Page
# ============================================================================================================================================
# ==================================================___LANDING PAGE VIEW___===============================================================
# ============================================================================================================================================
def landing(request):
    query = request.GET.get('q')
    category_name = request.GET.get('category')  # Get category name from query params
    book_number = request.GET.get('book_number')  # Get book number from query params
    books = BookInventory.objects.all()
    
    # Fetch all categories to display in the sidebar
    categories = Category.objects.all()

    # Filter by category if provided
    if category_name:
        books = books.filter(category__name=category_name)  # Filter by category

    # Search by title, author, or book number if query is provided
    if query:
        books = books.filter(
            Q(book_title__icontains=query) |
            Q(author__icontains=query) |
            Q(book_number__icontains=query)
        )

    # Determine book status based on BorrowSlip data
    for book in books:
        try:
            latest_borrow_slip = BorrowSlip.objects.filter(book_number=book.book_number).order_by('-date_borrow').first()
            current_date = timezone.now().date()

            if latest_borrow_slip:
                if latest_borrow_slip.due_date.date() < current_date and not latest_borrow_slip.returned:
                    book.status = 'Overdue'
                elif latest_borrow_slip.returned:
                    book.status = 'Returned'
                else:
                    book.status = 'Borrowed'
            else:
                book.status = 'Available'
        except BorrowSlip.DoesNotExist:
            book.status = 'Available'
    
    # Fetch the 10 most recent books
    recent_books = BookInventory.objects.order_by('-record_date')[:10]

    # Determine status for recent books
    for book in recent_books:
        try:
            latest_borrow_slip = BorrowSlip.objects.filter(book_number=book.book_number).order_by('-date_borrow').first()
            current_date = timezone.now().date()

            if latest_borrow_slip:
                if latest_borrow_slip.due_date.date() < current_date and not latest_borrow_slip.returned:
                    book.status = 'Overdue'
                elif latest_borrow_slip.returned:
                    book.status = 'Returned'
                else:
                    book.status = 'Borrowed'
            else:
                book.status = 'Available'
        except BorrowSlip.DoesNotExist:
            book.status = 'Available'

    # Handle book detail view
    book_detail = None
    if book_number:
        book_detail = get_object_or_404(BookInventory, book_number=book_number)
        # Determine the status of the book
        try:
            latest_borrow_slip = BorrowSlip.objects.filter(book_number=book_number).order_by('-date_borrow').first()
            current_date = timezone.now().date()

            if latest_borrow_slip:
                if latest_borrow_slip.due_date.date() < current_date and not latest_borrow_slip.returned:
                    book_detail.status = 'Overdue'
                elif latest_borrow_slip.returned:
                    book_detail.status = 'Returned'
                else:
                    book_detail.status = 'Borrowed'
            else:
                book_detail.status = 'Available'
        except BorrowSlip.DoesNotExist:
            book_detail.status = 'Available'

    # Data for the bar graph (count books by category)
    category_counts = BookInventory.objects.values('category__name').annotate(count=Count('book_number')).order_by('category__name')

    # Assign a unique color to each category
    categories_with_counts = [entry['category__name'] for entry in category_counts]
    counts = [entry['count'] for entry in category_counts]

    colors = plt.get_cmap('tab20').colors  # Use a colormap with enough distinct colors
    category_colors = dict(zip(categories_with_counts, colors))

    # Create the bar graph using matplotlib
    plt.figure(figsize=(14, 6))  # Increase figure width to accommodate legend
    bars = plt.bar(range(len(categories_with_counts)), counts, color=[category_colors[cat] for cat in categories_with_counts])
    plt.xlabel('Category')
    plt.ylabel('Number of Books')
    plt.title('Number of Books by Category')

    # Set the x-ticks and labels
    plt.xticks(range(len(categories_with_counts)), [''] * len(categories_with_counts))  # Empty labels for now

    # Add a legend to the plot outside the plot area
    handles = [plt.Line2D([0], [0], color=color, lw=4) for color in category_colors.values()]
    plt.legend(handles, category_colors.keys(), loc='center left', bbox_to_anchor=(1, 0.5))

    # Save the plot to a BytesIO object
    buffer = BytesIO()
    plt.savefig(buffer, format='png', bbox_inches='tight')
    buffer.seek(0)
    image_png = buffer.getvalue()
    buffer.close()

    # Encode the image to base64 string
    graph = base64.b64encode(image_png).decode('utf-8')

    return render(request, 'library/landing.html', {
        'books': books,  # Pass filtered books to the template
        'query': query,
        'recent_books': recent_books,
        'book_detail': book_detail,
        'graph': graph,
        'categories': categories,
        'category_name': category_name,  # Pass the category name to the template
    })

def book_detail(request, book_number):
    book = get_object_or_404(BookInventory, book_number=book_number)
    return render(request, 'landing.html', {
        'book_detail': book,
        'query': request.GET.get('q', ''),  # Preserve the search query
    })

def borrow_history(request):
    uid = request.GET.get('uid')
    response_data = {
        'full_name': '',
        'status': '',  # Add status here
        'history': [],
        'qr_code': ''
    }

    if uid:
        try:
            # Fetch the borrower using the UID
            borrower = Borrower.objects.get(borrower_uid=uid)
            response_data['full_name'] = borrower.borrower_name
            response_data['status'] = borrower.status  # Add the borrower's status to the response
            response_data['qr_code'] = borrower.qr_code.url  # Get QR code URL

            # Fetch all borrow slips associated with the UID
            borrow_slips = BorrowSlip.objects.filter(borrower_uid_number=uid)
            for slip in borrow_slips:
                response_data['history'].append({
                    'book_number': slip.book_number,
                    'book_title': slip.book_title,
                    'date_borrow': slip.date_borrow.strftime('%Y-%m-%d'),
                    'due_date': slip.due_date.strftime('%Y-%m-%d'),
                    'status': slip.status
                })

        except Borrower.DoesNotExist:
            response_data['full_name'] = 'UID not found'

    return JsonResponse(response_data)


def landingLog(request):
    form = AttendanceForm()
    return render(request, 'library/landing_attendance.html', {'form': form})

import logging

logger = logging.getLogger(__name__)

def log_attendance(request):
    if request.method == 'POST':
        form = AttendanceForm(request.POST)
        if form.is_valid():
            borrower_uid = form.cleaned_data['borrower_uid_number']
            borrower = Borrower.objects.filter(borrower_uid=borrower_uid).first()
            if borrower:
                attendance = form.save(commit=False)
                attendance.borrower_name = borrower.borrower_name
                attendance.grade_level = borrower.grade_level
                attendance.section = borrower.section
                attendance.save()
                return JsonResponse({'borrower_name': borrower.borrower_name})
            else:
                logger.error("Borrower not found for UID: %s", borrower_uid)
                return JsonResponse({'error': 'Borrower not found.'}, status=404)
        else:
            logger.error("Form errors: %s", form.errors)
            return JsonResponse({'errors': form.errors}, status=400)
    else:
        form = AttendanceForm()
    return render(request, 'library/landing_attendance.html', {'form': form})







#MARK: Login
# ============================================================================================================================================
# ==================================================___LOG IN/ REGISTER VIEW___===============================================================
# ============================================================================================================================================
# Helper function to check if user is head librarian
# Utility function to check if user is a Head Librarian
def is_head_librarian(user):
    return user.role == 'Head Librarian'

# Head Librarian Login View
class HeadLibrarianLoginView(LoginView):
    template_name = 'library/LogRegister.html'
    form_class = AuthenticationForm
    success_url = reverse_lazy('home')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['login_type'] = 'Head Librarian'  # Sets login type for template
        return context

    def form_valid(self, form):
        user = form.get_user()
        if user.is_staff:
            login(self.request, user)
            messages.success(self.request, "Permission Granted, Account Authorized!")
            return redirect(self.success_url)
        else:
            messages.error(self.request, "Permission Denied. LOWER access level accounts can't view this page.")
            return redirect('head_librarian_login')  # Redirect to the same page to show the error message

# Assistant Librarian Login View
class AssistantLibrarianLoginView(LoginView):
    template_name = 'library/LogRegister.html'
    form_class = AuthenticationForm
    success_url = reverse_lazy('home')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['login_type'] = 'Assistant Librarian'  # Sets login type for template
        return context

    def form_valid(self, form):
        user = form.get_user()
        if not user.is_staff and not user.is_superuser:
            login(self.request, user)
            messages.success(self.request, "Permission Granted, Account Authorized!")
            return redirect(self.success_url)
        else:
            messages.error(self.request, "Permission Denied. HIGHER access level accounts can't view this page.")
            return redirect('assistant_librarian_login') 

# Directory view
def directory(request):
    return render(request, 'library/directory.html')

def login_view(request):
    if request.method == 'POST':
        form = CustomAuthenticationForm(request, data=request.POST)
        
        if form.is_valid():
            # Retrieve cleaned data
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            admin_id = form.cleaned_data.get('admin_id')
            
            try:
                # Fetch the user from the database
                user = CustomUser.objects.get(username=username)
                
                # Check if the password matches the temporary password
                if user.temporary_password == password:
                    # If the user is using the temporary password, authenticate them manually
                    login(request, user)
                    
                    # Display a message prompting the user to change their password
                    messages.warning(request, 'You are using a temporary password. Please change your password.')
                    return redirect('change_password')  # Redirect to the password change page
                
                # Otherwise, authenticate the user with the usual credentials
                user = authenticate(request, username=username, password=password)
                
                if user is not None and user.admin_id == admin_id:
                    login(request, user)
                    
                    messages.success(request, 'Login successful.')
                    return redirect('home')
                else:
                    messages.error(request, 'Invalid credentials or admin ID.')
            except CustomUser.DoesNotExist:
                messages.error(request, 'User does not exist.')
        else:
            messages.error(request, 'Login failed. Please check your details.')

    else:
        form = CustomAuthenticationForm()

    return render(request, 'library/LogRegister.html', {'form': form})


# Logout view
def logout_view(request):
    logout(request)
    messages.success(request, "You have been logged out successfully.")
    return redirect('landing')

# Registration view (only accessible to Head Librarians)
@login_required
@user_passes_test(is_head_librarian)
def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Ensure admin_id is generated
            if user.admin_id:
                messages.success(request, 'Assistant Librarian registered successfully.')
                return redirect('register')
            else:
                messages.error(request, 'Failed to generate admin_id.')
            
    else:
        form = CustomUserCreationForm()

    all_users = CustomUser.objects.all()
    head_librarians = all_users.filter(is_staff=True)
    assistant_librarians = all_users.filter(is_staff=False)

    context = {
        'form': form,
        'head_librarians': head_librarians,
        'assistant_librarians': assistant_librarians,
        'user': request.user,  # Ensure user object is available in template
    }

    return render(request, 'library/RegisterLog.html', context)

def user_details(request, user_id):
    user = get_object_or_404(CustomUser, id=user_id)
    user_data = {
        'full_name': f"{user.first_name} {user.middle_name} {user.last_name}",
        'admin_id': user.admin_id,
        'username': user.username,
        'hashed_password': user.password,  # This shows the hashed password.
    }
    return JsonResponse(user_data)


def generate_account_pdf(request, admin_id):
    # Get the selected account using admin_id
    account = CustomUser.objects.get(admin_id=admin_id)

    # Check if the account already has a QR code
    if not account.qr_code:
        # Generate a new QR code for the account
        qr = qrcode.make(account.admin_id)
        qr_image = BytesIO()
        qr.save(qr_image, format='PNG')
        qr_image.seek(0)

        # Save the QR code to the account's `qr_code` field
        account.qr_code.save(f"{account.admin_id}_qr.png", File(qr_image))
        account.save()

    # Create a response object with PDF content type
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{account.username}_account.pdf"'

    # Create PDF canvas
    p = canvas.Canvas(response, pagesize=letter)
    width, height = letter

    # Set font size
    p.setFont("Helvetica", 10)

    # Define the initial position for an ID-like layout
    id_card_width = 3.5 * inch  # Adjusted width for a more compact ID size
    id_card_height = 2.25 * inch  # Adjusted height for a more compact ID size
    margin_left = 0.5 * inch  # Centered horizontally on the page
    margin_top = height - .8 * inch  # Adjust position from the top of the page
    row_height = id_card_height  # Make the rectangle height match ID height

    # Draw rectangle border around account data
    p.rect(margin_left, margin_top - row_height, id_card_width, row_height)

    # Draw QR code within the ID rectangle
    qr_code_x = margin_left + 10  # Adjusted X position for padding
    qr_code_y = margin_top - 1.7 * inch  # Position QR code inside the ID
    qr_code_size = 80  # Adjust size to fit within the ID card

    qr_code_path = os.path.join(settings.MEDIA_ROOT, account.qr_code.name)
    p.drawImage(qr_code_path, qr_code_x, qr_code_y, width=qr_code_size, height=qr_code_size)

    # Position text to the right of QR code
    text_start_x = qr_code_x + qr_code_size + 10  # Spacing between QR and text
    text_start_y = margin_top - 60  # Adjust Y position for better alignment
    line_height = 12  # Adjusted line height for compact spacing

    # Add account details in a compact format
    p.drawString(text_start_x, text_start_y, f"Admin ID: {account.admin_id}")
    p.drawString(text_start_x, text_start_y - line_height, f"Username: {account.username}")
    p.drawString(text_start_x, text_start_y - 2 * line_height, f"Full Name: {account.first_name} {account.middle_name} {account.last_name}")
    p.drawString(text_start_x, text_start_y - 3 * line_height, f"Role: {account.get_role_display()}")

    # Save the PDF
    p.save()
    return response

# Generate a random temporary password
def generate_temporary_password():
    return ''.join(random.choices(string.ascii_letters + string.digits, k=8))

def request_password_reset(request):
    temp_password = None  # Initialize to None in case no password has been generated yet

    if request.method == "POST":
        username = request.POST.get('username')
        try:
            user = CustomUser.objects.get(username=username)
        except CustomUser.DoesNotExist:
            # If the user does not exist, handle the error gracefully
            return render(request, 'library/request.html', {'error': 'User does not exist'})

        # Generate temporary password
        temp_password = generate_temporary_password()
        user.temporary_password = temp_password
        user.save()

        # Pass the temporary password to the template
        return render(request, 'library/request.html', {'temp_password': temp_password})

    return render(request, 'library/request.html', {'temp_password': temp_password})

def validate_username(request):
    if request.method == "POST":
        data = json.loads(request.body)
        username = data.get("username", "").strip()

        if CustomUser.objects.filter(username=username).exists():
            return JsonResponse({"is_valid": True})
        else:
            return JsonResponse({"is_valid": False})

    return JsonResponse({"error": "Invalid request method"}, status=400)
    

def change_password(request):
    if request.method == 'POST':
        form = CustomPasswordResetForm(request.POST)
        if form.is_valid():
            user = request.user  

            new_password = form.cleaned_data['new_password1']
            user.set_password(new_password)
            user.save()

            update_session_auth_hash(request, user)

            user.temporary_password = None
            user.save()

            messages.success(request, 'Your password has been successfully changed!')
            return redirect('home')  
    else:
        form = CustomPasswordResetForm()

    return render(request, 'library/password_change.html', {'form': form})


def temporary_login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        temp_password = request.POST.get('temporary_password')

        try:
            # Fetch the user based on the username
            user = CustomUser.objects.get(username=username)

            # Check if the entered temporary password matches
            if user.temporary_password == temp_password:
                # Log the user in
                login(request, user)

                # Clear the temporary password to prevent reuse
                user.temporary_password = None
                user.save()

                # Redirect to password change page
                return redirect('change_password')
            else:
                messages.error(request, 'Invalid temporary password.')
        except CustomUser.DoesNotExist:
            messages.error(request, 'User does not exist.')

    return render(request, 'library/temporary_login.html')

@csrf_exempt  # Use only for debugging; remove in production for security
def validate_uid(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            uid = data.get("uid", "").strip()

            if not uid:
                return JsonResponse({"is_valid": False, "error": "UID is required."})

            # Check if admin_id (formerly uid) exists in the database
            if CustomUser.objects.filter(admin_id=uid).exists():
                return JsonResponse({"is_valid": True})
            else:
                return JsonResponse({"is_valid": False, "error": "UID does not exist."})
        except json.JSONDecodeError:
            return JsonResponse({"is_valid": False, "error": "Invalid JSON format."}, status=400)
        except Exception as e:
            return JsonResponse({"is_valid": False, "error": f"Unexpected error: {str(e)}"}, status=500)

    return JsonResponse({"is_valid": False, "error": "Invalid request method."}, status=405)










#MARK: Home

@login_required
def home(request):
    query = request.GET.get('q')
    book_number = request.GET.get('book_number')  # Get book number from query params
    books = BookInventory.objects.all()
    
    if not request.user.is_authenticated:
        return redirect('directory')

    if query:
        # Search by title, author, or book number
        books = books.filter(
            Q(book_title__icontains=query) |
            Q(author__icontains=query) |
            Q(book_number__icontains=query)
        )

    # Determine book status based on BorrowSlip data
    for book in books:
        try:
            latest_borrow_slip = BorrowSlip.objects.filter(book_number=book.book_number).order_by('-date_borrow').first()
            current_date = timezone.now().date()

            if latest_borrow_slip:
                if latest_borrow_slip.due_date.date() < current_date and not latest_borrow_slip.returned:
                    book.status = 'Overdue'
                elif latest_borrow_slip.returned:
                    book.status = 'Returned'
                else:
                    book.status = 'Borrowed'
            else:
                book.status = 'Available'
        except BorrowSlip.DoesNotExist:
            book.status = 'Available'
    
    # Fetch the 10 most recent books
    recent_books = BookInventory.objects.order_by('-record_date')[:10]

    # Determine status for recent books
    for book in recent_books:
        try:
            latest_borrow_slip = BorrowSlip.objects.filter(book_number=book.book_number).order_by('-date_borrow').first()
            current_date = timezone.now().date()

            if latest_borrow_slip:
                if latest_borrow_slip.due_date.date() < current_date and not latest_borrow_slip.returned:
                    book.status = 'Overdue'
                elif latest_borrow_slip.returned:
                    book.status = 'Returned'
                else:
                    book.status = 'Borrowed'
            else:
                book.status = 'Available'
        except BorrowSlip.DoesNotExist:
            book.status = 'Available'

    book_detail = None
    if book_number:
        book_detail = get_object_or_404(BookInventory, book_number=book_number)
        # Determine the status of the book
        try:
            latest_borrow_slip = BorrowSlip.objects.filter(book_number=book_number).order_by('-date_borrow').first()
            current_date = timezone.now().date()

            if latest_borrow_slip:
                if latest_borrow_slip.due_date.date() < current_date and not latest_borrow_slip.returned:
                    book_detail.status = 'Overdue'
                elif latest_borrow_slip.returned:
                    book_detail.status = 'Returned'
                else:
                    book_detail.status = 'Borrowed'
            else:
                book_detail.status = 'Available'
        except BorrowSlip.DoesNotExist:
            book_detail.status = 'Available'

    # Data for the bar graph
    category_counts = BookInventory.objects.values('category__name').annotate(count=Count('book_number')).order_by('category__name')
    categories = [entry['category__name'] for entry in category_counts]
    counts = [entry['count'] for entry in category_counts]

    # Calculate total books across all categories
    total_books = sum(counts) 

    # Assign a unique color to each category
    colors = plt.get_cmap('tab20').colors  # Use a colormap with enough distinct colors
    category_colors = dict(zip(categories, colors))

    # Create the bar graph using matplotlib
    plt.figure(figsize=(14, 6))  # Increase figure width to accommodate legend
    bars = plt.bar(range(len(categories)), counts, color=[category_colors[cat] for cat in categories])
    plt.xlabel('Category')
    plt.ylabel('Number of Books')
    plt.title('Number of Books by Category')

    # Set the x-ticks and labels
    plt.xticks(range(len(categories)), [''] * len(categories))  # Empty labels for now
    plt.gca().yaxis.get_major_locator().set_params(integer=True)

    # Add a legend to the plot outside the plot area
    handles = [plt.Line2D([0], [0], color=color, lw=4) for color in category_colors.values()]
    plt.legend(handles, category_colors.keys(), loc='center left', bbox_to_anchor=(1, 0.5))

    # Save the plot to a BytesIO object
    buffer = BytesIO()
    plt.savefig(buffer, format='png', bbox_inches='tight')
    buffer.seek(0)
    image_png = buffer.getvalue()
    buffer.close()

    # Encode the image to base64 string
    graph = base64.b64encode(image_png).decode('utf-8')

    return render(request, 'library/home.html', {
        'books': books,
        'query': query,
        'recent_books': recent_books,
        'book_detail': book_detail,
        'graph': graph,  # Pass the graph image to the template
        'total_books': total_books  # Pass the total book count
    })


def book_detail(request, book_number):
    book = get_object_or_404(BookInventory, book_number=book_number)
    return render(request, 'home.html', {
        'book_detail': book,
        'query': request.GET.get('q', ''),  # Preserve the search query
    })




def book_details(request, book_number):
    # Get the book instance
    book = get_object_or_404(BookInventory, book_number=book_number)

    # Calculate statuses directly based on database records
    total_quantity = book.quantity

    borrowed_count = BorrowSlip.objects.filter(book_number=book_number, status='Borrowed').count()
    reserved_count = BookReservation.objects.filter(book_number=book_number, status='Reserved').count()
    overdue_count = BorrowSlip.objects.filter(book_number=book_number, status='Overdue').count()
    lost_count = BorrowSlip.objects.filter(book_number=book_number, status='Lost').count()

    # Available copies based on quantity and existing records
    unavailable_copies = borrowed_count + reserved_count + overdue_count + lost_count
    available_count = total_quantity - unavailable_copies

    # Ensure available copies do not go below 0
    available_count = max(available_count, 0)

    # Return the status counts as JSON data
    data = {
        'book_title': book.book_title,
        'status_counts': {
            'Available': available_count,
            'Borrowed': borrowed_count,
            'Reserved': reserved_count,
            'Overdue': overdue_count,
            'Lost': lost_count,
        },
    }

    return JsonResponse(data)








#MARK: Student
# ============================================================================================================================================
# ==================================================___STUDENT/BORROWER MANANGEMENT VIEW___===================================================
# ============================================================================================================================================
@login_required
def borrower_list(request):
    query = request.GET.get('search', '')
    grade_filter = request.GET.get('grade', '')
    form = BorrowerForm()

    if request.method == 'POST' and 'action' in request.POST:
        action = request.POST.get('action')
        selected_ids = request.POST.getlist('selected_borrowers')

        if action == 'delete':
            Borrower.objects.filter(borrower_uid__in=selected_ids).delete()
            return redirect('borrower-list')
        elif action == 'download_pdf':
            return generate_selected_borrowers_pdf(selected_ids)

    borrowers = Borrower.objects.all().order_by('-date_issued')

    if query:
        borrowers = borrowers.filter(borrower_uid__icontains=query)

    if grade_filter and grade_filter != '':
        if grade_filter == 'others':
            borrowers = borrowers.exclude(grade_level__in=['7', '8', '9', '10', '11', '12'])
        else:
            borrowers = borrowers.filter(grade_level=grade_filter)

    return render(request, 'library/borrower_list.html', {
        'borrowers': borrowers,
        'query': query,
        'form': form,
        'grade_filter': grade_filter,
    })


@login_required
def edit_borrower(request, pk):
    borrower = get_object_or_404(Borrower, borrower_uid=pk)
    if request.method == 'POST':
        form = BorrowerForm(request.POST, instance=borrower)
        if form.is_valid():
            form.save()
            return redirect('borrower-list')
    else:
        form = BorrowerForm(instance=borrower)

    borrowers = Borrower.objects.all().order_by('-date_issued')
    context = {
        'form': form,
        'borrowers': borrowers,
        'query': '',  # Add the search query if needed
    }
    return render(request, 'library/borrower_list.html', context)


def delete_borrower(request, pk):
    borrower = get_object_or_404(Borrower, borrower_uid=pk)
    if request.method == 'POST':
        borrower.delete()
        messages.success(request, f"Borrower {borrower.borrower_name} deleted successfully.")
        return redirect('borrower-list')
    
    # Fallback if it's a GET request
    borrowers = Borrower.objects.all().order_by('-date_issued')
    return render(request, 'library/borrower_list.html', {'borrowers': borrowers, 'query': '', 'form': BorrowerForm()})

@login_required
def delete_multiple_borrowers(request):
    if request.method == 'POST':
        selected_ids = request.POST.get('selected_ids', '').split(',')
        if selected_ids:
            borrowers = Borrower.objects.filter(borrower_uid__in=selected_ids)
            count = borrowers.count()
            borrowers.delete()
            messages.success(request, f"{count} borrower(s) deleted successfully.")
        else:
            messages.error(request, "No borrowers selected for deletion.")
    
    return redirect('borrower-list')

@login_required
def borrower_create(request):
    if request.method == 'POST':
        form = BorrowerForm(request.POST)
        if form.is_valid():
            borrower = form.save(commit=False)
            borrower.date_issued = timezone.now()  # Set the current date and time
            borrower.save()
            return redirect('borrower-list')
    else:
        form = BorrowerForm()
    borrowers = Borrower.objects.all().order_by('-date_issued')
    return render(request, 'library/borrower_list.html', {'borrowers': borrowers, 'query': '', 'form': form})



def generate_uid_pdf(request, pk):
    borrower = Borrower.objects.get(pk=pk)
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{borrower.borrower_uid}.pdf"'

    # ID card dimensions
    id_width, id_height = 3.375 * inch, 2.125 * inch
    p = canvas.Canvas(response, pagesize=landscape((id_width, id_height)))

    qr_code_path = os.path.join(settings.MEDIA_ROOT, borrower.qr_code.name)
    p.drawImage(qr_code_path, 10, id_height - 110, width=100, height=100)

    text_start_x = 120
    text_start_y = id_height - 30
    line_height = 15

    p.drawString(10, id_height - 130, "Borrower UID:")
    p.drawString(10, id_height - 145, f"{borrower.borrower_uid}")

    p.drawString(text_start_x, text_start_y, f"Name: {borrower.borrower_name}")
    p.drawString(text_start_x, text_start_y - line_height, f"Age: {borrower.age}")
    p.drawString(text_start_x, text_start_y - 2 * line_height, f"Grade Level: {borrower.grade_level}")
    p.drawString(text_start_x, text_start_y - 3 * line_height, f"Section: {borrower.section}")
    p.drawString(text_start_x, text_start_y - 4 * line_height, f"Adviser: {borrower.adviser}")
    p.drawString(text_start_x, text_start_y - 5 * line_height, f"Date Issued:")
    p.drawString(text_start_x, text_start_y - 6 * line_height, f"{borrower.date_issued.date()}")

    p.showPage()
    p.save()
    return response


def generate_selected_borrowers_pdf(selected_ids):
    # Get selected borrowers
    borrowers = Borrower.objects.filter(borrower_uid__in=selected_ids)
    
    # Create a response object with PDF content type
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="selected_borrowers.pdf"'

    # Create PDF canvas
    p = canvas.Canvas(response, pagesize=letter)
    width, height = letter

    # Set font size
    p.setFont("Helvetica", 10)

    # Define margins and initial position
    margin_left = 0.3 * inch
    margin_top = height - 0.2 * inch
    margin_right = width - 0.3 * inch
    margin_bottom = 0.5 * inch
    current_x = margin_left
    current_y = margin_top
    row_height = 2.5 * inch  # Adjusted height for each row
    column_width = (width - 2 * margin_left) / 2  # Two columns

    # Draw each borrower's details
    for index, borrower in enumerate(borrowers):
        if current_y - row_height < margin_bottom:
            p.showPage()
            current_y = margin_top
            current_x = margin_left

        # Draw rectangle border around borrower's data
        p.rect(current_x, current_y - row_height, column_width, row_height)

        # Adjust QR code position to be closer to the text
        qr_code_path = os.path.join(settings.MEDIA_ROOT, borrower.qr_code.name)
        p.drawImage(qr_code_path, current_x + 10, current_y - 110, width=80, height=80)  # Moved QR code up

        # Move text position slightly down
        text_start_x = current_x + 100  # Moved text position closer to QR code
        text_start_y = current_y - 50  # Move text down by 20 points to avoid overlapping with top line
        line_height = 15

        p.drawString(text_start_x, text_start_y, f"Borrower UID: {borrower.borrower_uid}")
        p.drawString(text_start_x, text_start_y - line_height, f"Name: {borrower.borrower_name}")
        p.drawString(text_start_x, text_start_y - 2 * line_height, f"Age: {borrower.age}")
        p.drawString(text_start_x, text_start_y - 3 * line_height, f"Grade Level: {borrower.grade_level}")
        p.drawString(text_start_x, text_start_y - 4 * line_height, f"Section: {borrower.section}")
        p.drawString(text_start_x, text_start_y - 5 * line_height, f"Adviser: {borrower.adviser}")
        p.drawString(text_start_x, text_start_y - 6 * line_height, f"Date Issued: {borrower.date_issued.date()}")

        # Move to the next column if space runs out
        if index % 2 == 1:  # 2 columns
            current_x = margin_left
            current_y -= row_height
        else:
            current_x = margin_left + column_width

    # Save the PDF
    p.save()
    return response










#MARK: Inventory
# ============================================================================================================================================
# ==================================================___BOOK MANANGEMENT VIEW___===============================================================
# ============================================================================================================================================
@user_passes_test(is_head_librarian)
@login_required
def book_list(request):
    query = request.GET.get('search', '')
    category_name = request.GET.get('category', '')
    form = BookInventoryForm()

    if request.method == 'POST':
        if 'add-category' in request.POST:
            category_name = request.POST.get('category_name')
            if category_name:
                Category.objects.get_or_create(name=category_name)
            return redirect('book-list')
        elif 'delete-selected' in request.POST:
            selected_books = request.POST.getlist('selected_books')
            if selected_books:
                BookInventory.objects.filter(book_number__in=selected_books).delete()
            return redirect('book-list')
        elif 'set-location' in request.POST:  # Handle setting location
            location_id = request.POST.get('location')
            selected_books = request.POST.getlist('selected_books')

            if location_id and selected_books:
                try:
                    location = Location.objects.get(id=location_id)
                    BookInventory.objects.filter(book_number__in=selected_books).update(location=location)
                except Location.DoesNotExist:
                    messages.error(request, "Invalid location selected.")
            return redirect('book-list')
        elif 'add-location' in request.POST:  # Handle adding a new location
            location_name = request.POST.get('new_location')
            if location_name:
                Location.objects.get_or_create(name=location_name)
            return redirect('book-list')

    # Fetch categories and locations
    categories = Category.objects.all()
    locations = Location.objects.all()

    # Filter books based on query or category
    if query:
        books = BookInventory.objects.filter(
            models.Q(book_number__icontains=query) | models.Q(book_title__icontains=query)
        ).order_by('-record_date')
    elif category_name:
        books = BookInventory.objects.filter(category__name=category_name).order_by('-record_date')
    else:
        books = BookInventory.objects.all().order_by('-record_date')

    # Ensure QR codes are generated for all books
    for book in books:
        if not book.qr_code:
            book.save()  # This will trigger the QR code generation logic in the `save` method

    no_results = not books.exists() if query else False

    if 'download_pdf' in request.GET:
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="books.pdf"'

        p = canvas.Canvas(response, pagesize=letter)

        # Create a temporary folder for QR codes
        temp_dir = os.path.join(settings.MEDIA_ROOT, 'qr_codes')
        os.makedirs(temp_dir, exist_ok=True)

        for book in books:
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(book.book_number)
            qr.make(fit=True)

            qr_image = qr.make_image(fill='black', back_color='white')
            qr_image_bytes = BytesIO()
            qr_image.save(qr_image_bytes)

            qr_code_path = os.path.join(temp_dir, f"{book.book_number}.png")

            with open(qr_code_path, 'wb') as f:
                f.write(qr_image_bytes.getvalue())

            p.drawImage(qr_code_path, 10, 750, width=100, height=100)

            p.drawString(120, 800, f"Book Number: {book.book_number}")
            p.drawString(120, 780, f"Title: {book.book_title}")

            # Move to next page if necessary
            p.showPage()

        p.save()

        # Clean up temporary files
        for filename in os.listdir(temp_dir):
            file_path = os.path.join(temp_dir, filename)
            os.remove(file_path)
        os.rmdir(temp_dir)

        return response

    context = {
        'books': books,
        'query': query,
        'category': category_name,
        'form': form,
        'categories': categories,
        'locations': locations,  # Pass locations to template
        'no_results': no_results,
    }
    return render(request, 'library/book_list.html', context)



@login_required
def book_create(request):
    if request.method == 'POST':
        if 'add-category' in request.POST:  # Handle adding a new category
            category_name = request.POST.get('category_name')
            if category_name:
                Category.objects.get_or_create(name=category_name)
                return redirect('book-create')  # Redirect to avoid re-posting the form
        else:
            form = BookInventoryForm(request.POST)
            if form.is_valid():
                # Save the book with the location (new or existing)
                form.save()
                return redirect('book-list')
    else:
        form = BookInventoryForm()

    categories = Category.objects.all()
    locations = Location.objects.all()  # Include locations for the dropdown
    return render(
        request,
        'library/book_form.html',
        {'form': form, 'categories': categories, 'locations': locations}
    )


@login_required
def book_update(request, book_number):
    book = get_object_or_404(BookInventory, book_number=book_number)
    
    if request.method == 'POST':
        form = BookInventoryForm(request.POST, instance=book)
        if form.is_valid():
            form.save()
            return redirect('book-list')
    else:
        form = BookInventoryForm(instance=book)
    
    locations = Location.objects.all()  # Fetch all locations
    categories = Category.objects.all()  # Fetch all categories
    return render(request, 'library/book_form.html', {'form': form, 'categories': categories, 'locations': locations})


@login_required
def delete_category(request, category_id):
    category = get_object_or_404(Category, id=category_id)
    if request.method == 'POST':
        category.delete()
        return redirect('book-create')  # Redirect to the book creation view after deletion
    return redirect('book-create')  # Redirect to the book creation view if not POST request

def delete_selected_books(request):
    if request.method == 'POST':
        book_numbers = request.POST.getlist('selected_books')
        if not book_numbers:
            messages.error(request, 'No books selected for deletion.')
        else:
            BookInventory.objects.filter(book_number__in=book_numbers).delete()
            messages.success(request, 'Selected books have been deleted.')
    return redirect('book-list')

def set_location_for_books(request):
    if request.method == 'POST':
        selected_books = request.POST.getlist('selected_books')
        location = request.POST.get('location')

        if not selected_books or not location:
            messages.error(request, "No books selected or location not provided.")
            return redirect('book-list')

        books = BookInventory.objects.filter(book_number__in=selected_books)
        for book in books:
            book.location = location
            book.save()

        messages.success(request, f"Set location to {location} for {len(selected_books)} book(s).")
    
    return redirect('book-list')

@login_required
def book_detail(request, book_number):
    # Retrieve the book by book_number
    book = get_object_or_404(BookInventory, book_number=book_number)

    # Create a dictionary of book details
    book_data = {
        'book_number': book.book_number,
        'author': book.author,
        'book_title': book.book_title,
        'edition': book.edition,
        'volume': book.volume,
        'pages': book.pages,
        'quantity': book.quantity,
        'fund_source': book.fund_source,
        'price': book.price,
        'publisher': book.publisher,
        'year': book.year,
        'remark': book.remark,
        'book_type': book.book_type,
        'category': book.category.name,  # assuming category is related to the Category model
    }

    # Return the data as JSON
    return JsonResponse(book_data)


def generate_selected_books_pdf(request):
    # Get selected book numbers from the POST request
    selected_book_numbers = request.POST.getlist('selected_books')
    books = BookInventory.objects.filter(book_number__in=selected_book_numbers)

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    elements = []

    # Define table data and style
    data = [['QR Code', 'Book Number', 'Book Title']]
    styles = getSampleStyleSheet()
    styleN = ParagraphStyle(
        name='Normal',
        fontName='Helvetica',
        fontSize=10,
    )

    for book in books:
        # Get QR code path
        qr_code_path = default_storage.path(book.qr_code.name) if book.qr_code else ''
        
        # Create an Image object for QR code if it exists
        if qr_code_path and default_storage.exists(qr_code_path):
            qr_code_image = Image(qr_code_path, width=50, height=50)
        else:
            qr_code_image = ''
        
        # Add book data to table
        data.append([
            qr_code_image,
            book.book_number,
            Paragraph(book.book_title, styleN)
        ])

    table = Table(data, colWidths=[60, 100, 300])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))

    elements.append(table)
    doc.build(elements)

    buffer.seek(0)
    return FileResponse(buffer, as_attachment=True, filename='selected_books.pdf')

@login_required
def add_location(request):
    if request.method == 'POST':
        import json
        data = json.loads(request.body)
        location_name = data.get('name')

        if location_name:
            location, created = Location.objects.get_or_create(name=location_name)
            return JsonResponse({'success': True, 'location_id': location.id})
        else:
            return JsonResponse({'success': False, 'message': 'Invalid location name.'})
    return JsonResponse({'success': False, 'message': 'Invalid request method.'})






#MARK: Slip
# ============================================================================================================================================
# =======================================================__SLIP MANANGEMENT VIEW___===========================================================
# ============================================================================================================================================
import io
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
@login_required
def borrow_slip_list(request):
    query = request.GET.get('search', '')
    sort_order = request.GET.get('sort', '-slip_number')  # Sort by slip_number by default (highest first)
    form = BorrowSlipForm()

    # Handle date filter
    date_filter = request.GET.get('date_filter', '')
    if date_filter:
        try:
            date_filter = datetime.strptime(date_filter, '%Y-%m-%d').date()
            borrow_slips = BorrowSlip.objects.filter(date_borrow=date_filter).order_by(sort_order)
        except ValueError:
            borrow_slips = BorrowSlip.objects.none()
    else:
        borrow_slips = BorrowSlip.objects.all().order_by(sort_order)

    # Handle form submission for creating new borrow slip
    if request.method == 'POST':
        form = BorrowSlipForm(request.POST)
        if form.is_valid():
            borrow_slip = form.save(commit=False)
            borrow_slip.date_borrow = timezone.now().date()  # Make date_borrow timezone-aware
            borrow_slip.save()
            return redirect('borrow-slip-list')

    # Handle search query
    if query:
        borrow_slips = borrow_slips.filter(
            Q(book_number__icontains=query) |
            Q(borrower_uid_number__icontains=query) |
            Q(librarian_name__icontains=query)
        )

    context = {
        'borrow_slips': borrow_slips,
        'query': query,
        'form': form,
        'sort_order': sort_order,
        'date_filter': date_filter,
    }
    return render(request, 'library/borrow_slip_list.html', context)



@login_required
def download_selected_pdf(request):
    selected_slips = request.POST.getlist('selected_slips')
    if not selected_slips:
        return redirect('borrow-slip-list')

    # Retrieve BorrowSlip objects based on slip numbers
    borrow_slips = BorrowSlip.objects.filter(slip_number__in=selected_slips)

    buffer = io.BytesIO()
    # Set up document for landscape orientation
    doc = SimpleDocTemplate(buffer, pagesize=landscape(letter), rightMargin=30, leftMargin=30, topMargin=50, bottomMargin=50)

    table_data = [["Slip No.", "Book Borrowed", "Author", "Book Number", "Date Borrow", "Borrower Name", "Due Date", "Librarian Name"]]

    for slip in borrow_slips:
        table_data.append([
            slip.slip_number,
            slip.book_title,
            slip.author,
            slip.book_number,
            slip.date_borrow.strftime('%Y-%m-%d'),
            slip.borrower_name,
            slip.due_date.strftime('%Y-%m-%d'),
            slip.librarian_name
        ])

    # Define column widths
    col_widths = [40, 110, 120, 70, 90, 120, 70, 100]

    # Create the Table object
    table = Table(table_data, colWidths=col_widths)

    # Set Table Style with border and margins
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('INNERGRID', (0, 0), (-1, -1), 0.25, colors.black),
        ('BOX', (0, 0), (-1, -1), 0.25, colors.black),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('WORDSPACE', (0, 0), (-1, -1), 2),
    ]))

    # Build the PDF
    doc.build([table])

    buffer.seek(0)
    response = HttpResponse(buffer.read(), content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="selected_borrow_slips.pdf"'
    buffer.close()

    return response


@login_required
def borrow_slip_create(request):
    if request.method == 'POST':
        form = BorrowSlipForm(request.POST, user=request.user)
        if form.is_valid():
            borrow_slip = form.save(commit=False)

            # Ensure that date_borrow is timezone-aware
            if timezone.is_naive(borrow_slip.date_borrow):
                borrow_slip.date_borrow = timezone.make_aware(borrow_slip.date_borrow, timezone.get_current_timezone())

            # Ensure due_date is timezone-aware and set to 8:00 AM
            if timezone.is_naive(borrow_slip.due_date):
                borrow_slip.due_date = timezone.make_aware(borrow_slip.due_date, timezone.get_current_timezone())
                
                # Set the time to 8:00 AM
                borrow_slip.due_date = borrow_slip.due_date.replace(hour=8, minute=0, second=0, microsecond=0)
            
            # Optional: Convert to local time if you want to store it in local time zone (if needed)
            borrow_slip.date_borrow = timezone.localtime(borrow_slip.date_borrow)
            borrow_slip.due_date = timezone.localtime(borrow_slip.due_date)

            borrow_slip.save()
            return redirect('borrow-slip-list')  # Assuming this is a URL that lists all borrow slips
    else:
        form = BorrowSlipForm(user=request.user)
    
    return render(request, 'library/borrow_slip_form.html', {'form': form})


@login_required
def borrower_details(request, borrower_uid):
    try:
        borrower = Borrower.objects.get(borrower_uid=borrower_uid)
        data = {
            'borrower_name': borrower.borrower_name,
            'borrower_uid': borrower.borrower_uid,
            'grade_level': borrower.grade_level if hasattr(borrower, 'grade_level') else '',
            'section': borrower.section if hasattr(borrower, 'section') else '',
            'adviser': borrower.adviser if hasattr(borrower, 'adviser') else '',
            'status': borrower.status,  # Include status here
        }
    except Borrower.DoesNotExist:
        data = {}
    return JsonResponse(data)



@login_required
def reserve_book(request):
    if request.method == 'POST':
        form = BookReservationForm(request.POST, user=request.user)
        if form.is_valid():
            reservation = form.save(commit=False)

            # Get the borrower details
            if reservation.borrower_uid_number:
                try:
                    borrower = Borrower.objects.get(borrower_uid=reservation.borrower_uid_number)
                    
                    # Check if borrower is banned
                    if borrower.status == 'Banned':
                        # If the borrower is banned, show an error message and disable form submission
                        form.add_error(None, "⚠ This borrower is banned and cannot reserve books!")
                        return render(request, 'library/reserve_book_form.html', {'form': form})
                    
                    reservation.borrower_name = borrower.borrower_name  # Automatically set the name
                except Borrower.DoesNotExist:
                    reservation.borrower_name = ""  # Set to empty string if borrower doesn't exist

            reservation.status = 'Reserved'
            reservation.save()

            # Update the book status to 'Reserved'
            try:
                book = BookInventory.objects.get(book_number=reservation.book_number)
                book.status = 'Reserved'
                book.save()
            except BookInventory.DoesNotExist:
                # Handle case where the book doesn't exist
                pass

            return redirect('reservation-list')  # Redirect to the reservation list or another page
    else:
        form = BookReservationForm(user=request.user)

    return render(request, 'library/reserve_book_form.html', {'form': form})




@login_required
def collect_reservation(request, reservation_number):
    try:
        reservation = BookReservation.objects.get(reservation_number=reservation_number)

        # Check for POST request after validation
        if request.method == 'POST':
            # Transfer reservation details to BorrowSlip
            borrow_slip = BorrowSlip(
                book_number=reservation.book_number,
                book_title=reservation.book_title,
                author=reservation.author,
                date_borrow=timezone.now().date(),
                borrower_uid_number=reservation.borrower_uid_number,
                borrower_name=reservation.borrower_name,
                due_date=reservation.due_date,
                librarian_name=reservation.librarian_name,
                status='Borrowed'
            )
            borrow_slip.save()

            # Update reservation status
            reservation.status = 'Collected'
            reservation.collected_date = timezone.now()
            reservation.save()

            # Update book status to 'Borrowed'
            try:
                book = BookInventory.objects.get(book_number=reservation.book_number)
                book.status = 'Borrowed'
                book.save()
            except BookInventory.DoesNotExist:
                pass

            return JsonResponse({'success': True})

        return JsonResponse({'success': False, 'message': 'Invalid request.'})
    except BookReservation.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Reservation not found.'})


@csrf_exempt
def validate_collector(request, reservation_number):
    if request.method == 'POST':
        data = json.loads(request.body)
        uid = data.get('uid')

        try:
            reservation = BookReservation.objects.get(reservation_number=reservation_number)

            # Compare UID
            if reservation.borrower_uid_number == uid:
                return JsonResponse({'valid': True})
            else:
                return JsonResponse({'valid': False, 'message': 'UID does not match.'})
        except BookReservation.DoesNotExist:
            return JsonResponse({'valid': False, 'message': 'Reservation not found.'})


def expire_reservations():
    expired_reservations = BookReservation.objects.filter(
        status='Reserved',
        reservation_date__lt=timezone.now() - timedelta(hours=24)  
    )
    for reservation in expired_reservations:
        # Update book status to 'Available'
        try:
            book = BookInventory.objects.get(book_number=reservation.book_number)
            book.status = 'Available'
            book.save()
        except BookInventory.DoesNotExist:
            pass

        # Mark reservation as expired
        reservation.status = 'Expired'
        reservation.save()


@login_required
def reservation_list(request):
    # Run expiration logic (if this is required for your application)
    expire_reservations()

    # Query all reservations
    reservations = BookReservation.objects.all()

    # Categorize reservations by status
    ongoing_reservations = reservations.filter(status='Reserved')
    # collected_reservations = reservations.filter(status='Collected')
    collected_reservations = reservations.filter(status='Collected').order_by('-reservation_date')
    expired_reservations = reservations.filter(status='Expired')

    # Calculate the time remaining for ongoing reservations
    for reservation in ongoing_reservations:
        reservation.time_remaining = max(
            timedelta(hours=24) - (timezone.now() - reservation.reservation_date),
            timedelta(0)
        )
    
    # Combine all reservations and sort if needed
    # Sorting ongoing reservations by reservation date
    ongoing_reservations = sorted(
        ongoing_reservations,
        key=lambda x: x.reservation_date,
        reverse=True
    )
    # Sorting expired reservations (optional)
    expired_reservations = sorted(
        expired_reservations,
        key=lambda x: x.reservation_date,
        reverse=True
    )

    # Pass categorized data to the template
    context = {
        'ongoing_reservations': ongoing_reservations,
        'collected_reservations': collected_reservations,
        'expired_reservations': expired_reservations,
    }
    return render(request, 'library/reservation_list.html', context)







#MARK: Attendance Log
# ============================================================================================================================================
# ==================================================___LOG MANANGEMENT VIEW___===============================================================
# ============================================================================================================================================
@login_required
def create_attendance(request):
    if request.method == 'POST':
        form = AttendanceForm(request.POST)
        if form.is_valid():
            borrower_uid = form.cleaned_data['borrower_uid_number']
            borrower = Borrower.objects.filter(borrower_uid=borrower_uid).first()
            if borrower:
                attendance = form.save(commit=False)
                attendance.borrower_name = borrower.borrower_name
                attendance.grade_level = borrower.grade_level
                attendance.section = borrower.section
                attendance.save()
                # Return a JSON response with the borrower's name
                return JsonResponse({'borrower_name': borrower.borrower_name})
            else:
                # Return an error message if the borrower is not found
                return JsonResponse({'error': 'Borrower not found.'}, status=404)
        else:
            # Return the form errors as a JSON response
            return JsonResponse({'errors': form.errors}, status=400)
    else:
        form = AttendanceForm()
    return render(request, 'library/create_attendance.html', {'form': form})


@login_required
def attendance_list(request):
    # Fetch attendance data for the table
    attendances = Attendance.objects.all().order_by('-date_time')

    # Convert date_time to local time zone for each attendance record
    for attendance in attendances:
        attendance.date_time_local = timezone.localtime(attendance.date_time)  # Convert to local timezone

    # Calculate statistics by grade level
    grade_level_stats = Attendance.objects.values('grade_level') \
        .annotate(total_students=Count('borrower_uid_number', distinct=True)) \
        .order_by('grade_level')

    # Prepare data for JSON response (labels and sizes)
    labels = [f"{stat['grade_level']}" for stat in grade_level_stats]
    sizes = [stat['total_students'] for stat in grade_level_stats]

    return render(request, 'library/attendance_list.html', {
        'attendances': attendances,
        'grade_level_data': json.dumps({'labels': labels, 'sizes': sizes}),  # Pass JSON data to the template
    })

@login_required
def recent_attendance_stats(request):
    # Get the three most recent attendance dates with records
    recent_dates = Attendance.objects.dates('date_time', 'day', order='DESC')[:3]

    # Gather attendance counts by grade level for each of the recent dates
    recent_data = []
    for date in recent_dates:
        day_data = Attendance.objects.filter(date_time__date=date) \
            .values('grade_level') \
            .annotate(total_students=Count('borrower_uid_number', distinct=True)) \
            .order_by('grade_level')

        # Convert date to local time zone for display, ensuring it works for both date and datetime
        if isinstance(date, datetime):
            local_date = timezone.localtime(date).strftime('%b %d, %Y')  # Convert datetime to local time and format
        else:
            # If it's just a date (no time component), handle it differently
            local_date = date.strftime('%b %d, %Y')

        # Format each day's data for JSON serialization
        recent_data.append({
            'date': local_date,  # Use the local time version of the date
            'data': {stat['grade_level']: stat['total_students'] for stat in day_data}
        })

    return JsonResponse(recent_data, safe=False)








#MARK: Book Monitoring
# ============================================================================================================================================
# ===================================================___BOOK MONITORING VIEW___===============================================================
# ============================================================================================================================================
@login_required
def monitor_borrowed_books(request):
    # Get the current date
    current_date = timezone.now().date()
    current_month = current_date.month
    current_year = current_date.year

    # Get the name of the current month
    current_month_name = calendar.month_name[current_month]

    # Get filter parameters from GET request
    book_number = request.GET.get('book_number', '').strip()
    borrower_uid = request.GET.get('borrower_uid', '').strip()

    # Base filter for the current month and year
    borrow_slips = BorrowSlip.objects.filter(date_borrow__year=current_year, date_borrow__month=current_month)

    # Apply filtering based on book number and borrower UID
    if book_number:
        borrow_slips = borrow_slips.filter(book_number__icontains=book_number)
    if borrower_uid:
        borrow_slips = borrow_slips.filter(borrower_uid_number__icontains=borrower_uid)

    # Update status of borrow slips based on due date and return status
    for slip in borrow_slips:
        if slip.status == 'Lost':
            continue  # Skip updating the status if the book is lost

        slip_due_date = slip.due_date.date() if isinstance(slip.due_date, datetime) else slip.due_date
        if slip_due_date < current_date and not slip.returned:
            slip.status = 'Overdue'
        elif slip.returned:
            slip.status = 'Returned'
        else:
            slip.status = 'Borrowed'

        slip.save()

    # Get overdue books from previous months (status = Overdue and date_borrowed before the current month)
    overdue_previous_months = BorrowSlip.objects.filter(
        status="Overdue", 
        due_date__lt=current_date,
        date_borrow__lt=f"{current_year}-{current_month:02d}-01"
    )

    # Most Borrowed Books (Top 5 by count for this month)
    most_borrowed_books = (
        borrow_slips.values("book_title")
        .annotate(count=Count("book_title"))
        .order_by("-count")[:5]
    )

    # Count for different statuses for this month
    ongoing_borrowing = borrow_slips.filter(status="Borrowed").count()
    returned_books = borrow_slips.filter(status="Returned").count()
    overdue_books = borrow_slips.filter(status="Overdue").count()
    lost_books = borrow_slips.filter(status="Lost").count()
    reserved_books = borrow_slips.filter(status="Reserved").count()

    # Reserved Books from the reservation list
    reserved_books_count = BookReservation.objects.filter(status="Reserved").count()

    # Monthly Borrow Count for the last 3 months (current month and the previous two months)
    monthly_borrow_counts = [
        BorrowSlip.objects.filter(date_borrow__year=current_year, date_borrow__month=month).count()
        for month in [current_month, current_month - 1, current_month - 2] if month > 0
    ]

    # Get the names of the last 3 months
    last_3_months_labels = [calendar.month_name[(current_month - i - 1) % 12] for i in range(3)]

    # Prepare statistics data
    statistics_data = {
        'ongoingBorrowing': ongoing_borrowing,
        'returnedBooks': returned_books,
        'overdueBooks': overdue_books,
        'lostBooks': lost_books,
        'reservedBooks': reserved_books_count,  # Updated reserved count
        'mostBorrowedBooks': list(most_borrowed_books),
        'monthlyBorrowCounts': monthly_borrow_counts,  # Add monthly borrow counts
        'last3MonthsLabels': last_3_months_labels,  # Add the month names
    }

    # Pass statistics data and month name to the template
    context = {
        "borrow_slips": borrow_slips,
        "overdue_previous_months": overdue_previous_months,  # Pass overdue books from previous months
        "statistics_data": json.dumps(statistics_data),  # Add the statistics data to context
        "current_month_name": current_month_name,  # Add the current month name to context
        "book_number": book_number,
        "borrower_uid": borrower_uid,
    }

    return render(request, 'library/monitor_borrowed_books.html', context)











import logging
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import BorrowSlip

logger = logging.getLogger(__name__)

@csrf_exempt
def return_book(request, slip_number):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            book_number = data.get('book_number')
            lost = data.get('lost', False)

            # Fetch borrow slip
            borrow_slip = BorrowSlip.objects.get(slip_number=slip_number, book_number=book_number)

            logger.info(f"Before Update: {borrow_slip.status}")

            # Mark as lost
            if lost:
                borrow_slip.status = 'Lost'
                borrow_slip.returned = False  # Ensure it’s not marked as returned
                borrow_slip.save()
                logger.info(f"After Update (Lost): {borrow_slip.status}")
                return JsonResponse({'success': True, 'message': 'The book has been marked as Lost.'})

            # Handle normal return
            if borrow_slip.status in ['Borrowed', 'Overdue']:
                borrow_slip.returned = True
                borrow_slip.status = 'Returned'
                borrow_slip.save()
                logger.info(f"After Update (Returned): {borrow_slip.status}")
                return JsonResponse({'success': True, 'message': 'Book returned successfully!'})

            return JsonResponse({'success': False, 'message': 'This book has already been returned or marked as lost.'})

        except BorrowSlip.DoesNotExist:
            logger.error(f"No record found for slip_number={slip_number}, book_number={book_number}")
            return JsonResponse({'success': False, 'message': 'No record found for the given slip number and book number.'})

    return JsonResponse({'success': False, 'message': 'Invalid request method.'})












@login_required
@csrf_exempt
def set_penalty(request, slip_number):
    borrow_slip = get_object_or_404(BorrowSlip, slip_number=slip_number)
    borrower = get_object_or_404(Borrower, borrower_uid=borrow_slip.borrower_uid_number)
    
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            action = data.get('action')
            
            # Apply action to the borrow slip
            if action == 'replace':
                borrow_slip.status = 'Pending Replacement'
                borrow_slip.penalty = 'Replace Book'

            
            # Update borrower status based on rules
            if borrower.status == 'Normal':
                borrower.status = '1st Violation'  # If 'Normal' or '1st Violation'
            elif borrower.status == '1st Violation':
                borrower.status = '2nd Violation'   
            elif borrower.status == '2nd Violation':
                borrower.status = '3rd Violation'  # If '2nd Violation', promote to '3rd Violation'
            elif borrower.status == '3rd Violation':
                borrower.status = 'Banned'  # Final penalty, banned after 3rd violation
            
            borrow_slip.save()
            borrower.save()

            return JsonResponse({'success': True, 'message': 'Penalty applied successfully.'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})

    return JsonResponse({'success': False, 'message': 'Invalid request method.'})













def get_borrower_status(request, borrower_uid):
    try:
        # Get the borrower by their UID
        borrower = Borrower.objects.get(borrower_uid=borrower_uid)
        # Return the status as a JSON response
        return JsonResponse({'status': borrower.status})
    except Borrower.DoesNotExist:
        # If the borrower does not exist, return an error message
        return JsonResponse({'error': 'Borrower not found'}, status=404)



#MARK: Super Admin
def redirect_to_admin(request):
    return HttpResponseRedirect('/admin')



#MARK:Tutorial
def VidTutorials(request):
    return render(request, 'library/Tutorials.html')  