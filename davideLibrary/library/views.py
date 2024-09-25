# ============================================================================================================================================
# ==========================================================___IMPORTS___====================++++++===========================================
# ============================================================================================================================================
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
from .models import  Borrower, BookInventory, BorrowSlip, Attendance, Category, CustomUser
from .forms import  BorrowerForm, BookInventoryForm, BorrowSlipForm, AttendanceForm, PenaltyForm
from django.contrib import messages
from datetime import datetime
from django.utils import timezone  
from io import BytesIO
from django.template.loader import get_template
from django.db.models import Q, Count
from django.utils.timezone import now
from django.http import JsonResponse
import qrcode
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Image
from django.core.files.storage import default_storage
from django.http import FileResponse
from django.views.decorators.csrf import csrf_exempt

import matplotlib
matplotlib.use('Agg')  # Set the backend to 'Agg' for non-interactive plotting
import matplotlib.pyplot as plt
import base64


from django.contrib.auth.decorators import login_required, user_passes_test
from django.urls import reverse
from django.contrib.auth.models import Group 
from django.http import HttpResponseForbidden

from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.views import LoginView
from django.urls import reverse_lazy





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
        if user.is_superuser:
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

# Custom login view (if using a custom authentication form)
def login_view(request):
    if request.method == 'POST':
        form = CustomAuthenticationForm(request, data=request.POST)
        
        if form.is_valid():
            # Retrieve cleaned data
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            admin_id = form.cleaned_data.get('admin_id')
            
            # Authenticate user
            user = authenticate(request, username=username, password=password)
            
            # Check if user is authenticated and if admin_id matches
            if user is not None and user.admin_id == admin_id:  # Adjust this check based on your User model
                login(request, user)
                messages.success(request, 'Login successful.')
                return redirect('home')
            else:
                messages.error(request, 'Invalid credentials or admin ID.')
        else:
            messages.error(request, 'Login failed. Please check your details.')

    else:
        form = CustomAuthenticationForm()

    return render(request, 'library/LogRegister.html', {'form': form})

# Registration view (only accessible to Head Librarians)
@login_required
@user_passes_test(is_head_librarian)
def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Assistant Librarian registered successfully.')
        else:
            messages.error(request, 'Registration failed. Please check the form.')
    else:
        form = CustomUserCreationForm()

    all_users = CustomUser.objects.all()
    head_librarians = all_users.filter(is_staff=True)
    assistant_librarians = all_users.filter(is_staff=False)

    context = {
        'form': form,
        'head_librarians': head_librarians,
        'assistant_librarians': assistant_librarians,
        'user': request.user  # Ensure user object is available in template
    }

    return render(request, 'library/RegisterLog.html', context)

# Logout view
def logout_view(request):
    logout(request)
    messages.success(request, "You have been logged out successfully.")
    return redirect('directory')

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

    # Data for the bar graph (count books by category)
    category_counts = BookInventory.objects.values('category__name').annotate(count=Count('book_number')).order_by('category__name')
    categories = [entry['category__name'] for entry in category_counts]
    counts = [entry['count'] for entry in category_counts]

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
    })


def book_detail(request, book_number):
    book = get_object_or_404(BookInventory, book_number=book_number)
    return render(request, 'home.html', {
        'book_detail': book,
        'query': request.GET.get('q', ''),  # Preserve the search query
    })












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

@login_required
def delete_borrower(request, pk):
    borrower = get_object_or_404(Borrower, borrower_uid=pk)
    if request.method == 'POST':
        borrower.delete()
        return redirect('borrower-list')
    borrowers = Borrower.objects.all().order_by('-date_issued')
    return render(request, 'library/borrower_list.html', {'borrowers': borrowers, 'query': '', 'form': BorrowerForm()})



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

    categories = Category.objects.all()

    if query:
        books = BookInventory.objects.filter(
            models.Q(book_number__icontains=query) | models.Q(book_title__icontains=query)
        ).order_by('-record_date')
    elif category_name:
        books = BookInventory.objects.filter(category__name=category_name).order_by('-record_date')
    else:
        books = BookInventory.objects.all().order_by('-record_date')

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
        'no_results': no_results,
    }
    return render(request, 'library/book_list.html', context)



@login_required
def book_create(request):
    if request.method == 'POST':
        if 'add-category' in request.POST:
            category_name = request.POST.get('category_name')
            if category_name:
                Category.objects.get_or_create(name=category_name)
                return redirect('book-create')  # Redirect to the same view to avoid re-posting the form
        else:
            form = BookInventoryForm(request.POST)
            if form.is_valid():
                form.save()
                return redirect('book-list')
    else:
        form = BookInventoryForm()

    categories = Category.objects.all()
    return render(request, 'library/book_form.html', {'form': form, 'categories': categories})

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
    
    categories = Category.objects.all()
    return render(request, 'library/book_form.html', {'form': form, 'categories': categories})

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

def book_details(request, book_number):
    try:
        book = BookInventory.objects.get(book_number=book_number)
        data = {
            'book_number': book.book_number,
            'record_date': book.record_date.strftime('%Y-%m-%d'),
            'class_field': book.class_field,
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
            'category_name': book.category.name,
            'location': book.location,
            'qr_code': book.qr_code.url if book.qr_code else None,
        }
        return JsonResponse(data)
    except BookInventory.DoesNotExist:
        return JsonResponse({'error': 'Book not found'}, status=404)


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










