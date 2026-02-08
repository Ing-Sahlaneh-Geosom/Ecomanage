from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy, reverse
from django.views.generic import ListView, DetailView, UpdateView, CreateView, DeleteView , TemplateView
from django.contrib import messages
from datetime import time , timedelta , datetime
from Ecole_admin.models import Absence, Eleve, Classe , Proffeseur,  EmploiDuTemps, EmploiDuTempsSoir ,Matier
from Ecole_admin.utils.mixins import ActiveYearMixin, EcoleAssignMixin , RoleRequiredMixin , UserAssignMixin
from Ecole_admin.utils.utils import get_annee_active
from Ecole_admin.form import EmploiDuTempsForm


class ListDesAbsences(LoginRequiredMixin , RoleRequiredMixin , ListView):
    model = Absence
    template_name = 'ListeDesAbsences.html'
    context_object_name = 'absences'
    paginate_by = 20
    login_url = 'Connection'
    allowed_roles = ['admin','proffesseur']

    def get_queryset(self):
        user = self.request.user
        if user.is_proffesseur:
            queryset = Absence.objects.filter(
                ecole = self.request.user.ecole,
                user = user,
                annee_scolaire = get_annee_active(self.request)
            )
        if user.is_admin:
            queryset = Absence.objects.filter(
                ecole=self.request.user.ecole,
                annee_scolaire = get_annee_active(self.request)
            )

        eleve = self.request.GET.get("eleve")
        justifiee = self.request.GET.get("justifiee")
        classe = self.request.GET.get("classe")

        if eleve and eleve != "":
            queryset = queryset.filter(eleve__id = eleve)
        if justifiee and justifiee != "":
            queryset = queryset.filter(justifiee__icontains = justifiee)
        if classe and classe != "":
            queryset = queryset.filter( eleve__classe_id = classe )

        return queryset

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)
        context["All"] = Absence.objects.filter(user=self.request.user , ecole=self.request.user.ecole,annee_scolaire = get_annee_active(self.request)).count
        context['justifiee'] = Absence.objects.filter(user=self.request.user ,ecole=self.request.user.ecole,annee_scolaire = get_annee_active(self.request),justifiee = True).count
        context['Nom_justifiee'] = Absence.objects.filter(user=self.request.user ,ecole=self.request.user.ecole,annee_scolaire = get_annee_active(self.request),justifiee=False).count
        context['eleves'] = Eleve.objects.filter( classe__professeurs=self.request.user.proffeseur , ecole=self.request.user.ecole,annee_scolaire = get_annee_active(self.request)).all
        context['classes'] = Classe.objects.filter( professeurs=self.request.user.proffeseur ,ecole=self.request.user.ecole ).all
        return context





    



class DetailleDesAbsence( LoginRequiredMixin , RoleRequiredMixin , DetailView):
    model = Absence
    template_name = 'detaille_absence.html'
    context_object_name = 'absence'
    login_url = 'Connection'
    allowed_roles = ['admin',]


# views.py
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import render, redirect
from django.utils import timezone

from Ecole_admin.models import Proffeseur, AnneeScolaire
from Ecole_admin.models import ProfesseurAbsence  # ou AbsenceProfesseur

def staff_only(user):
    return user.is_authenticated and user.role in ("admin", "secretaire")

