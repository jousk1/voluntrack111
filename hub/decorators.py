from django.contrib.auth.decorators import user_passes_test

def coordinator_required(view_func):
    return user_passes_test(lambda u: hasattr(u, "profile") and u.profile.is_coordinator)(view_func)
