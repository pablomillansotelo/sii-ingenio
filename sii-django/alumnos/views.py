from django.shortcuts import render

# Create your views here.
def home(request):
    print("Home view accessed")
    return render(request, 'home.html')