@login_required
def saisie_absences_enseignants(request):
    if not staff_only(request.user):
        raise PermissionDenied()

    annee = AnneeScolaire.get_active()
    ecole = request.user.ecole

    # --------- GET filtres (comme capture) ----------
    date_str = request.GET.get("date") or timezone.localdate().isoformat()
    prof_id = request.GET.get("prof") or ""

    # heures (filtre)
    h_debut = request.GET.get("h_debut") or ""
    h_fin = request.GET.get("h_fin") or ""

    # profs
    profs_qs = Proffeseur.objects.filter(ecole=ecole, actif=True).order_by("nom_conplet")
    if prof_id:
        profs_qs = profs_qs.filter(id=prof_id)
    profs = list(profs_qs)

    # existants (on filtre aussi par heure pour éviter doublons)
    exist_qs = ProfesseurAbsence.objects.filter(
        ecole=ecole,
        annee_scolaire=annee,
        date=date_str,
        professeur__in=profs,
    )
    if h_debut:
        exist_qs = exist_qs.filter(h_debut=h_debut)
    if h_fin:
        exist_qs = exist_qs.filter(h_fin=h_fin)

    exist_map = {a.professeur_id: a for a in exist_qs}

    # --------- POST : enregistrer ----------
    if request.method == "POST":
        date_post = request.POST.get("date") or date_str
        h_debut_post = request.POST.get("h_debut") or None
        h_fin_post = request.POST.get("h_fin") or None

        saved = 0
        for p in profs:
            statut = request.POST.get(f"statut_{p.id}", "present")
            motif = (request.POST.get(f"motif_{p.id}", "") or "").strip()
            justifiee = request.POST.get(f"justifiee_{p.id}") == "1"

            should_save = (statut != "present") or motif or justifiee
            if not should_save:
                old = exist_map.get(p.id)
                if old:
                    old.delete()
                continue

            obj = exist_map.get(p.id)
            if obj:
                obj.statut = statut
                obj.motif = motif
                obj.justifiee = justifiee
                obj.user = request.user
                obj.h_debut = h_debut_post
                obj.h_fin = h_fin_post
                obj.save()
            else:
                ProfesseurAbsence.objects.create(
                    user=request.user,
                    ecole=ecole,
                    annee_scolaire=annee,
                    professeur=p,
                    date=date_post,
                    h_debut=h_debut_post,
                    h_fin=h_fin_post,
                    statut=statut,
                    motif=motif,
                    justifiee=justifiee,
                )
            saved += 1

        messages.success(request, f"✅ Absences enseignants enregistrées ({saved})")
        # on garde filtres + heures dans l’URL
        return redirect(
            f"{request.path}?date={date_post}&prof={prof_id}&h_debut={h_debut_post or ''}&h_fin={h_fin_post or ''}"
        )

    # ✅ Solution B : rows (sans get_item)
    rows = []
    for p in profs:
        rows.append({"p": p, "a": exist_map.get(p.id)})

    return render(request, "saisie_absences_enseignants.html", {
        "annee": annee,
        "date_value": date_str,
        "prof_id": prof_id,
        "h_debut": h_debut,
        "h_fin": h_fin,
        "profs_select": Proffeseur.objects.filter(ecole=ecole, actif=True).order_by("nom_conplet"),
        "rows": rows,
    })



from django.views import View
from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.views.decorators.http import require_GET
from django.utils.html import escape
from django.contrib import messages
from django.db import transaction


class SaisieAbsencesEDTView(View):
    template_name = "edt_absences.html"

    def get(self, request):
        ecole = request.user.ecole
        annee = get_annee_active(request)

        profs = Proffeseur.objects.filter(ecole=ecole, actif=True).order_by("nom_conplet")

        prof_id = request.GET.get("prof") or ""
        matier_id = request.GET.get("matier") or ""
        classe_id = request.GET.get("classe") or ""
        date = request.GET.get("date") or ""
        h_debut = request.GET.get("h_debut") or ""
        h_fin = request.GET.get("h_fin") or ""

        eleves = Eleve.objects.none()
        abs_map = {}

        if classe_id.isdigit() and date and h_debut and h_fin:
            eleves = Eleve.objects.filter(
                ecole=ecole,
                annee_scolaire=annee,
                classe_id=int(classe_id)
            ).order_by("nom")

            # Précharger les absences existantes (pour pré-cocher)
            abs_qs = Absence.objects.filter(
                ecole=ecole,
                annee_scolaire=annee,
                date=date,
                h_debut=h_debut,
                h_fin=h_fin,
                eleve__classe_id=int(classe_id),
            )
            abs_map = {a.eleve_id: a for a in abs_qs}

        return render(request, self.template_name, {
            "profs": profs,
            "prof_id": prof_id,
            "matier_id": matier_id,
            "classe_id": classe_id,
            "date": date,
            "h_debut": h_debut,
            "h_fin": h_fin,
            "eleves": eleves,
            "abs_map": abs_map
        })

    @transaction.atomic
    def post(self, request):
        ecole = request.user.ecole
        annee = get_annee_active(request)

        prof_id = request.POST.get("prof") or ""
        matier_id = request.POST.get("matier") or ""
        classe_id = request.POST.get("classe") or ""
        date = request.POST.get("date") or ""
        h_debut = request.POST.get("h_debut") or ""
        h_fin = request.POST.get("h_fin") or ""

        if not (prof_id.isdigit() and classe_id.isdigit() and date and h_debut and h_fin):
            messages.error(request, "Choisis Enseignant + Classe + Date + Heures.")
            return redirect("absences_edt")

        eleves = Eleve.objects.filter(
            ecole=ecole,
            annee_scolaire=annee,
            classe_id=int(classe_id)
        )

        # Supprimer les anciennes saisies du même créneau (unique_together)
        Absence.objects.filter(
            ecole=ecole,
            annee_scolaire=annee,
            date=date,
            h_debut=h_debut,
            h_fin=h_fin,
            eleve__classe_id=int(classe_id),
        ).delete()

        created = 0

        for e in eleves:
            statut = request.POST.get(f"statut_{e.id}", "present")
            justifiee = request.POST.get(f"justifiee_{e.id}") == "1"
            motif = (request.POST.get(f"motif_{e.id}") or "").strip()

            # ✅ on enregistre seulement si pas "present"
            if statut == "present":
                continue

            Absence.objects.create(
                user=request.user,
                eleve=e,
                statut=statut,
                date=date,
                h_debut=h_debut,
                h_fin=h_fin,
                motif=motif,
                justifiee=justifiee,
                annee_scolaire=annee,
                ecole=ecole
            )
            created += 1

        messages.success(request, f"Absences enregistrées avec succès ({created}).")

        return redirect(
            f"{request.path}?prof={prof_id}&matier={matier_id}&classe={classe_id}&date={date}&h_debut={h_debut}&h_fin={h_fin}"
        )


