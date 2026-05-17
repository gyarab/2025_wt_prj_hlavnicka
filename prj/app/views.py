from django.shortcuts import render, redirect
from .models import Prvek, Stitek, Seznam
from django import forms
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.http import Http404, JsonResponse
from .services import extract_smart_dates # Import tvojí nové logiky
from datetime import datetime

# Create your views here.

class PrvekForm(forms.ModelForm):
    class Meta:
        model = Prvek
        fields = ['nazev', 'obsah', 'stitky']
        labels = {
            'nazev': 'Název prvku',
            'obsah': 'Obsah',
            'stitky': 'Štítky'
        }

def custom_404(request, exception):
    return render(request, "404.html", status=404)

def test_view(request):
    raise Http404("Not found")

def registrace_view(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('/prihlasit/')
    else:
        form = UserCreationForm()
    return render(request, 'registration/registrace.html', {'form': form})


    
@login_required(login_url='/prihlasit')
def pridat_prvek(request):
    if request.method == 'POST':
        form = PrvekForm(request.POST)
        if form.is_valid():
            prvek = form.save(commit=False)
            prvek.vlastnik = request.user
            
            # Zpracování datumů ze skrytých polí
            datum_zacatku_str = request.POST.get('datum_zacatku_hidden')
            datum_konce_str = request.POST.get('datum_konce_hidden')
            
            if datum_zacatku_str:
                try:
                    prvek.datum_zacatku = datetime.fromisoformat(datum_zacatku_str)
                except:
                    pass
            
            if datum_konce_str:
                try:
                    prvek.datum_konce = datetime.fromisoformat(datum_konce_str)
                except:
                    pass
            
            prvek.save()
            form.save_m2m()  # Uloží many-to-many relationship (stitky)
            return redirect('/home')
    else:
        form = PrvekForm()
    
    return render(request, 'pridat_prvek.html', {'form': form})


def home_view(request):
    if request.user.is_authenticated:
        prvky = Prvek.objects.filter(vlastnik=request.user, smazano=False).order_by('-datum_vytvoreni')
        seznamy = Seznam.objects.filter(vlastnik=request.user).order_by('nazev')
        
        # Filtrování podle štítku
        stitek_id = request.GET.get('stitek')
        if stitek_id:
            prvky = prvky.filter(stitky__id=stitek_id)
        
        # Získání všech štítků uživatele pro filtr
        stitky = Stitek.objects.filter(vlastnik=request.user).order_by('nazev')
    else:
        prvky = []
        stitky = []
        seznamy = []
    
    return render(request, "home.html", {"prvky": prvky, "stitky": stitky, "selected_stitek": request.GET.get('stitek'), "seznamy": seznamy})

def about_view(request):
    # Data z prvku #1
    prvek = Prvek.objects.first()
    return render(request, "about.html", {"prvek": prvek})

def detail_prvku(request, id):
    if not request.user.is_authenticated:
        return redirect('/prihlasit') 
    try:
        prvek = Prvek.objects.get(id=id)
    except Prvek.DoesNotExist:
        raise Http404("Prvek nenalezen")

    if not prvek.vlastnik == request.user and not prvek.vlastnik == None:
        raise Http404("Prvek nenalezen")
    return render(request, "detailPrvku.html", {"prvek": prvek})

@login_required(login_url='/prihlasit')
def upravit_prvek(request, id):
    try:
        prvek = Prvek.objects.get(id=id)
    except Prvek.DoesNotExist:
        raise Http404("Prvek nenalezen")
    
    # Ověřit, že uživatel je vlastník prvku
    if prvek.vlastnik != request.user:
        raise Http404("Prvek nenalezen")
    
    if request.method == 'POST':
        form = PrvekForm(request.POST, instance=prvek)
        if form.is_valid():
            prvek = form.save(commit=False)
            prvek.save()
            form.save_m2m()
            return redirect('detail_prvku', id=prvek.id)
    else:
        form = PrvekForm(instance=prvek)
    
    return render(request, 'upravit_prvek.html', {'form': form, 'prvek': prvek})

@login_required(login_url='/prihlasit')
def smazat_prvek(request, id):
    try:
        prvek = Prvek.objects.get(id=id)
    except Prvek.DoesNotExist:
        raise Http404("Prvek nenalezen")
    
    # Ověřit, že uživatel je vlastník prvku
    if prvek.vlastnik != request.user:
        raise Http404("Prvek nenalezen")
    
    if request.method == 'POST':
        prvek.smazano = True
        prvek.save()
        return redirect('home')
    
    return render(request, 'smazat_prvek.html', {'prvek': prvek})

def detail_stitku(request,id):
    if not request.user.is_authenticated:
        return redirect('/prihlasit')
    try:
        stitek = Stitek.objects.get(id=id)
        print("Vlastník štítku",stitek.nazev,":", stitek.vlastnik)
        if not stitek.vlastnik == request.user and not stitek.vlastnik == None:
            raise Http404("Štítek nenalezen")
    except Stitek.DoesNotExist:
        raise Http404("Štítek nenalezen")
    return render(request, "detailStitku.html", {"stitek": stitek})

def detail_seznamu(request, id):
    if not request.user.is_authenticated:
        return redirect('/prihlasit')
    try:
        seznam = Seznam.objects.get(id=id)
        print("Vlastník seznamu",seznam.nazev,":", seznam.vlastnik)
        if not seznam.vlastnik == request.user and not seznam.vlastnik == None:
            raise Http404("Seznam nenalezen")
    except Seznam.DoesNotExist:
        raise Http404("Seznam nenalezen")
    return render(request, "detail_seznamu.html", {"seznam": seznam})


def stitek_api(request, id):
    if not request.user.is_authenticated:
        return JsonResponse({'success': False, 'error': 'Neautorizovaný přístup'}, status=401)
    
    try:
        stitek = Stitek.objects.get(id=id)
        if not stitek.vlastnik == request.user and not stitek.vlastnik == None:
            return JsonResponse({'success': False, 'error': 'Štítek nenalezen'}, status=404)
    except Stitek.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Štítek nenalezen'}, status=404)

    prvky = stitek.prvek_set.filter(smazano=False,vlastnik=request.user).values('id', 'nazev')[:10]  
    return JsonResponse({'success': True, 'prvky': list(prvky), 'stitek': stitek.nazev, 'stitek_id': stitek.id, 'prvky_count': stitek.prvek_set.filter(smazano=False).count(), 'stitek_vlastnik': stitek.vlastnik.username if stitek.vlastnik else None, 'request_user': request.user.username})

def prvek_api(request, id):
    if (not request.user.is_authenticated):
        pass


def api_playground_view(request):
    return render(request, "api_playground.html")