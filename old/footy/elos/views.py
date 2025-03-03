from django.http import HttpResponse
from django.shortcuts import render


# Create your views here.
def elos_home(request) -> HttpResponse:
    context = {}
    # return render(request, "base/home.html", context)
    return HttpResponse("HELLO")