@require_GET
def ajax_prof_data(request):
    """
    Retourne en une réponse HTML:
    - select matières (1 seule chez toi)
    - select classes (M2M)
    """
    ecole = request.user.ecole
    prof_id = (request.GET.get("prof_id") or "").strip()

    if not prof_id.isdigit():
        return HttpResponse("")

    prof = Proffeseur.objects.filter(id=int(prof_id), ecole=ecole, actif=True).first()
    if not prof:
        return HttpResponse("")

    # Matière (FK -> une seule)
    mat_html = ['<option value="">Sélectionner...</option>']
    if prof.matieres:
        mat_html.append(f'<option value="{prof.matieres.id}">{escape(str(prof.matieres))}</option>')

    # Classes (M2M)
    cls_html = ['<option value="">Sélectionner...</option>']
    for c in prof.classes.filter(ecole=ecole, actif=True).order_by("niveau", "nom"):
        cls_html.append(f'<option value="{c.id}">{escape(str(c))}</option>')

    # On renvoie les deux blocs séparés par un tag simple
    return HttpResponse(
        "<!--MAT-->" + "".join(mat_html) + "<!--CLS-->" + "".join(cls_html)
    )











class AjouterDesAbsences( UserAssignMixin , LoginRequiredMixin , RoleRequiredMixin , ActiveYearMixin , EcoleAssignMixin , CreateView):
    model = Absence
    template_name = 'ajouter_absence.html'
    fields = ['eleve' , 'date','motif','justifiee']
    login_url = 'Connection'
    allowed_roles = ['admin' , 'proffesseur']


    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        annee_active = get_annee_active(self.request)
        ecole = getattr(self.request.user, "ecole", None)
        prof = getattr(self.request.user, "proffeseur")

        if ecole and annee_active:
            form.fields["eleve"].queryset = Eleve.objects.filter(
                ecole = ecole,
                classe__professeurs = prof,
                annee_scolaire = annee_active
            )
        else:
            form.fields["eleve"].queryset = Eleve.objects.none()

        return form

    def get_queryset(self):
        annee = get_annee_active(self.request)
        return Absence.objects.filter(annee_scolaire=annee)




    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["submit_text"] = "Ajouter"
        context["Title"] = "Ajouter Une Absence"
        context['eleves'] = Eleve.objects.filter(annee_scolaire = get_annee_active(self.request), ecole = self.request.user.ecole)
        return context

    def get_initial(self):
        initial = super().get_initial()
        eleve_id = self.kwargs.get("eleve_id")
        if eleve_id:
            initial["eleve"] = eleve_id
        return initial

    def form_valid(self, form):
        eleve_id = self.kwargs.get('eleve_id')
        if eleve_id:
            form.instance.eleve_id = eleve_id
        messages.success(self.request, "Absence ajouter avec success")
        return super().form_valid(form)

    def get_success_url(self):
        eleve_id = self.kwargs.get("eleve_id")
        if eleve_id:
            return reverse("detaille", kwargs={"id": eleve_id})
        return reverse("ListeDesAbsences")





