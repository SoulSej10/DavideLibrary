

### Summary of Views

1. **`directory`**: Renders the directory page.
   
2. **`register`**: Handles user registration. On successful registration, the user is logged in and redirected to the login page.

3. **`login_view`**: Handles user login. On successful login, the user is redirected to the home page.

4. **`home`**: Renders the home page, accessible only to logged-in users.

5. **`logout_view`**: Logs out the user and redirects to the directory page.

6. **`borrower_list`**: Displays a list of borrowers with optional search and grade-level filters. Supports adding and editing borrowers.

7. **`edit_borrower`**: Edits an existing borrower’s information.

8. **`delete_borrower`**: Deletes a borrower’s record.

9. **`borrower_create`**: Creates a new borrower record.

10. **`generate_uid_pdf`**: Generates and serves a PDF with borrower details and a QR code.

11. **`book_list`**: Displays a list of books with search and category filtering options. Supports adding and deleting categories.

12. **`book_delete`**: Deletes a book record.

13. **`book_create`**: Creates a new book record and allows adding new categories.

14. **`book_update`**: Updates an existing book record.

15. **`delete_category`**: Deletes a category and redirects to the book creation view.

16. **`borrow_slip_list`**: Displays a list of borrow slips with search and date filtering. Supports generating a PDF report of borrow slips.

17. **`delete_selected_books`**: Deletes selected books based on user input.

18. **`set_location_for_books`**: Sets the location for selected books.

19. **`book_details`**: Provides book details in JSON format for AJAX requests.

20. **`borrow_slip_create`**: Creates a new borrow slip.

21. **`borrower_details`**: Provides borrower details in JSON format for AJAX requests.

22. **`create_attendance`**: Creates a new attendance record.

23. **`attendance_list`**: Displays a list of attendance records.

