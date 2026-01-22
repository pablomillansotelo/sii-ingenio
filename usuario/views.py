from django.shortcuts import render
from django.contrib.auth.decorators import login_required


# Create your views here.
@login_required
def usuario(request):
    print("Usuario view accessed")
    return render(request, 'usuario.html')
