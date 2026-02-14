from django.core.exceptions import PermissionDenied

from Ecole_admin.models import AnneeScolaire, Eleve
from Ecole_admin.utils.utils import get_annee_active


class ActiveYearMixin:
    def form_valid(self, form):
        instance = form.save(commit=False)
        instance.annee_scolaire = AnneeScolaire.get_active()
        instance.save()
        return super().form_valid(form)

class UserAssignMixin:
    def form_valid(self , form):
        form.instance.user = self.request.user
        return super().form_valid(form)


# mixins.py
from django.core.exceptions import PermissionDenied

class EcoleAssignMixin:
    """
    - Sur CREATE: force instance.ecole = request.user.ecole
    - Sur UPDATE/DELETE/DETAIL: empêche accès aux objets d'une autre école via get_queryset()
    """
    def get_queryset(self):
        qs = super().get_queryset()
        user_ecole = getattr(self.request.user, "ecole", None)

        # si user n'a pas d'école => pas d'accès
        if not user_ecole:
            return qs.none()

        # si le modèle a un champ ecole => filtrer (sécurité anti IDOR)
        try:
            qs.model._meta.get_field("ecole")
            return qs.filter(ecole=user_ecole)
        except Exception:
            return qs

    def form_valid(self, form):
        user_ecole = getattr(self.request.user, "ecole", None)
        if not user_ecole:
            raise PermissionDenied("Aucune école associée à cet utilisateur.")

        # ✅ CREATE => on force l'école
        if not form.instance.pk:
            form.instance.ecole = user_ecole
            return super().form_valid(form)

        # ✅ UPDATE => on vérifie que l'objet appartient à la même école
        instance_ecole_id = getattr(form.instance, "ecole_id", None)
        if instance_ecole_id != user_ecole.id:
            raise PermissionDenied("Accès refusé: objet d'une autre école.")

        return super().form_valid(form)



class RoleRequiredMixin:
    allowed_roles = []

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            raise PermissionDenied
        if request.user.role not in self.allowed_roles:
            raise PermissionDenied
        return super().dispatch(request, *args , **kwargs)


