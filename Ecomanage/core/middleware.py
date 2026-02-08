from django.utils import translation
from django.conf import settings

class SchoolLanguageMiddleware:
    """
    Force la langue de l'interface selon l'école du user connecté.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        lang = None

        if request.user.is_authenticated:
            ecole = getattr(request.user, "ecole", None)
            if ecole and getattr(ecole, "langue", None):
                lang = ecole.langue

        # fallback si pas connecté ou pas d'école
        if not lang:
            lang = getattr(settings, "LANGUAGE_CODE", "fr")[:2]

        translation.activate(lang)
        request.LANGUAGE_CODE = lang

        response = self.get_response(request)

        translation.deactivate()
        return response
