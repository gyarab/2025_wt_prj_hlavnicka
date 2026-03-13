from django.shortcuts import render
from .models import Prvek, Stitek

# Create your views here.

def custom_404(request, exception):
    return render(request, "404.html", status=404)

from django.http import Http404
from django.shortcuts import redirect

def test_view(request):
    raise Http404("Not found")


def home_view(request):
    return render(request, "home.html")

def about_view(request):
    return render(request, "about.html")

def detail_prvku(request, id):
    if not request.user.is_authenticated:
        return redirect('/prihlaseni') 
    try:
        prvek = Prvek.objects.get(id=id)
    except Prvek.DoesNotExist:
        raise Http404("Prvek nenalezen")
    return render(request, "detailPrvku.html", {"prvek": prvek})

def detail_stitku(request,id):
    if not request.user.is_authenticated:
        return redirect('/prihlaseni')
    try:
        stitek = Stitek.objects.get(id=id)
        print("Vlastník štítku",stitek.nazev,":", stitek.vlastnik)
        if not stitek.vlastnik == request.user and not stitek.vlastnik == None:
            raise Http404("Štítek nenalezen")
    except Stitek.DoesNotExist:
        raise Http404("Štítek nenalezen")
    return render(request, "detailStitku.html", {"stitek": stitek})