class ModiferDesAbsences(UpdateView):
    model = Absence
    template_name = 'ajouter_absence.html'
    fields = ['eleve' , 'date','motif','justifiee']
    success_url = reverse_lazy("ListeDesAbsences")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["submit_text"] = "Modifier"
        context["Title"] = "Modifier Une Absence"
        return context


class SupprimerDesAbsences(DeleteView):
    model = Absence
    template_name = 'supprimer_absence.html'
    context_object_name = 'absence'
    success_url = reverse_lazy("ListeDesAbsences")





class EmploiDuTempsListView(LoginRequiredMixin, ListView):
    model = EmploiDuTemps
    context_object_name = 'emplois'
    template_name = 'liste_emploi.html'

    def get_queryset(self):
        user = self.request.user
        if hasattr(user, 'eleve'):
            # Élève : voir seulement son emploi
            return EmploiDuTemps.objects.filter(
                classe=user.eleve.classe,
                ecole=user.ecole,
                annee_scolaire = get_annee_active(self.request)
            )
        elif hasattr(user, 'professeur'):
            # Professeur : voir ses cours
            return EmploiDuTemps.objects.filter(
                professeur=user.professeur,
                ecole=user.ecole,
                annee_scolaire = get_annee_active(self.request)
            )
        else:
            # Admin : voir tout
            return EmploiDuTemps.objects.filter(
                ecole=user.ecole,
                annee_scolaire=self.request.annee_active
            )


class EmploiDuTempsCreateView(LoginRequiredMixin, EcoleAssignMixin, ActiveYearMixin, CreateView):
    model = EmploiDuTemps
    form_class = EmploiDuTempsForm
    template_name = 'ajout_emploi.html'
    success_url = reverse_lazy('liste_emploi')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs



class EmploiDuTempsGrilleView(LoginRequiredMixin, TemplateView):
    template_name = 'grille_emploi.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        # On filtre selon le rôle
        if hasattr(user, 'eleve'):
            emplois = EmploiDuTemps.objects.filter(
                classe=user.eleve.classe,
                ecole=user.ecole,
                annee_scolaire = get_annee_active(self.request)
            )
        elif hasattr(user, 'professeur'):
            emplois = EmploiDuTemps.objects.filter(
                professeur=user.professeur,
                ecole=user.ecole,
                annee_scolaire = get_annee_active(self.request)
            )
        else:
            emplois = EmploiDuTemps.objects.filter(
                ecole=user.ecole,
                annee_scolaire = get_annee_active(self.request)
            )

        heures = []
        current = datetime(2000, 1, 1, 7, 30)
        end = datetime(2000, 1, 1, 18, 30)
        while current <= end:
            heures.append(current.time())
            current += timedelta(hours=1)

        jours = ['Samedi' , 'Dimanche' , 'Lundi', 'Mardi', 'Mercredi', 'Jeudi']
        context['jours'] = jours
        context['hours']= heures

        context['emplois'] = emplois
        return context
    




# views.py
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from django.core.exceptions import PermissionDenied
from django.contrib import messages

from Ecole_admin.models import EmploiDuTemps
from Ecole_admin.form import EmploiDuTempsForm


def staff_only(user):
    return user.is_authenticated and user.role in ("admin", "secretaire")

@login_required
def emploi_list(request):
    if not staff_only(request.user):
        raise PermissionDenied()

    annee_active = get_annee_active(request)
    emplois = EmploiDuTemps.objects.filter(
        ecole=request.user.ecole,
        annee_scolaire=annee_active
    ).select_related("classe", "matiere", "professeur__user", "salle")

    return render(request, "emploi_list.html", {
        "emplois": emplois,
        "annee_active": annee_active
    })


 # views.py
from datetime import datetime, date, timedelta
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_GET, require_POST

from Ecole_admin.models import EmploiDuTemps, Niveau, Classe, Salle, Proffeseur, Matier
from Ecole_admin.form import EmploiDuTempsForm


def staff_only(user):
    return user.is_authenticated and user.role in ("admin", "secretaire")


# =========================
# Time config
# =========================
MORNING_START = "07:30"
MORNING_END   = "12:30"
AFTER_START   = "14:30"
AFTER_END     = "18:30"
STEP_MINUTES  = 60

def parse_hm(s: str):
    return datetime.strptime(s, "%H:%M").time()

def hm(t):
    return t.strftime("%H:%M")

