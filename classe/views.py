from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render
from django.urls import reverse_lazy
from django.views.generic import CreateView, ListView, UpdateView, DeleteView, DetailView

from Ecole_admin.models import Classe , Specialite , Niveau
from Ecole_admin.utils.mixins import EcoleAssignMixin
from Ecole_admin.utils.utils import get_annee_active
from classe.form import ClasseForm



class ClasseCreateView(EcoleAssignMixin,CreateView):
    model = Classe
    template_name = "AjouterUneClasse.html"
    fields = '__all__'
    success_url = reverse_lazy("ListeDesClasse")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['submit_text'] = "Ajouter"
        context['Title'] = "Ajouter une classe"
        return context

    def form_valid(self, form):
        messages.success(self.request, "Le classe et ajouter avec success")
        return super().form_valid(form)

class SpecialiteCreateView(EcoleAssignMixin,CreateView):
    model = Specialite
    template_name = "AjouterUneSpecialite.html"
    fields = '__all__'
    success_url = reverse_lazy("CreeDesSpecialite")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['submit_text'] = "Ajouter"
        context['Title'] = "Ajouter une Specialite"
        return context

    def form_valid(self, form):
        messages.success(self.request, "Un Specialite et ajouter avec success")
        return super().form_valid(form)


class NiveauCreateView(EcoleAssignMixin,CreateView):
    model = Niveau
    template_name = "AjouterUnNiveau.html"
    fields = '__all__'
    success_url = reverse_lazy("CreeDesNiveau")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['submit_text'] = "Ajouter"
        context['Title'] = "Ajouter une Niveau"
        return context

    def form_valid(self, form):
        messages.success(self.request, "Le Niveau et ajouter avec success")
        return super().form_valid(form)




class ListeDesClasse(LoginRequiredMixin ,ListView):
    model = Classe
    template_name = 'listedesclasses.html'
    context_object_name = "classes"
    paginate_by = 20

    def get_queryset(self):
        queryset = Classe.objects.filter(
            ecole=self.request.user.ecole,
        )

        nom = self.request.GET.get("nom")

        if nom and nom != "":
            queryset = queryset.filter(nom__icontains = nom)

        return queryset




class ClasseUpdateView(EcoleAssignMixin , UpdateView):
    model = Classe
    template_name = "AjouterUneClasse.html"
    fields = "__all__"
    success_url = reverse_lazy("ListeDesClasse")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["submit_text"] = "Modifier"
        context["Title"] = "Modifier une classe"
        return context

class ClasseDeleteView(DeleteView):
    model = Classe
    template_name = "deleteClasse.html"
    success_url = reverse_lazy("ListeDesClasse")

class ClasseDetailView(DetailView):
    model = Classe
    template_name = "detailleClasse.html"
    context_object_name = "classes"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['eleves'] = self.object.eleves.all()
        return context
    

from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.http import JsonResponse
from django.shortcuts import render
from django.utils import timezone
from django.views.decorators.http import require_POST

from Ecole_admin.models import Niveau, Classe, Eleve, RaisonConvocation, AnneeScolaire

User = get_user_model()

def _active_annee():
    try:
        return AnneeScolaire.get_active()
    except Exception:
        return AnneeScolaire.objects.order_by("-debut").first()


@login_required
def convocation_parent(request):
    ecole = getattr(request.user, "ecole", None)
    annee = _active_annee()

    niveaux = Niveau.objects.all()
    if hasattr(Niveau, "actif"):
        niveaux = niveaux.filter(actif=True)
    if ecole and hasattr(Niveau, "ecole_id"):
        niveaux = niveaux.filter(ecole=ecole)
    niveaux = niveaux.order_by("nom")

    raisons = RaisonConvocation.objects.all()
    if hasattr(RaisonConvocation, "actif"):
        raisons = raisons.filter(actif=True)
    if ecole and hasattr(RaisonConvocation, "ecole_id"):
        raisons = raisons.filter(ecole=ecole)
    raisons = raisons.order_by("libelle")

    # ✅ RESPONSABLE établissement = Admin/Secrétaire
    responsables = User.objects.filter(role__in=["admin", "secretaire"])
    if ecole and hasattr(User, "ecole_id"):
        responsables = responsables.filter(ecole=ecole)
    responsables = responsables.order_by("nom_complet", "username")

    return render(request, "convocation_parent.html", {
        "ecole": ecole,
        "annee": annee,
        "today": timezone.localdate(),
        "niveaux": niveaux,
        "raisons": raisons,
        "responsables": responsables,
    })


@login_required
def ajax_classes_by_niveau(request):
    niveau_id = request.GET.get("niveau_id")
    if not niveau_id:
        return JsonResponse({"ok": True, "classes": []})

    ecole = getattr(request.user, "ecole", None)
    qs = Classe.objects.filter(niveau_id=niveau_id)
    if hasattr(Classe, "actif"):
        qs = qs.filter(actif=True)
    if ecole and hasattr(Classe, "ecole_id"):
        qs = qs.filter(ecole=ecole)

    data = [{"id": c.id, "label": c.nom} for c in qs.order_by("nom")]
    return JsonResponse({"ok": True, "classes": data})


@login_required
def ajax_eleves_by_classe(request):
    classe_id = request.GET.get("classe_id")
    if not classe_id:
        return JsonResponse({"ok": True, "eleves": []})

    ecole = getattr(request.user, "ecole", None)
    annee = _active_annee()

    qs = Eleve.objects.filter(classe_id=classe_id)
    if ecole and hasattr(Eleve, "ecole_id"):
        qs = qs.filter(ecole=ecole)
    if annee and hasattr(Eleve, "annee_scolaire_id"):
        qs = qs.filter(annee_scolaire=annee)
    if hasattr(Eleve, "actif"):
        qs = qs.filter(actif=True)

    data = [{"id": e.id, "label": e.nom} for e in qs.order_by("nom")]
    return JsonResponse({"ok": True, "eleves": data})


@require_POST
@login_required
def ajax_raisons_create(request):
    ecole = getattr(request.user, "ecole", None)
    libelle = (request.POST.get("libelle") or "").strip()
    if not libelle:
        return JsonResponse({"ok": False, "error": "Libellé obligatoire"}, status=400)

    obj = RaisonConvocation(libelle=libelle)
    if ecole and hasattr(obj, "ecole_id"):
        obj.ecole = ecole
    if hasattr(obj, "actif"):
        obj.actif = True
    obj.save()

    return JsonResponse({"ok": True, "raison": {"id": obj.id, "libelle": obj.libelle}})
