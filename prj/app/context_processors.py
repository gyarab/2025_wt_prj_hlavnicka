from django.conf import settings


def vue_frontend(request):
    """Zpřístupní VUE_FRONTEND_URL ve všech šablonách (odkaz na Vue SPA v navigaci
    i na rozcestníku). Lokálně míří na Vite dev server (:5173), v produkci na /app/."""
    return {"vue_frontend_url": settings.VUE_FRONTEND_URL}