def add_minutes(t, minutes: int):
    dt = datetime.combine(date(2000, 1, 1), t) + timedelta(minutes=minutes)
    return dt.time()

def overlaps(a_start, a_end, b_start, b_end):
    return (a_start < b_end) and (a_end > b_start)

def gen_candidate_starts(start_t, end_t, duration_min):
    start_dt = datetime.combine(date(2000,1,1), start_t)
    last_start = datetime.combine(date(2000,1,1), end_t) - timedelta(minutes=duration_min)
    while start_dt <= last_start:
        yield start_dt.time()
        start_dt += timedelta(minutes=STEP_MINUTES)


# =========================
# LIST
# =========================
@login_required
def emploi_list(request):
    if not staff_only(request.user):
        raise PermissionDenied()

    ecole = request.user.ecole
    annee_active = get_annee_active(request)

    qs = EmploiDuTemps.objects.filter(ecole=ecole, annee_scolaire=annee_active)\
        .select_related("classe", "matiere", "professeur", "salle")\
        .order_by("jour", "heure_debut")

    return render(request, "emploi_list.html", {
        "emplois": qs,
        "annee_active": annee_active,
    })


# =========================
# CREATE / UPDATE (auto page)
# =========================
@login_required
def emploi_create_auto(request):
    if not staff_only(request.user):
        raise PermissionDenied()

    annee_active = get_annee_active(request)

    if request.method == "POST":
        form = EmploiDuTempsForm(request.POST, request=request)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.ecole = request.user.ecole
            obj.annee_scolaire = annee_active
            obj.save()
            messages.success(request, "Créneau ajouté.")
            return redirect("emploi_list")
    else:
        form = EmploiDuTempsForm(request=request)

    return render(request, "emploi_form_auto.html", {
        "mode": "create",
        "form": form,
        "annee_active": annee_active,
        "morning_start": MORNING_START,
        "morning_end": MORNING_END,
        "after_start": AFTER_START,
        "after_end": AFTER_END,
    })


@login_required
def emploi_update_auto(request, pk):
    if not staff_only(request.user):
        raise PermissionDenied()

    ecole = request.user.ecole
    annee_active = get_annee_active(request)

    obj = get_object_or_404(EmploiDuTemps, pk=pk, ecole=ecole, annee_scolaire=annee_active)

    if request.method == "POST":
        form = EmploiDuTempsForm(request.POST, instance=obj, request=request)
        if form.is_valid():
            form.save()
            messages.success(request, "Créneau mis à jour.")
            return redirect("emploi_list")
    else:
        form = EmploiDuTempsForm(instance=obj, request=request)

    return render(request, "emploi_form_auto.html", {
        "mode": "update",
        "obj": obj,
        "form": form,
        "annee_active": annee_active,
        "morning_start": MORNING_START,
        "morning_end": MORNING_END,
        "after_start": AFTER_START,
        "after_end": AFTER_END,
    })


# =========================
# DELETE (POST only)
# =========================
@login_required
@require_POST
def emploi_delete(request, pk):
    if not staff_only(request.user):
        raise PermissionDenied()

    ecole = request.user.ecole
    annee_active = get_annee_active(request)

    obj = get_object_or_404(EmploiDuTemps, pk=pk, ecole=ecole, annee_scolaire=annee_active)
    obj.delete()
    messages.success(request, "Créneau supprimé.")
    return redirect("emploi_list")


# =========================
# APIs AJAX
# =========================
@login_required
@require_GET
def api_niveaux(request):
    if not staff_only(request.user):
        raise PermissionDenied()
    ecole = request.user.ecole
    niveaux = Niveau.objects.filter(ecole=ecole, actif=True).order_by("ordre", "nom")
    return JsonResponse({"items": [{"id": n.id, "nom": n.nom} for n in niveaux]})


@login_required
@require_GET
def api_classes(request):
    if not staff_only(request.user):
        raise PermissionDenied()
    ecole = request.user.ecole
    niveau_id = request.GET.get("niveau_id") or ""
    qs = Classe.objects.filter(ecole=ecole, actif=True)
    if niveau_id:
        qs = qs.filter(niveau_id=niveau_id)
    qs = qs.order_by("nom", "id")
    return JsonResponse({"items": [{"id": c.id, "nom": c.nom} for c in qs]})


