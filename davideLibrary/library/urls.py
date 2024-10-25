from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static
from .views import book_details, generate_selected_books_pdf

urlpatterns = [

    path('', views.landing, name='landing'),
    path('borrow-history/', views.borrow_history, name='borrow-history'),
    
    # home
    path('home/', views.home, name='home'),
    path('directory/', views.directory, name='directory'),
    path('book/<str:book_number>/', views.book_detail, name='book_detail'),
    # path('borrow/<str:book_number>/', views.borrow_book, name='borrow_book'),
    
    # directories in accounts
    path('register/', views.register, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('login/head/', views.HeadLibrarianLoginView.as_view(), name='head_librarian_login'),
    path('login/assistant/', views.AssistantLibrarianLoginView.as_view(), name='assistant_librarian_login'),
    

    # borrowers
    path('borrower-list/', views.borrower_list, name='borrower-list'),
    path('borrower-create/', views.borrower_create, name='borrower-create'),
    path('generate-uid-pdf/<str:pk>/', views.generate_uid_pdf, name='generate_uid_pdf'),
    path('edit-borrower/<str:pk>/', views.edit_borrower, name='edit-borrower'),
    # path('delete-borrower/<str:pk>/', views.delete_borrower, name='delete-borrower'),
    path('borrowers/delete/<str:pk>/', views.delete_borrower, name='delete-borrower'),
    path('borrowers/delete-multiple/', views.delete_multiple_borrowers, name='delete-multiple-borrowers'),


    # book inventory
    path('books/', views.book_list, name='book-list'),
    path('books/create/', views.book_create, name='book-create'),
    path('books/update/<str:book_number>/', views.book_update, name='book-update'),
    path('category/delete/<int:category_id>/', views.delete_category, name='delete-category'),
    path('books/delete-selected/', views.delete_selected_books, name='delete-selected-books'),
    path('books/set-location/', views.set_location_for_books, name='set-location-for-books'),
    path('book-details/<str:book_number>/', book_details, name='book-details'),
    path('generate-selected-books-pdf/', generate_selected_books_pdf, name='generate-selected-books-pdf'),
    
    # borrow slip
    path('borrow-slips/', views.borrow_slip_list, name='borrow-slip-list'),
    path('borrow-slips/create/', views.borrow_slip_create, name='borrow-slip-create'),
    path('book-details/<str:book_number>/', book_details, name='book-details'),
    path('borrower-details/<str:borrower_uid>/', views.borrower_details, name='borrower-details'),
    path('download-selected-pdf/', views.download_selected_pdf, name='download-selected-pdf'),
    
    # attendance
    path('create/', views.create_attendance, name='create-attendance'),
    path('list/', views.attendance_list, name='attendance-list'),

    # # Borrowed books
    path('monitor-borrowed-books/', views.monitor_borrowed_books, name='monitor-borrowed-books'),
    path('return-book/<int:slip_number>/', views.return_book, name='return-book'),
    path('set-penalty/<str:slip_number>/', views.set_penalty, name='set-penalty'),
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)