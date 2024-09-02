# library/context_processors.py

def navbar_context(request):
    username = None
    if request.user.is_authenticated:
        username = request.user.username
    return {'username': username}