@login_required
@require_GET
def api_slots(request):
    """
    créneaux dispos (classe + jour + durée + période)
    période: morning | afternoon
    """
    if not staff_only(request.user):
        raise PermissionDenied()

    ecole = request.user.ecole
    annee_active = get_annee_active(request)

    classe_id = request.GET.get("classe_id") or ""
    jour = request.GET.get("jour") or ""
    duration = int(request.GET.get("duration") or 60)
    period = (request.GET.get("period") or "morning").strip().lower()

    if not (classe_id and jour):
        return JsonResponse({"ok": False, "items": [], "error": "classe_id et jour requis"}, status=400)

    if period == "afternoon":
        start_t = parse_hm(AFTER_START)
        end_t = parse_hm(AFTER_END)
        period_label = f"Après-midi ({AFTER_START}-{AFTER_END})"
    else:
        start_t = parse_hm(MORNING_START)
        end_t = parse_hm(MORNING_END)
        period_label = f"Matin ({MORNING_START}-{MORNING_END})"

    emplois = EmploiDuTemps.objects.filter(
        ecole=ecole,
        annee_scolaire=annee_active,
        classe_id=classe_id,
        jour=jour,
    ).filter(
        heure_debut__lt=end_t,
        heure_fin__gt=start_t
    ).values_list("heure_debut", "heure_fin")

    busy = [{"start": hm(hd), "end": hm(hf)} for (hd, hf) in emplois]

    available = []
    for st in gen_candidate_starts(start_t, end_t, duration):
        en = add_minutes(st, duration)
        conflict = any(overlaps(st, en, hd, hf) for (hd, hf) in emplois)
        if not conflict:
            available.append({"start": hm(st), "end": hm(en), "label": f"{hm(st)} - {hm(en)}"})

    return JsonResponse({"ok": True, "busy": busy, "items": available, "period_label": period_label})


@login_required
@require_GET
def api_resources_free(request):
    """
    pour un créneau choisi:
    - salles libres
    - profs libres (✅ filtrés par classe)
    """
    if not staff_only(request.user):
        raise PermissionDenied()

    ecole = request.user.ecole
    annee_active = get_annee_active(request)

    jour = request.GET.get("jour") or ""
    start_s = request.GET.get("start") or ""
    end_s = request.GET.get("end") or ""
    classe_id = request.GET.get("classe_id") or ""

    if not (jour and start_s and end_s and classe_id):
        return JsonResponse({"ok": False, "error": "jour/start/end/classe_id requis"}, status=400)

    st = parse_hm(start_s)
    en = parse_hm(end_s)

    overlap_q = Q(heure_debut__lt=en) & Q(heure_fin__gt=st)

    occ = EmploiDuTemps.objects.filter(
        ecole=ecole,
        annee_scolaire=annee_active,
        jour=jour,
    ).filter(overlap_q)

    busy_salles = list(occ.values_list("salle_id", flat=True).distinct())
    busy_profs = list(occ.values_list("professeur_id", flat=True).distinct())

    # salles libres
    salles = Salle.objects.filter(ecole=ecole).exclude(id__in=busy_salles).order_by("nom", "id")
    salles_items = [{"id": s.id, "label": str(s)} for s in salles]

    # ✅ profs libres + ✅ profs de la classe
    profs = Proffeseur.objects.filter(ecole=ecole, actif=True, classes__id=classe_id)\
        .exclude(id__in=busy_profs).order_by("nom_conplet", "id")
    profs_items = [{"id": p.id, "label": p.nom_conplet} for p in profs]

    return JsonResponse({"ok": True, "salles": salles_items, "profs": profs_items})


@login_required
@require_GET
def api_matieres_by_prof(request):
    """
    ✅ matières filtrées par prof (chez toi: 1 matière via Proffeseur.matieres)
    et aussi vérifie que la matière appartient à la classe.
    """
    if not staff_only(request.user):
        raise PermissionDenied()

    ecole = request.user.ecole
    prof_id = request.GET.get("professeur_id") or ""
    classe_id = request.GET.get("classe_id") or ""

    if not (prof_id and classe_id):
        return JsonResponse({"ok": False, "items": [], "error": "professeur_id et classe_id requis"}, status=400)

    prof = get_object_or_404(Proffeseur, id=prof_id, ecole=ecole, actif=True)

    items = []
    if prof.matieres_id:
        m = Matier.objects.filter(id=prof.matieres_id, ecole=ecole, classe_id=classe_id).first()
        if m:
            items.append({"id": m.id, "nom": m.nom})

    return JsonResponse({"ok": True, "items": items})









