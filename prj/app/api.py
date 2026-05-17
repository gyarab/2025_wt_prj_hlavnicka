from ninja import NinjaAPI, Schema, ModelSchema  # Přidán import ModelSchema
from ninja.responses import Response
from ninja.security import django_auth
from app.services import extract_smart_dates
from typing import Optional, Any
from app.models import Prvek as PrvekModel  
from app.models import Stitek as StitekModel
from ninja.errors import HttpError
from app.templatetags.ceske_data import chytre_datum  
from django.utils import timezone

api = NinjaAPI(title="Aplikace API", version="1.0.0")

class ParseDatesResponse(Schema):
    success: bool
    choice_reason: Optional[str] = None
    start: Optional[str] = None
    end: Optional[str] = None
    display_start: Optional[str] = None
    display_end: Optional[str] = None
    matched_string_start: Optional[str] = None
    matched_string_end: Optional[str] = None
    matched_string_full: Optional[str] = None
    processed_query: str

class StitekSchema(ModelSchema):
    class Meta:
        model = StitekModel
        fields = ["nazev", "barva", "id"]

class PrvekSchema(ModelSchema):
    stitky: list[StitekSchema]
    class Meta:
        model = PrvekModel
        fields = ["id", "nazev", "obsah", "vlastnik", "datum_zacatku", "datum_konce", "datum_vytvoreni", "datum_upravy"]

class PrvekCreateSchema(Schema):
    nazev: str
    obsah: Optional[str] = None
    datum_zacatku: Optional[str] = None
    datum_konce: Optional[str] = None
    stitky: Optional[list[int]] = None

class PrvekUpdateSchema(Schema):
    nazev: Optional[str] = None
    obsah: Optional[str] = None
    datum_zacatku: Optional[str] = None
    datum_konce: Optional[str] = None
    stitky: Optional[list[int]] = None

@api.get("/prvek/", response=list[PrvekSchema], auth=django_auth)
def list_prvky(request):
    if request.user.is_anonymous:
        return []
    return PrvekModel.objects.filter(smazano=False, vlastnik=request.user)

@api.get("/parse-dates/", response=ParseDatesResponse)
def parse_dates(request, q:str = ""):
    if not q.strip():
        return {"success": False, "error": "Prázdný dotaz", "processed_query": ""}
    
    result_data = extract_smart_dates(q)
    return result_data

@api.get("/prvek/{id}/", response=PrvekSchema, auth=django_auth)
def get_prvek(request, id: int):
    try:
        prvek = PrvekModel.objects.get(id=id)
        if prvek.vlastnik != request.user and prvek.vlastnik is not None:
            raise HttpError(403, "Nemáte oprávnění k zobrazení tohoto prvku.")
        if prvek.smazano:
            raise HttpError(404, "Prvek už je smazaný.")
        return prvek
    except PrvekModel.DoesNotExist:
        raise HttpError(404, "Prvek nebyl nalezen.")

@api.delete("/prvek/{id}/", auth=django_auth)
def delete_prvek(request, id: int):
    try:
        prvek = PrvekModel.objects.get(id=id)
        if prvek.vlastnik != request.user or prvek.vlastnik is None:
            raise HttpError(403, "Nemáte oprávnění k odstranění tohoto prvku.")
        prvek.smazano = True
        prvek.save()
        return Response({"success": True})
    except PrvekModel.DoesNotExist:
        raise HttpError(404, "Prvek nebyl nalezen.")

@api.post("/prvek/", response=PrvekSchema, auth=django_auth)
def create_prvek(request, payload: PrvekCreateSchema):
    if request.user.is_anonymous:
        raise HttpError(403, "Musíte být přihlášen pro vytvoření prvku.")

    data = payload.dict(exclude_unset=True)
    stitky_ids = data.pop("stitky", [])
    
    prvek = PrvekModel.objects.create(
        vlastnik=request.user,
        **data
    )
    if stitky_ids:
        prvek.stitky.set(stitky_ids)
    
    return prvek

@api.put("/prvek/{id}/", response=PrvekSchema, auth=django_auth)
def update_prvek_put(request, id: int, payload: PrvekCreateSchema):
    try:
        prvek = PrvekModel.objects.get(id=id)
        if prvek.vlastnik != request.user:
            raise HttpError(403, "Nemáte oprávnění k úpravě tohoto prvku.")
        
        data = payload.dict()
        stitky_ids = data.pop("stitky") or []
        
        for attr, value in data.items():
            setattr(prvek, attr, value)
        
        prvek.stitky.set(stitky_ids)
        prvek.save()
        return prvek
    except PrvekModel.DoesNotExist:
        raise HttpError(404, "Prvek nebyl nalezen.")

