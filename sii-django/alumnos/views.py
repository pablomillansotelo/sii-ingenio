from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect


@login_required
def home(request):
    return redirect("sii_home")


@login_required
def kardex(request):
    return redirect("sii_kardex")