class EmploiDuTempsSoirListView(LoginRequiredMixin, ListView):
    model = EmploiDuTempsSoir
    context_object_name = 'emplois'
    template_name = 'liste_emploi_soir.html'

    def get_queryset(self):
        user = self.request.user
        if hasattr(user, 'eleve'):
            # Élève : voir seulement son emploi
            return EmploiDuTemps.objects.filter(
                classe=user.eleve.classe,
                ecole=user.ecole,
                annee_scolaire = get_annee_active(self.request)
            )
        elif hasattr(user, 'professeur'):
            # Professeur : voir ses cours
            return EmploiDuTemps.objects.filter(
                professeur=user.professeur,
                ecole=user.ecole,
                annee_scolaire = get_annee_active(self.request)
            )
        else:
            # Admin : voir tout
            return EmploiDuTemps.objects.filter(
                ecole=user.ecole,
                annee_scolaire=self.request.annee_active
            )


class EmploiDuTempsSoirCreateView(LoginRequiredMixin, EcoleAssignMixin, ActiveYearMixin, CreateView):
    model = EmploiDuTempsSoir
    form_class = EmploiDuTempsForm
    template_name = 'ajout_emploi_soir.html'
    success_url = reverse_lazy('liste_emploi')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs



class EmploiDuTempsSoirGrilleView(LoginRequiredMixin, TemplateView):
    template_name = 'grille_emploi_soir.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        # On filtre selon le rôle
        if hasattr(user, 'eleve'):
            emplois = EmploiDuTempsSoir.objects.filter(
                classe=user.eleve.classe,
                ecole=user.ecole,
                annee_scolaire = get_annee_active(self.request)
            )
        elif hasattr(user, 'proffeseur'):
            emplois = EmploiDuTempsSoir.objects.filter(
                professeur=user.proffeseur,
                ecole=user.ecole,
                annee_scolaire = get_annee_active(self.request)
            )
        else:
            emplois = EmploiDuTempsSoir.objects.filter(
                ecole=user.ecole,
                annee_scolaire = get_annee_active(self.request)
            )

        heures = []
        current = datetime(2000, 1, 1, 18, 30)
        end = datetime(2000, 1, 1, 23, 30)
        while current <= end:
            heures.append(current.time())
            current += timedelta(hours=1)

        soires = ['Samedi' , 'Dimanche' , 'Lundi', 'Mardi', 'Mercredi', 'Jeudi']
        context['soires'] = soires
        context['hours']= heures

        context['emplois'] = emplois
        return context



from datetime import date

from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.shortcuts import render

from Ecole_admin.models import Absence, Eleve, Classe, Niveau, PeriodeScolaire, AnneeScolaire

FR_MONTHS = {
    1: "Janvier", 2: "Février", 3: "Mars", 4: "Avril", 5: "Mai", 6: "Juin",
    7: "Juillet", 8: "Août", 9: "Septembre", 10: "Octobre", 11: "Novembre", 12: "Décembre"
}

def _require_staff(user):
    return user.is_authenticated and (
        user.is_superuser or getattr(user, "role", "") in ("admin", "secretaire")
    )

def _months_in_period(d1: date, d2: date):
    out = []
    y, m = d1.year, d1.month
    while (y < d2.year) or (y == d2.year and m <= d2.month):
        out.append((y, m))
        m += 1
        if m == 13:
            m = 1
            y += 1
    return out

def _safe_period(ecole, annee, pid: str):
    if not pid:
        return None
    try:
        return PeriodeScolaire.objects.get(id=pid, ecole=ecole, annee_scolaire=annee)
    except PeriodeScolaire.DoesNotExist:
        return None