@api.patch("/prvek/{id}/", response=PrvekSchema, auth=django_auth)
def update_prvek_patch(request, id: int, payload: PrvekUpdateSchema):
    try:
        prvek = PrvekModel.objects.get(id=id)

        if prvek.vlastnik != request.user or prvek.vlastnik is None:
            raise HttpError(403, "Nemáte oprávnění k úpravě tohoto prvku.")
        
        update_data = payload.dict(exclude_unset=True)
        
        if "stitky" in update_data:
            stitky_ids = update_data.pop("stitky")
            prvek.stitky.set(stitky_ids)

        for attr, value in update_data.items():
            setattr(prvek, attr, value)
            
        prvek.datum_upravy = timezone.now()
        prvek.save()
        
        return prvek
    except PrvekModel.DoesNotExist: 
        raise HttpError(404, "Prvek nebyl nalezen.")

# --- Seznam API ---
from app.models import Seznam as SeznamModel

class SeznamSchema(ModelSchema):
    class Meta:
        model = SeznamModel
        fields = ["id", "nazev", "popis", "vlastnik", "velikostni_typ"]

class SeznamCreateSchema(Schema):
    nazev: str
    popis: Optional[str] = None
    velikostni_typ: str = "střední"

@api.get("/seznam/", response=list[SeznamSchema], auth=django_auth)
def list_seznamy(request):
    if request.user.is_anonymous:
        return []
    return SeznamModel.objects.filter(vlastnik=request.user)

@api.get("/seznam/{id}/", response=SeznamSchema, auth=django_auth)
def get_seznam(request, id: int):
    try:
        seznam = SeznamModel.objects.get(id=id)
        if seznam.vlastnik != request.user:
            raise HttpError(403, "Nemáte oprávnění k zobrazení tohoto seznamu.")
        return seznam
    except SeznamModel.DoesNotExist:
        raise HttpError(404, "Seznam nebyl nalezen.")

@api.post("/seznam/", response=SeznamSchema, auth=django_auth)
def create_seznam(request, payload: SeznamCreateSchema):
    if request.user.is_anonymous:
        raise HttpError(403, "Musíte být přihlášen pro vytvoření seznamu.")
    
    seznam = SeznamModel.objects.create(
        vlastnik=request.user,
        **payload.dict()
    )
    return seznam

@api.get("/stitek/{id}/prvky/", response=list[PrvekSchema], auth=django_auth)
def get_prvky_by_stitek(request, id: int):
    try:
        stitek = StitekModel.objects.get(id=id)
        if stitek.vlastnik != request.user and stitek.vlastnik is not None:
            raise HttpError(403, "Nemáte oprávnění k zobrazení tohoto štítku.")
        if stitek is None:
            raise HttpError(404, "Štítek nebyl nalezen.")
        
        prvky = stitek.prvek_set.filter(smazano=False, vlastnik=request.user)
        return list(prvky)
    except StitekModel.DoesNotExist:
        raise HttpError(404, "Štítek nebyl nalezen.")

@api.get("/stitek/{id}/", response=StitekSchema, auth=django_auth)
def get_stitek(request, id: int):
    try:
        stitek = StitekModel.objects.get(id=id)
        if stitek.vlastnik != request.user and stitek.vlastnik is not None:
            raise HttpError(403, "Nemáte oprávnění k zobrazení tohoto štítku.")
        if stitek is None:
            raise HttpError(404, "Štítek nebyl nalezen.")
        return stitek
    except StitekModel.DoesNotExist:
        raise HttpError(404, "Štítek nebyl nalezen.")


# Připravené pro budoucí použití, zatím nehotové
class LidskyCasResponse(Schema):
    iso: str
    lidske: Any

@api.get("/lidsky-cas/", response=LidskyCasResponse)
def lidsky_cas(request, q: str = ""):
    # ensure we always pass a string to chytre_datum (ISO format for current time)
    if not q.strip():
        cas_iso = timezone.now().isoformat()
    else:
        cas_iso = q.strip()
    try:
        result_data = chytre_datum(cas_iso)
        # chytre_datum may return a string or a dict; handle both safely
        if isinstance(result_data, dict):
            if not result_data.get("success", True):
                raise HttpError(400, "Neplatný formát data")
            lidske = result_data
        else:
            lidske = result_data
        return {"iso": cas_iso, "lidske": lidske}
    except HttpError:
        raise
    except Exception as e:
        raise HttpError(400, f"Chyba při zpracování data: {str(e)}")