# ============================================================================================================================================
# =======================================================__SLIP MANANGEMENT VIEW___===========================================================
# ============================================================================================================================================
import io
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
@login_required
def borrow_slip_list(request):
    query = request.GET.get('search', '')
    sort_order = request.GET.get('sort', '-date_borrow')
    form = BorrowSlipForm()

    date_filter = request.GET.get('date_filter', '')
    if date_filter:
        try:
            date_filter = datetime.strptime(date_filter, '%Y-%m-%d').date()
            borrow_slips = BorrowSlip.objects.filter(date_borrow=date_filter).order_by(sort_order)
        except ValueError:
            borrow_slips = BorrowSlip.objects.none()
    else:
        borrow_slips = BorrowSlip.objects.all().order_by(sort_order)

    if request.method == 'POST':
        form = BorrowSlipForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('borrow-slip-list')

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
            borrow_slip.date_borrow = timezone.now().date()
            borrow_slip.due_date = timezone.now().date() + timezone.timedelta(days=3)
            borrow_slip.save()
            return redirect('borrow-slip-list')
    else:
        form = BorrowSlipForm(user=request.user)
    return render(request, 'library/borrow_slip_form.html', {'form': form})


@login_required
def book_details(request, book_number):
    try:
        book = BookInventory.objects.get(book_number=book_number)
        data = {
            'book_title': book.book_title,
            'author': book.author,
            'book_number': book.book_number,
            'class_field': book.class_field,
            'edition': book.edition,
            'volume': book.volume,
            'pages': book.pages,
            'quantity': book.quantity,
            'fund_source': book.fund_source,
            'price': book.price,
            'publisher': book.publisher,
            'year': book.year,
            'category': book.category.name if book.category else '',
            'remark': book.remark,
            'location': book.location,
            
        }
    except BookInventory.DoesNotExist:
        data = {}
    return JsonResponse(data)

@login_required
def borrower_details(request, borrower_uid):
    try:
        borrower = Borrower.objects.get(borrower_uid=borrower_uid)
        data = {
            'borrower_name': borrower.borrower_name,
            'borrower_uid': borrower.borrower_uid,
            'grade_level': borrower.grade_level if hasattr(borrower, 'grade_level') else '',  # Adjust if using a different field name
            'section': borrower.section if hasattr(borrower, 'section') else '',  # Adjust if using a different field name
            'adviser': borrower.adviser if hasattr(borrower, 'adviser') else '',  # Adjust if using a different field name
        }
    except Borrower.DoesNotExist:
        data = {}
    return JsonResponse(data)










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
                return redirect('attendance-list')
    else:
        form = AttendanceForm()
    return render(request, 'library/create_attendance.html', {'form': form})
@login_required
def attendance_list(request):
    attendances = Attendance.objects.all()
    return render(request, 'library/attendance_list.html', {'attendances': attendances})








# ============================================================================================================================================
# ===================================================___BOOK MONITORING VIEW___===============================================================
# ============================================================================================================================================
@login_required
def monitor_borrowed_books(request):
    # Order by 'returned' (False first) and then by '-date_borrow' (most recent first)
    borrow_slips = BorrowSlip.objects.order_by('returned', '-date_borrow')
    current_date = timezone.now().date()

    for slip in borrow_slips:
        # Ensure 'due_date' is a date object for comparison
        if isinstance(slip.due_date, datetime):
            slip_due_date = slip.due_date.date()
        else:
            slip_due_date = slip.due_date

        # Update status based on due_date and return status
        if slip_due_date < current_date and not slip.returned:
            slip.status = 'Overdue'
        elif slip.returned:
            slip.status = 'Returned'
        else:
            slip.status = 'Borrowed'

        slip.save()  # Save the updated status

    return render(request, 'library/monitor_borrowed_books.html', {'borrow_slips': borrow_slips})

@csrf_exempt
def return_book(request, slip_number):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            book_number = data.get('book_number')

            borrow_slip = BorrowSlip.objects.get(slip_number=slip_number, book_number=book_number)

            if borrow_slip.status in ['Borrowed', 'Overdue']:
                borrow_slip.returned = True
                borrow_slip.status = 'Returned'
                borrow_slip.save()

                return JsonResponse({'success': True, 'message': 'Book returned successfully!'})
            else:
                return JsonResponse({'success': False, 'message': 'This book has already been returned.'})

        except BorrowSlip.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'No record found for the given slip number and book number.'})

    return JsonResponse({'success': False, 'message': 'Invalid request method.'})

@login_required
@csrf_exempt
def set_penalty(request, slip_number):
    borrow_slip = get_object_or_404(BorrowSlip, slip_number=slip_number)
    
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            action = data.get('action')
            ban_duration = data.get('ban_duration')
            
            if action == 'replace':
                borrow_slip.status = 'Pending Replacement'
                borrow_slip.penalty = 'Replace Book'
            
            elif action == 'ban':
                if ban_duration:
                    borrow_slip.status = f'Banned for {ban_duration} days'
                    borrow_slip.penalty = f'Banned for {ban_duration} days'
                    
            borrow_slip.save()
            return JsonResponse({'success': True, 'message': 'Penalty applied successfully.'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})
    
    return JsonResponse({'success': False, 'message': 'Invalid request method.'})