@login_required
def suivi_absences_par_mois(request):
    if not _require_staff(request.user):
        return HttpResponseForbidden("Accès refusé")

    ecole = getattr(request.user, "ecole", None)
    annee = AnneeScolaire.get_active()  # ✅ on garde active en interne (pas dans filtre)

    niveaux = Niveau.objects.all().order_by("ordre", "nom")
    classes = Classe.objects.filter(ecole=ecole).select_related("niveau").order_by("niveau__ordre", "nom")
    periodes = PeriodeScolaire.objects.filter(ecole=ecole, annee_scolaire=annee).order_by("debut")

    niveau_id = request.GET.get("niveau") or ""
    classe_id = request.GET.get("classe") or ""
    periode_id = request.GET.get("periode") or ""

    periode = _safe_period(ecole, annee, periode_id)

    months = []   # [{"key":"YYYY-MM","label":"Septembre"}...]
    rows = []     # lignes tableau

    if periode and classe_id:
        months_raw = _months_in_period(periode.debut, periode.fin)
        months = [{"key": f"{y:04d}-{m:02d}", "label": FR_MONTHS[m]} for (y, m) in months_raw]

        eleves = Eleve.objects.filter(
            ecole=ecole,
            annee_scolaire=annee,
            classe_id=classe_id
        ).order_by("nom")

        classe_label = Classe.objects.filter(id=classe_id).values_list("nom", flat=True).first() or ""

        # absences dans période (toutes + justifiées)
        abs_qs = Absence.objects.filter(
            ecole=ecole,
            annee_scolaire=annee,
            eleve__classe_id=classe_id,
            statut="absence",
            date__range=(periode.debut, periode.fin),
        ).values("eleve_id", "date", "justifiee")

        bucket_all = {}   # (eleve_id, "YYYY-MM") -> count
        bucket_aj = {}    # (eleve_id, "YYYY-MM") -> count justifiee

        for a in abs_qs:
            d = a["date"]
            ym = f"{d.year:04d}-{d.month:02d}"
            k = (a["eleve_id"], ym)

            bucket_all[k] = bucket_all.get(k, 0) + 1
            if a["justifiee"]:
                bucket_aj[k] = bucket_aj.get(k, 0) + 1

        for idx, e in enumerate(eleves, start=1):
            vals = []
            total = 0
            total_aj = 0

            for mo in months:
                ym = mo["key"]
                n = bucket_all.get((e.id, ym), 0)
                n_aj = bucket_aj.get((e.id, ym), 0)
                vals.append(n)
                total += n
                total_aj += n_aj

            rows.append({
                "i": idx,
                "eleve": e,
                "classe_label": classe_label,
                "vals": vals,
                "total": total,
                "aj": total_aj,
            })

    context = {
        "niveaux": niveaux,
        "classes": classes,
        "periodes": periodes,

        "niveau_id": niveau_id,
        "classe_id": classe_id,
        "periode_id": periode_id,

        "periode": periode,
        "months": months,
        "rows": rows,
    }
    return render(request, "suivi_absences_mois.html", context)

from calendar import monthrange
from datetime import date
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import render, redirect, get_object_or_404

from Ecole_admin.models import ProfesseurAbsence, Proffeseur, AnneeScolaire

def staff_only(user):
    return user.is_authenticated and user.role in ("admin", "secretaire")

@login_required
def suivi_absences_enseignants(request):
    if not staff_only(request.user):
        raise PermissionDenied()

    ecole = request.user.ecole

    # ✅ années présentes en DB (select)
    annees_db = AnneeScolaire.objects.order_by("-debut")
    annee_active = AnneeScolaire.get_active()
    annee_id = request.GET.get("annee_id") or str(annee_active.id)

    # ✅ mois
    today = date.today()
    mois = int(request.GET.get("mois", today.month))

    # ✅ prof
    prof_id = request.GET.get("prof") or ""

    # année scolaire sélectionnée
    annee_obj = get_object_or_404(AnneeScolaire, id=annee_id)

    # ✅ on utilise l'année de "debut" (ou today.year si vide)
    year = annee_obj.debut.year if getattr(annee_obj, "debut", None) else today.year
    start_date = date(year, mois, 1)
    end_date = date(year, mois, monthrange(year, mois)[1])

    qs = ProfesseurAbsence.objects.filter(
        ecole=ecole,
        annee_scolaire=annee_obj,
        date__range=(start_date, end_date),
    ).select_related("professeur").order_by("date", "h_debut")

    if prof_id:
        qs = qs.filter(professeur_id=prof_id)

    # suppression
    if request.method == "POST":
        abs_id = request.POST.get("delete_id")
        if abs_id:
            obj = get_object_or_404(
                ProfesseurAbsence,
                id=abs_id,
                ecole=ecole,
                annee_scolaire=annee_obj
            )
            obj.delete()
            messages.success(request, "✅ Absence supprimée")
            return redirect(request.get_full_path())

    return render(request, "suivi_absences_enseignants.html", {
        "rows": qs,
        "profs": Proffeseur.objects.filter(ecole=ecole, actif=True).order_by("nom_conplet"),
        "annees_db": annees_db,
        "annee_id": str(annee_obj.id),
        "mois": mois,
        "prof_id": prof_id,
    })
