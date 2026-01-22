from django.shortcuts import render
from django.contrib.auth.decorators import login_required


# Create your views here.
@login_required
def home(request):
    print("Home view accessed")
    return render(request, 'home.html')

@login_required
def kardex(request):
    print("Kardex view accessed")
    return render(request, 'alumnos/kardex.html')
