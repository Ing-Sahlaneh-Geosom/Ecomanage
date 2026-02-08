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


class EcoleAssignMixin:
    def form_valid(self, form):
        form.instance.ecole = self.request.user.ecole
        return super().form_valid(form)


class RoleRequiredMixin:
    allowed_roles = []

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            raise PermissionDenied
        if request.user.role not in self.allowed_roles:
            raise PermissionDenied
        return super().dispatch(request, *args , **kwargs)


