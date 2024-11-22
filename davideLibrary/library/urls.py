from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static
from .views import generate_selected_books_pdf

urlpatterns = [
    #landing
    path('', views.landing, name='landing'),
    path('borrow-history/', views.borrow_history, name='borrow-history'),
    path('landingLog/', views.landingLog, name = 'landingLog'),
    path('log_attendance/', views.log_attendance, name='log_attendance'),


    # home
    path('home/', views.home, name='home'),
    path('directory/', views.directory, name='directory'),
    path('book/<str:book_number>/', views.book_detail, name='book_detail'),
    
    # directories in accounts
    path('register/', views.register, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('login/head/', views.HeadLibrarianLoginView.as_view(), name='head_librarian_login'),
    path('login/assistant/', views.AssistantLibrarianLoginView.as_view(), name='assistant_librarian_login'),

    #login
    path('password_reset/', views.request_password_reset, name='password_reset'),
    path('change_password/', views.change_password, name='change_password'),
    path('login/temporary/', views.temporary_login_view, name='temporary_login'),
    path("validate-username/", views.validate_username, name="validate_username"),
    
    #register
    path('user-details/<str:user_id>/', views.user_details, name='user_details'),
    path('account/<str:admin_id>/download-pdf/', views.generate_account_pdf, name='download-account-pdf'),
  

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
    path('book-detail/<str:book_number>/', views.book_detail, name='book-detail'),
    path('generate-selected-books-pdf/', generate_selected_books_pdf, name='generate-selected-books-pdf'),
    path('add-location/',views.add_location, name='add-location'),
    
    # borrow slip
    path('borrow-slips/', views.borrow_slip_list, name='borrow-slip-list'),
    path('borrow-slips/create/', views.borrow_slip_create, name='borrow-slip-create'),
    # path('book-details/<str:book_number>/', book_details, name='book-details'),
    path('borrower-details/<str:borrower_uid>/', views.borrower_details, name='borrower-details'),
    path('download-selected-pdf/', views.download_selected_pdf, name='download-selected-pdf'),
    path('reserve-book/', views.reserve_book, name='reserve-book'),
    path('collect-reservation/<int:reservation_number>/', views.collect_reservation, name='collect-reservation'),
    path('expire-reservations/', views.expire_reservations, name='expire-reservations'),
    path('reservation-list/', views.reservation_list, name='reservation-list'),
    path('validate-collector/<str:reservation_number>/', views.validate_collector, name='validate-collector'),
    path('collect-reservation/<str:reservation_number>/', views.collect_reservation, name='collect-reservation'),
    
    # attendance
    path('create/', views.create_attendance, name='create-attendance'),
    path('list/', views.attendance_list, name='attendance-list'),
    path('recent-attendance-stats/', views.recent_attendance_stats, name='recent_attendance_stats'),

    # Monitoring Borrowed books
    path('monitor-borrowed-books/', views.monitor_borrowed_books, name='monitor-borrowed-books'),
    path('return-book/<int:slip_number>/', views.return_book, name='return-book'),
    path('set-penalty/<str:slip_number>/', views.set_penalty, name='set-penalty'),
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)