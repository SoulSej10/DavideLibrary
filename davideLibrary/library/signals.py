from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.db.models.signals import post_migrate
from django.dispatch import receiver

@receiver(post_migrate)
def create_user_groups(sender, **kwargs):
    if sender.name == 'library':
        # Create Assistant Librarian group if it doesn't exist
        assistant_group, created = Group.objects.get_or_create(name='Assistant Librarian')
        if created:
            # Assign permissions to assistant librarian group
            permissions = [
                'add_bookinventory',
                'view_bookinventory',
                'add_borrower',
                'view_borrower',
                'add_borrowslip',
                'view_borrowslip',
                # Add other permissions as needed
            ]
            for perm_code in permissions:
                try:
                    app_label, codename = perm_code.split('_', 1)
                    permission = Permission.objects.get(codename=perm_code, content_type__app_label=app_label)
                    assistant_group.permissions.add(permission)
                except Permission.DoesNotExist:
                    pass
