from django.shortcuts import render

# Create your views here.

def custom_404(request, exception):
    return render(request, "404.html", status=404)

from django.http import Http404

def test_view(request):
    raise Http404("Not found")


def home_view(request):
    return render(request, "home.html")

def about_view(request):
    return render(request, "about.html")