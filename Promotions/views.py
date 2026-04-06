from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.translation import gettext_lazy as _

from Ecole_admin.form import (
    PromotionListeFilterForm,
    PromotionEvaluationForm,
    PromotionValidationForm,
)
from Ecole_admin.models import (
    Absence,
    AnneeScolaire,
    Eleve,
    Note,
    PromotionEleve,
    PromotionEtat,
    PromotionDecisionCode,
)


def _get_user_ecole(request):
    ecole = getattr(request.user, "ecole", None)
    if not ecole:
        raise ValueError(_("Aucune école n'est liée à cet utilisateur."))
    return ecole


def _get_active_annee():
    try:
        return AnneeScolaire.get_active()
    except Exception:
        annee = AnneeScolaire.objects.order_by("-debut").first()
        if not annee:
            raise ValueError(_("Aucune année scolaire active n'a été trouvée."))
        return annee


def _sync_promotions(ecole, annee_scolaire):
    eleves = Eleve.objects.filter(
        ecole=ecole,
        annee_scolaire=annee_scolaire
    ).select_related("classe__niveau")

    existing_ids = set(
        PromotionEleve.objects.filter(
            ecole=ecole,
            annee_scolaire=annee_scolaire
        ).values_list("eleve_id", flat=True)
    )

    to_create = []
    for eleve in eleves:
        if eleve.id not in existing_ids:
            to_create.append(
                PromotionEleve(
                    ecole=ecole,
                    annee_scolaire=annee_scolaire,
                    eleve=eleve,
                    classe_actuelle=eleve.classe,
                    niveau_actuel=eleve.classe.niveau if eleve.classe_id else None,
                )
            )

    if to_create:
        PromotionEleve.objects.bulk_create(to_create)

@login_required
def promotion_liste_attente(request):
    try:
        ecole = _get_user_ecole(request)
        annee_active = _get_active_annee()
    except ValueError as e:
        messages.error(request, str(e))
        return redirect("home")

    selected_annee_id = request.GET.get("annee_scolaire")
    if selected_annee_id:
        annee_scolaire = AnneeScolaire.objects.filter(pk=selected_annee_id).first()
    else:
        annee_scolaire = None

    # sync seulement si une année existe
    if annee_scolaire:
        _sync_promotions(ecole, annee_scolaire)
    else:
        _sync_promotions(ecole, annee_active)

    initial = {}
    if not request.GET:
        initial["annee_scolaire"] = annee_active

    form = PromotionListeFilterForm(
        request.GET or None,
        ecole=ecole,
        initial=initial
    )

    qs = PromotionEleve.objects.filter(
        ecole=ecole,
        etat__in=[
            PromotionEtat.EN_ATTENTE,
            PromotionEtat.EVALUE,
            PromotionEtat.VALIDE,
        ]
    ).select_related(
        "eleve",
        "annee_scolaire",
        "niveau_actuel",
        "classe_actuelle",
        "prochaine_classe",
        "prochaine_specialite",
    ).order_by(
        "annee_scolaire__debut",
        "niveau_actuel__ordre",
        "classe_actuelle__nom",
        "eleve__nom"
    )

    if form.is_valid():
        q = form.cleaned_data.get("q")
        annee = form.cleaned_data.get("annee_scolaire")
        niveau = form.cleaned_data.get("niveau")
        classe = form.cleaned_data.get("classe")
        decision = form.cleaned_data.get("decision")
        etat = form.cleaned_data.get("etat")

        if annee:
            qs = qs.filter(annee_scolaire=annee)

        if q:
            qs = qs.filter(
                Q(eleve__nom__icontains=q) |
                Q(eleve__identifiant__icontains=q)
            )

        if niveau:
            qs = qs.filter(niveau_actuel=niveau)

        if classe:
            qs = qs.filter(classe_actuelle=classe)

        if decision:
            qs = qs.filter(
                Q(decision_proposee=decision) |
                Q(decision_finale=decision)
            )

        if etat:
            qs = qs.filter(etat=etat)

    context = {
        "titre": _("Étudiants en attente d'une décision"),
        "form": form,
        "promotions": qs,
        "total": qs.count(),
        "annee_scolaire_selectionnee": form.cleaned_data.get("annee_scolaire") if form.is_valid() else None,
    }
    return render(request, "promotion/liste_attente.html", context)


@login_required
def promotion_evaluer(request, pk):
    try:
        ecole = _get_user_ecole(request)
    except ValueError as e:
        messages.error(request, str(e))
        return redirect("home")

    promotion = get_object_or_404(
        PromotionEleve.objects.select_related(
            "eleve",
            "annee_scolaire",
            "classe_actuelle",
            "niveau_actuel",
            "prochaine_classe",
            "prochaine_specialite",
        ),
        pk=pk,
        ecole=ecole,
    )

    notes = Note.objects.filter(
        eleve=promotion.eleve,
        ecole=ecole,
        annee_scolaire=promotion.annee_scolaire,
    ).select_related("matiere", "devoir").order_by("matiere__nom", "trimestre")

    absences = Absence.objects.filter(
        eleve=promotion.eleve,
        ecole=ecole,
        annee_scolaire=promotion.annee_scolaire,
    ).order_by("-date")[:20]

    form = PromotionEvaluationForm(
            request.POST or None,
            instance=promotion,
            ecole=ecole,
            niveau_actuel=promotion.niveau_actuel,
            decision=promotion.decision_proposee or PromotionDecisionCode.ADMIS,
        )

    if request.method == "POST":
        if "evaluer_auto" in request.POST:
            promotion.proposer_decision(user=request.user)

            # recharge après décision auto pour recalculer le bon queryset / valeur par défaut
            return redirect("promotion:promotion_evaluer", pk=promotion.pk)

        if "enregistrer_evaluation" in request.POST and form.is_valid():
            obj = form.save(commit=False)

            promotion.prochaine_classe = obj.prochaine_classe if obj.prochaine_classe else None
            promotion.prochaine_specialite = obj.prochaine_specialite if obj.prochaine_specialite else None
            promotion.commentaire = obj.commentaire

            promotion.save()

            messages.success(request, _("Les informations d'évaluation ont été enregistrées."))
            return redirect("promotion:promotion_evaluer", pk=promotion.pk)

    context = {
        "titre": _("Évaluer l'élève pour la promotion"),
        "promotion": promotion,
        "form": form,
        "notes": notes,
        "absences": absences,
    }
    return render(request, "promotion/evaluer.html", context)


@login_required
def promotion_valider_decision(request, pk):
    try:
        ecole = _get_user_ecole(request)
    except ValueError as e:
        messages.error(request, str(e))
        return redirect("home")

    promotion = get_object_or_404(
        PromotionEleve.objects.select_related(
            "eleve",
            "annee_scolaire",
            "classe_actuelle",
            "niveau_actuel",
            "prochaine_classe",
            "prochaine_specialite",
        ),
        pk=pk,
        ecole=ecole,
    )

    form = PromotionValidationForm(
            request.POST or None,
            instance=promotion,
            ecole=ecole,
            niveau_actuel=promotion.niveau_actuel,
        )

    if request.method == "POST" and form.is_valid():
        promotion_form = form.save(commit=False)

        promotion.decision_personnalisee = promotion_form.decision_personnalisee
        promotion.prochaine_classe = promotion_form.prochaine_classe
        promotion.prochaine_specialite = promotion_form.prochaine_specialite
        promotion.commentaire = promotion_form.commentaire

        promotion.valider_decision(
            user=request.user,
            decision=promotion_form.decision_finale,
            commentaire=promotion_form.commentaire,
        )

        messages.success(request, _("La décision finale a été validée avec succès."))
        return redirect("promotion:promotion_liste_attente")

    context = {
        "titre": _("Valider la décision finale"),
        "promotion": promotion,
        "form": form,
    }
    return render(request, "promotion/valider_decision.html", context)


@login_required
def promotion_executer(request, pk):
    if request.method != "POST":
        return redirect("promotion:promotion_liste_attente")

    try:
        ecole = _get_user_ecole(request)
    except ValueError as e:
        messages.error(request, str(e))
        return redirect("home")

    promotion = get_object_or_404(
        PromotionEleve,
        pk=pk,
        ecole=ecole,
    )

    if promotion.etat != PromotionEtat.VALIDE:
        messages.error(
            request,
            _("Impossible d'exécuter cette promotion tant que la décision finale n'est pas validée.")
        )
        return redirect("promotion:promotion_valider_decision", pk=promotion.pk)

    try:
        with transaction.atomic():
            promotion.executer_promotion(user=request.user)

        messages.success(request, _("La promotion a été exécutée avec succès."))
    except Exception as e:
        messages.error(
            request,
            _("Erreur lors de l'exécution : %(error)s") % {"error": str(e)}
        )

    return redirect("promotion:promotion_liste_attente")










@login_required
def promotion_afficher_decision_finale(request, pk):
    try:
        ecole = _get_user_ecole(request)
    except ValueError as e:
        messages.error(request, str(e))
        return redirect("home")

    promotion = get_object_or_404(
        PromotionEleve.objects.select_related(
            "eleve",
            "annee_scolaire",
            "niveau_actuel",
            "classe_actuelle",
            "prochaine_niveau",
            "prochaine_classe",
            "prochaine_specialite",
            "valide_par",
            "execute_par",
            "decision_personnalisee",
        ),
        pk=pk,
        ecole=ecole,
    )

    context = {
        "titre": _("Afficher la décision finale"),
        "promotion": promotion,
    }
    return render(request, "promotion/afficher_decision_finale.html", context)


@login_required
def promotion_liste_decisions_finales(request):
    try:
        ecole = _get_user_ecole(request)
        annee_active = _get_active_annee()
    except ValueError as e:
        messages.error(request, str(e))
        return redirect("home")

    selected_annee_id = request.GET.get("annee_scolaire")
    if selected_annee_id:
        annee_scolaire = AnneeScolaire.objects.filter(pk=selected_annee_id).first()
    else:
        annee_scolaire = None

    if annee_scolaire:
        _sync_promotions(ecole, annee_scolaire)
    else:
        _sync_promotions(ecole, annee_active)

    initial = {}
    if not request.GET:
        initial["annee_scolaire"] = annee_active

    form = PromotionListeFilterForm(
        request.GET or None,
        ecole=ecole,
        initial=initial
    )

    qs = PromotionEleve.objects.filter(
        ecole=ecole,
        etat__in=[PromotionEtat.VALIDE, PromotionEtat.EXECUTE]
    ).exclude(
        decision_finale__in=["", "attente"]
    ).select_related(
        "eleve",
        "annee_scolaire",
        "niveau_actuel",
        "classe_actuelle",
        "prochaine_niveau",
        "prochaine_classe",
        "prochaine_specialite",
        "valide_par",
        "execute_par",
        "decision_personnalisee",
    ).order_by(
        "annee_scolaire__debut",
        "niveau_actuel__ordre",
        "classe_actuelle__nom",
        "eleve__nom"
    )

    if form.is_valid():
        q = form.cleaned_data.get("q")
        annee = form.cleaned_data.get("annee_scolaire")
        niveau = form.cleaned_data.get("niveau")
        classe = form.cleaned_data.get("classe")
        decision = form.cleaned_data.get("decision")
        etat = form.cleaned_data.get("etat")

        if annee:
            qs = qs.filter(annee_scolaire=annee)

        if q:
            qs = qs.filter(
                Q(eleve__nom__icontains=q) |
                Q(eleve__identifiant__icontains=q)
            )

        if niveau:
            qs = qs.filter(niveau_actuel=niveau)

        if classe:
            qs = qs.filter(classe_actuelle=classe)

        if decision:
            qs = qs.filter(decision_finale=decision)

        if etat:
            qs = qs.filter(etat=etat)

    context = {
        "titre": _("Afficher la décision finale"),
        "form": form,
        "promotions": qs,
        "total": qs.count(),
        "annee_scolaire_selectionnee": form.cleaned_data.get("annee_scolaire") if form.is_valid() else None,
    }
    return render(request, "promotion/liste_decisions_finales.html", context)


@login_required
def promotion_liste_evaluation(request):
    try:
        ecole = _get_user_ecole(request)
        annee_active = _get_active_annee()
    except ValueError as e:
        messages.error(request, str(e))
        return redirect("home")

    selected_annee_id = request.GET.get("annee_scolaire")
    if selected_annee_id:
        annee_scolaire = AnneeScolaire.objects.filter(pk=selected_annee_id).first()
    else:
        annee_scolaire = None

    if annee_scolaire:
        _sync_promotions(ecole, annee_scolaire)
    else:
        _sync_promotions(ecole, annee_active)

    initial = {}
    if not request.GET:
        initial["annee_scolaire"] = annee_active

    form = PromotionListeFilterForm(
        request.GET or None,
        ecole=ecole,
        initial=initial
    )

    qs = PromotionEleve.objects.filter(
        ecole=ecole,
    ).select_related(
        "eleve",
        "annee_scolaire",
        "niveau_actuel",
        "classe_actuelle",
        "prochaine_classe",
        "prochaine_specialite",
    ).order_by(
        "annee_scolaire__debut",
        "niveau_actuel__ordre",
        "classe_actuelle__nom",
        "eleve__nom"
    )

    if form.is_valid():
        q = form.cleaned_data.get("q")
        annee = form.cleaned_data.get("annee_scolaire")
        niveau = form.cleaned_data.get("niveau")
        classe = form.cleaned_data.get("classe")
        decision = form.cleaned_data.get("decision")
        etat = form.cleaned_data.get("etat")

        if annee:
            qs = qs.filter(annee_scolaire=annee)

        if q:
            qs = qs.filter(
                Q(eleve__nom__icontains=q) |
                Q(eleve__identifiant__icontains=q)
            )

        if niveau:
            qs = qs.filter(niveau_actuel=niveau)

        if classe:
            qs = qs.filter(classe_actuelle=classe)

        if decision:
            qs = qs.filter(
                Q(decision_proposee=decision) |
                Q(decision_finale=decision)
            )

        if etat:
            qs = qs.filter(etat=etat)

    context = {
        "titre": _("Évaluer l'élève pour la promotion"),
        "form": form,
        "promotions": qs,
        "total": qs.count(),
        "annee_scolaire_selectionnee": form.cleaned_data.get("annee_scolaire") if form.is_valid() else None,
    }
    return render(request, "promotion/liste_evaluation.html", context)


from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView

from Ecole_admin.models import PromotionEleve, Niveau, AnneeScolaire


class EleveDiplomeListView(LoginRequiredMixin, ListView):
    model = PromotionEleve
    template_name = "promotion/eleve_diplome_list.html"
    context_object_name = "promotions"
    paginate_by = 20

    def get_queryset(self):
        user = self.request.user
        niveau_id = self.request.GET.get("niveau")
        annee_id = self.request.GET.get("annee_scolaire")

        qs = (
            PromotionEleve.objects
            .select_related(
                "eleve",
                "niveau_actuel",
                "classe_actuelle",
                "prochaine_classe",
                "annee_scolaire",
                "decision_personnalisee",
            )
            .filter(
                ecole=user.ecole,
                est_diplome=True,
                est_traite=True,
            )
            .order_by("classe_actuelle__nom", "eleve__nom")
        )

        if niveau_id:
            qs = qs.filter(niveau_actuel_id=niveau_id)

        if annee_id:
            qs = qs.filter(annee_scolaire_id=annee_id)

        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        context["niveaux"] = Niveau.objects.filter(
            ecole=user.ecole,
            actif=True
        ).order_by("ordre", "nom")

        context["annees_scolaires"] = AnneeScolaire.objects.all().order_by("-debut")
        context["selected_niveau"] = self.request.GET.get("niveau", "")
        context["selected_annee"] = self.request.GET.get("annee_scolaire", "")

        return context




from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.db.models import Q
from django.shortcuts import redirect, render
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.views import View

from Ecole_admin.models import PromotionEleve

try:
    from Ecole_admin.models import PromotionEtat
except Exception:
    PromotionEtat = None


class PromouvoirElevesEnAttenteView(LoginRequiredMixin, View):
    template_name = "promotion/promouvoir_eleves_attente.html"

    def get_queryset(self):
        return (
            PromotionEleve.objects
            .select_related(
                "eleve",
                "classe_actuelle",
                "prochaine_classe",
                "decision_personnalisee",
            )
            .filter(
                ecole=self.request.user.ecole,
                est_traite=False,
            )
            .filter(
                Q(est_diplome=True) | Q(prochaine_classe__isnull=False)
            )
            .order_by("classe_actuelle__nom", "eleve__nom")
        )

    def get(self, request, *args, **kwargs):
        context = {
            "promotions": self.get_queryset(),
        }
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        ids = request.POST.getlist("promotion_ids")

        if not ids:
            messages.warning(request, _("Sélectionnez au moins un élève."))
            return redirect("promouvoir_eleves_attente")

        promotions = self.get_queryset().filter(id__in=ids)

        executees = 0
        ignorees = 0
        maintenant = timezone.now()

        with transaction.atomic():
            for promotion in promotions:
                # Cas 1, élève diplômé
                if promotion.est_diplome:
                    pass

                # Cas 2, élève à promouvoir vers une classe suivante
                elif promotion.prochaine_classe_id:
                    eleve = promotion.eleve
                    eleve.classe = promotion.prochaine_classe
                    eleve.save(update_fields=["classe"])

                # Cas 3, impossible à exécuter
                else:
                    ignorees += 1
                    continue

                promotion.est_traite = True
                promotion.execute_par = request.user
                promotion.date_execution = maintenant

                update_fields = [
                    "est_traite",
                    "execute_par",
                    "date_execution",
                ]

                # Mise à jour de l'état, seulement si l'enum existe bien
                if PromotionEtat:
                    if hasattr(PromotionEtat, "EXECUTEE"):
                        promotion.etat = PromotionEtat.EXECUTEE
                        update_fields.append("etat")
                    elif hasattr(PromotionEtat, "EXECUTEE"):
                        promotion.etat = PromotionEtat.EXECUTEE
                        update_fields.append("etat")
                    elif hasattr(PromotionEtat, "TRAITEE"):
                        promotion.etat = PromotionEtat.TRAITEE
                        update_fields.append("etat")

                promotion.save(update_fields=update_fields)
                executees += 1

        if executees:
            messages.success(
                request,
                _("Les promotions sélectionnées ont été exécutées avec succès.")
            )

        if ignorees:
            messages.warning(
                request,
                _("Certaines promotions n'ont pas été exécutées, car la prochaine classe est absente.")
            )

        return redirect("promotion:promouvoir_eleves_attente")
    


    from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.views.generic import ListView

from Ecole_admin.models import PromotionEleve, Niveau, Classe, AnneeScolaire


class VoirElevesEnPromotionListView(LoginRequiredMixin, ListView):
    model = PromotionEleve
    template_name = "promotion/voir_eleves_promotion.html"
    context_object_name = "promotions"
    paginate_by = 20

    def get_queryset(self):
        user = self.request.user

        qs = (
            PromotionEleve.objects
            .select_related(
                "eleve",
                "niveau_actuel",
                "classe_actuelle",
                "prochaine_classe",
                "annee_scolaire",
                "decision_personnalisee",
                "evalue_par",
                "valide_par",
                "execute_par",
            )
            .filter(ecole=user.ecole)
            .order_by("-updated_at", "classe_actuelle__nom", "eleve__nom")
        )

        q = self.request.GET.get("q")
        niveau_id = self.request.GET.get("niveau")
        classe_id = self.request.GET.get("classe")
        annee_id = self.request.GET.get("annee_scolaire")
        etat = self.request.GET.get("etat")

        if q:
            qs = qs.filter(
                Q(eleve__nom__icontains=q) |
                Q(eleve__identifiant__icontains=q)
            )

        if niveau_id:
            qs = qs.filter(niveau_actuel_id=niveau_id)

        if classe_id:
            qs = qs.filter(classe_actuelle_id=classe_id)

        if annee_id:
            qs = qs.filter(annee_scolaire_id=annee_id)

        if etat:
            qs = qs.filter(etat=etat)

        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        context["niveaux"] = Niveau.objects.filter(
            ecole=user.ecole,
            actif=True
        ).order_by("ordre", "nom")

        context["classes"] = Classe.objects.filter(
            ecole=user.ecole,
            actif=True
        ).select_related("niveau").order_by("niveau__ordre", "nom")

        context["annees_scolaires"] = AnneeScolaire.objects.all().order_by("-debut")

        context["etat_choices"] = PromotionEleve._meta.get_field("etat").choices

        context["selected_q"] = self.request.GET.get("q", "")
        context["selected_niveau"] = self.request.GET.get("niveau", "")
        context["selected_classe"] = self.request.GET.get("classe", "")
        context["selected_annee"] = self.request.GET.get("annee_scolaire", "")
        context["selected_etat"] = self.request.GET.get("etat", "")

        return context
    





from datetime import datetime, time
from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.shortcuts import render
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.views import View

from Ecole_admin.models import AnneeScolaire, Classe, Eleve, Niveau, PromotionEleve


def get_annee_suivante(annee_source):
    if not annee_source:
        return None
    return (
        AnneeScolaire.objects
        .filter(debut__gt=annee_source.debut)
        .order_by("debut")
        .first()
    )


def get_niveau_suivant(ecole, niveau_source):
    if not niveau_source:
        return None
    return (
        Niveau.objects
        .filter(ecole=ecole, actif=True, ordre__gt=niveau_source.ordre)
        .order_by("ordre", "nom")
        .first()
    )


def get_classe_cible_par_defaut(ecole, classe_source, niveau_cible):
    if not niveau_cible:
        return None

    qs = Classe.objects.filter(
        ecole=ecole,
        actif=True,
        niveau=niveau_cible
    ).order_by("nom")

    if classe_source and getattr(classe_source, "specialite_id", None):
        match = qs.filter(specialite_id=classe_source.specialite_id).first()
        if match:
            return match

    return qs.first()


class PromotionsParClasseView(LoginRequiredMixin, View):
    template_name = "promotion/promotions_par_classe.html"

    def _request_data(self, request):
        return request.GET if request.method == "GET" else request.POST

    def _build_context(self, request):
        user = request.user
        data = self._request_data(request)

        annee_source_id = data.get("annee_source")
        niveau_source_id = data.get("niveau_source")
        classe_source_id = data.get("classe_source")

        annee_cible_id = data.get("annee_cible")
        niveau_cible_id = data.get("niveau_cible")
        classe_cible_id = data.get("classe_cible")

        annee_source = None
        niveau_source = None
        classe_source = None

        if annee_source_id:
            annee_source = AnneeScolaire.objects.filter(id=annee_source_id).first()

        if niveau_source_id:
            niveau_source = Niveau.objects.filter(
                id=niveau_source_id,
                ecole=user.ecole,
                actif=True
            ).first()

        if classe_source_id:
            classe_source = Classe.objects.filter(
                id=classe_source_id,
                ecole=user.ecole,
                actif=True
            ).select_related("niveau", "specialite").first()

        annees = AnneeScolaire.objects.all().order_by("-debut")
        niveaux = Niveau.objects.filter(
            ecole=user.ecole,
            actif=True
        ).order_by("ordre", "nom")

        classes_source = Classe.objects.filter(
            ecole=user.ecole,
            actif=True
        ).select_related("niveau").order_by("niveau__ordre", "nom")

        if niveau_source:
            classes_source = classes_source.filter(niveau=niveau_source)
        else:
            classes_source = classes_source.none()

        # destination automatique
        annee_cible_auto = get_annee_suivante(annee_source)
        niveau_cible_auto = get_niveau_suivant(user.ecole, niveau_source)

        annees_cibles = AnneeScolaire.objects.none()
        niveaux_cibles = Niveau.objects.none()
        classes_cibles = Classe.objects.none()

        if annee_cible_auto:
            annees_cibles = AnneeScolaire.objects.filter(id=annee_cible_auto.id)

        if niveau_cible_auto:
            niveaux_cibles = Niveau.objects.filter(id=niveau_cible_auto.id)

        annee_cible = None
        niveau_cible = None
        classe_cible = None

        if annee_cible_id:
            annee_cible = annees_cibles.filter(id=annee_cible_id).first()
        else:
            annee_cible = annee_cible_auto

        if niveau_cible_id:
            niveau_cible = niveaux_cibles.filter(id=niveau_cible_id).first()
        else:
            niveau_cible = niveau_cible_auto

        if niveau_cible:
            classes_cibles = Classe.objects.filter(
                ecole=user.ecole,
                actif=True,
                niveau=niveau_cible
            ).select_related("niveau", "specialite").order_by("nom")

        if classe_cible_id:
            classe_cible = classes_cibles.filter(id=classe_cible_id).first()
        elif classe_source and niveau_cible:
            classe_cible = get_classe_cible_par_defaut(user.ecole, classe_source, niveau_cible)

        rows = []

        if annee_source and classe_source:
            promotions = PromotionEleve.objects.filter(
                ecole=user.ecole,
                annee_scolaire=annee_source,
                classe_actuelle=classe_source
            ).select_related(
                "eleve",
                "decision_personnalisee",
                "prochaine_classe"
            )

            promo_map = {p.eleve_id: p for p in promotions}

            eleves = Eleve.objects.filter(
                ecole=user.ecole,
                annee_scolaire=annee_source,
                classe=classe_source
            ).order_by("nom")

            for eleve in eleves:
                promo = promo_map.get(eleve.id)

                moyenne = "-"
                decision = "-"
                statut = _("En attente")
                status_code = "waiting"

                if promo:
                    if promo.moyenne_annuelle is not None:
                        moyenne = promo.moyenne_annuelle

                    if promo.decision_personnalisee_id:
                        decision = promo.decision_personnalisee.decision
                    else:
                        decision = promo.get_decision_finale_display()

                    if promo.est_traite:
                        statut = _("Déjà traité")
                        status_code = "done"
                    elif promo.est_diplome:
                        statut = _("Diplômé")
                        status_code = "diploma"
                    elif promo.prochaine_classe_id or promo.decision_personnalisee_id:
                        statut = _("Prêt")
                        status_code = "ready"

                rows.append({
                    "eleve": eleve,
                    "promotion": promo,
                    "moyenne": moyenne,
                    "decision": decision,
                    "statut": statut,
                    "status_code": status_code,
                })

        return {
            "annees": annees,
            "niveaux": niveaux,
            "classes_source": classes_source,

            "annees_cibles": annees_cibles,
            "niveaux_cibles": niveaux_cibles,
            "classes_cibles": classes_cibles,

            "annee_source": annee_source,
            "niveau_source": niveau_source,
            "classe_source": classe_source,

            "annee_cible": annee_cible,
            "niveau_cible": niveau_cible,
            "classe_cible": classe_cible,

            "rows": rows,
            "selected_date_execution": data.get("date_execution") or timezone.localdate().isoformat(),
            "force_checked": bool(data.get("force")),
        }

    def get(self, request, *args, **kwargs):
        context = self._build_context(request)
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        context = self._build_context(request)

        annee_source = context["annee_source"]
        niveau_source = context["niveau_source"]
        classe_source = context["classe_source"]

        annee_cible = context["annee_cible"]
        niveau_cible = context["niveau_cible"]
        classe_cible = context["classe_cible"]

        force = bool(request.POST.get("force"))
        student_ids = request.POST.getlist("student_ids")
        date_execution_str = request.POST.get("date_execution")

        if not annee_source or not niveau_source or not classe_source:
            messages.warning(request, _("Veuillez sélectionner l'année, le niveau et la classe source."))
            return render(request, self.template_name, context)

        if not annee_cible or not classe_cible:
            messages.warning(request, _("Veuillez sélectionner l'année cible et la classe cible."))
            return render(request, self.template_name, context)

        if not student_ids:
            messages.warning(request, _("Veuillez sélectionner au moins un élève."))
            return render(request, self.template_name, context)

        execution_dt = timezone.now()
        if date_execution_str:
            try:
                d = datetime.strptime(date_execution_str, "%Y-%m-%d").date()
                execution_dt = timezone.make_aware(datetime.combine(d, time(12, 0)))
            except ValueError:
                pass

        eleves = Eleve.objects.filter(
            id__in=student_ids,
            ecole=request.user.ecole,
            annee_scolaire=annee_source,
            classe=classe_source
        ).select_related("classe", "annee_scolaire")

        total_ok = 0
        total_skip = 0

        with transaction.atomic():
            for eleve in eleves:
                promo, _created = PromotionEleve.objects.get_or_create(
                    ecole=request.user.ecole,
                    annee_scolaire=annee_source,
                    eleve=eleve,
                    defaults={
                        "niveau_actuel": niveau_source,
                        "classe_actuelle": classe_source,
                    }
                )

                if promo.est_traite and not force:
                    total_skip += 1
                    continue

                # on garde la source
                promo.niveau_actuel = niveau_source
                promo.classe_actuelle = classe_source

                # destination commune choisie
                promo.prochaine_niveau = classe_cible.niveau
                promo.prochaine_classe = classe_cible

                if getattr(classe_cible, "specialite_id", None):
                    promo.prochaine_specialite = classe_cible.specialite
                else:
                    promo.prochaine_specialite = None

                # si pas force, on respecte au moins les cas prêts
                if not force:
                    pret = (
                        promo.est_diplome
                        or bool(promo.prochaine_classe_id)
                        or bool(promo.decision_personnalisee_id)
                    )
                    if not pret and promo.decision_finale == promo.decision_proposee:
                        pass

                # déplacement réel de l'élève
                eleve.classe = classe_cible
                eleve.annee_scolaire = annee_cible
                eleve.save(update_fields=["classe", "annee_scolaire"])

                promo.est_traite = True
                promo.execute_par = request.user
                promo.date_execution = execution_dt
                promo.est_diplome = False

                # on garde un état texte simple si enum absent
                try:
                    from .models import PromotionEtat
                    if hasattr(PromotionEtat, "EXECUTEE"):
                        promo.etat = PromotionEtat.EXECUTEE
                except Exception:
                    promo.etat = "executee"

                promo.save()
                total_ok += 1

        if total_ok:
            messages.success(
                request,
                _("La promotion par classe a été exécutée avec succès pour les élèves sélectionnés.")
            )

        if total_skip:
            messages.warning(
                request,
                _("Certains élèves ont été ignorés, car ils étaient déjà traités.")
            )

        context = self._build_context(request)
        return render(request, self.template_name, context)
    






from datetime import datetime, time

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.shortcuts import render
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.views import View

from Ecole_admin.models import AnneeScolaire, Classe, Eleve, Niveau, PromotionEleve

try:
    from Ecole_admin.models import PromotionEtat
except Exception:
    PromotionEtat = None


def get_annee_suivante(annee_source):
    if not annee_source:
        return None
    return (
        AnneeScolaire.objects
        .filter(debut__gt=annee_source.debut)
        .order_by("debut")
        .first()
    )


def get_niveau_suivant(ecole, niveau_source):
    if not niveau_source:
        return None
    return (
        Niveau.objects
        .filter(ecole=ecole, actif=True, ordre__gt=niveau_source.ordre)
        .order_by("ordre", "nom")
        .first()
    )


def get_classe_cible_depuis_niveau(ecole, classe_source, niveau_cible):
    if not niveau_cible:
        return None

    qs = Classe.objects.filter(
        ecole=ecole,
        actif=True,
        niveau=niveau_cible
    ).order_by("nom")

    if classe_source and getattr(classe_source, "specialite_id", None):
        same_specialite = qs.filter(specialite_id=classe_source.specialite_id).first()
        if same_specialite:
            return same_specialite

    return qs.first()


class PromotionsParNiveauxView(LoginRequiredMixin, View):
    template_name = "promotion/promotions_par_niveaux.html"

    def _request_data(self, request):
        return request.GET if request.method == "GET" else request.POST

    def _build_context(self, request):
        user = request.user
        data = self._request_data(request)

        annee_source_id = data.get("annee_source")
        niveau_source_id = data.get("niveau_source")
        annee_cible_id = data.get("annee_cible")
        niveau_cible_id = data.get("niveau_cible")
        q = (data.get("q") or "").strip()

        annee_source = None
        niveau_source = None

        if annee_source_id:
            annee_source = AnneeScolaire.objects.filter(id=annee_source_id).first()

        if niveau_source_id:
            niveau_source = Niveau.objects.filter(
                id=niveau_source_id,
                ecole=user.ecole,
                actif=True
            ).first()

        annees = AnneeScolaire.objects.all().order_by("-debut")
        niveaux = Niveau.objects.filter(
            ecole=user.ecole,
            actif=True
        ).order_by("ordre", "nom")

        annee_cible_auto = get_annee_suivante(annee_source)
        niveau_cible_auto = get_niveau_suivant(user.ecole, niveau_source)

        annees_cibles = AnneeScolaire.objects.none()
        niveaux_cibles = Niveau.objects.none()

        if annee_cible_auto:
            annees_cibles = AnneeScolaire.objects.filter(id=annee_cible_auto.id)

        if niveau_cible_auto:
            niveaux_cibles = Niveau.objects.filter(id=niveau_cible_auto.id)

        annee_cible = None
        niveau_cible = None

        if annee_cible_id:
            annee_cible = annees_cibles.filter(id=annee_cible_id).first()
        else:
            annee_cible = annee_cible_auto

        if niveau_cible_id:
            niveau_cible = niveaux_cibles.filter(id=niveau_cible_id).first()
        else:
            niveau_cible = niveau_cible_auto

        rows = []

        if annee_source and niveau_source:
            eleves = (
                Eleve.objects
                .filter(
                    ecole=user.ecole,
                    annee_scolaire=annee_source,
                    classe__niveau=niveau_source
                )
                .select_related("classe", "classe__niveau")
                .order_by("nom")
            )

            if q:
                eleves = eleves.filter(nom__icontains=q) | eleves.filter(identifiant__icontains=q)

            promotions = PromotionEleve.objects.filter(
                ecole=user.ecole,
                annee_scolaire=annee_source,
                niveau_actuel=niveau_source
            ).select_related(
                "eleve",
                "decision_personnalisee",
                "prochaine_classe",
                "prochaine_niveau"
            )

            promo_map = {p.eleve_id: p for p in promotions}

            for eleve in eleves:
                promo = promo_map.get(eleve.id)
                classe_cible_proposee = get_classe_cible_depuis_niveau(
                    user.ecole,
                    eleve.classe,
                    niveau_cible
                )

                moyenne = "-"
                decision = "-"
                statut = _("En attente")
                status_code = "waiting"

                if promo:
                    if promo.moyenne_annuelle is not None:
                        moyenne = promo.moyenne_annuelle

                    if promo.decision_personnalisee_id:
                        decision = promo.decision_personnalisee.decision
                    else:
                        decision = promo.get_decision_finale_display()

                    if promo.est_traite:
                        statut = _("Déjà traité")
                        status_code = "done"
                    elif promo.est_diplome:
                        statut = _("Diplômé")
                        status_code = "diploma"
                    elif promo.prochaine_niveau_id or promo.decision_personnalisee_id:
                        statut = _("Prêt")
                        status_code = "ready"

                rows.append({
                    "eleve": eleve,
                    "promotion": promo,
                    "moyenne": moyenne,
                    "decision": decision,
                    "statut": statut,
                    "status_code": status_code,
                    "classe_cible_proposee": classe_cible_proposee,
                })

        return {
            "annees": annees,
            "niveaux": niveaux,
            "annees_cibles": annees_cibles,
            "niveaux_cibles": niveaux_cibles,
            "annee_source": annee_source,
            "niveau_source": niveau_source,
            "annee_cible": annee_cible,
            "niveau_cible": niveau_cible,
            "rows": rows,
            "selected_date_execution": data.get("date_execution") or timezone.localdate().isoformat(),
            "force_checked": bool(data.get("force")),
            "selected_q": q,
        }

    def get(self, request, *args, **kwargs):
        context = self._build_context(request)
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        context = self._build_context(request)

        annee_source = context["annee_source"]
        niveau_source = context["niveau_source"]
        annee_cible = context["annee_cible"]
        niveau_cible = context["niveau_cible"]

        force = bool(request.POST.get("force"))
        student_ids = request.POST.getlist("student_ids")
        date_execution_str = request.POST.get("date_execution")

        if not annee_source or not niveau_source:
            messages.warning(request, _("Veuillez sélectionner l'année et le niveau source."))
            return render(request, self.template_name, context)

        if not student_ids:
            messages.warning(request, _("Veuillez sélectionner au moins un élève."))
            return render(request, self.template_name, context)

        execution_dt = timezone.now()
        if date_execution_str:
            try:
                d = datetime.strptime(date_execution_str, "%Y-%m-%d").date()
                execution_dt = timezone.make_aware(datetime.combine(d, time(12, 0)))
            except ValueError:
                pass

        eleves = (
            Eleve.objects
            .filter(
                id__in=student_ids,
                ecole=request.user.ecole,
                annee_scolaire=annee_source,
                classe__niveau=niveau_source
            )
            .select_related("classe", "classe__niveau")
        )

        total_ok = 0
        total_skip = 0
        total_diplomes = 0

        with transaction.atomic():
            for eleve in eleves:
                promo, _created = PromotionEleve.objects.get_or_create(
                    ecole=request.user.ecole,
                    annee_scolaire=annee_source,
                    eleve=eleve,
                    defaults={
                        "niveau_actuel": niveau_source,
                        "classe_actuelle": eleve.classe,
                    }
                )

                if promo.est_traite and not force:
                    total_skip += 1
                    continue

                promo.niveau_actuel = niveau_source
                promo.classe_actuelle = eleve.classe

                # Cas fin de cycle, aucun niveau suivant
                if not niveau_cible:
                    promo.prochaine_niveau = None
                    promo.prochaine_classe = None
                    promo.prochaine_specialite = None
                    promo.est_diplome = True
                    promo.est_traite = True
                    promo.execute_par = request.user
                    promo.date_execution = execution_dt

                    if PromotionEtat and hasattr(PromotionEtat, "EXECUTEE"):
                        promo.etat = PromotionEtat.EXECUTEE
                    else:
                        promo.etat = "executee"

                    promo.save()
                    total_ok += 1
                    total_diplomes += 1
                    continue

                if not annee_cible:
                    total_skip += 1
                    continue

                classe_cible = get_classe_cible_depuis_niveau(
                    request.user.ecole,
                    eleve.classe,
                    niveau_cible
                )

                if not classe_cible:
                    total_skip += 1
                    continue

                promo.prochaine_niveau = niveau_cible
                promo.prochaine_classe = classe_cible

                if getattr(classe_cible, "specialite_id", None):
                    promo.prochaine_specialite = classe_cible.specialite
                else:
                    promo.prochaine_specialite = None

                eleve.classe = classe_cible
                eleve.annee_scolaire = annee_cible
                eleve.save(update_fields=["classe", "annee_scolaire"])

                promo.est_diplome = False
                promo.est_traite = True
                promo.execute_par = request.user
                promo.date_execution = execution_dt

                if PromotionEtat and hasattr(PromotionEtat, "EXECUTEE"):
                    promo.etat = PromotionEtat.EXECUTEE
                else:
                    promo.etat = "executee"

                promo.save()
                total_ok += 1

        if total_ok:
            if total_diplomes and total_diplomes == total_ok:
                messages.success(
                    request,
                    _("Les élèves sélectionnés ont été marqués diplômés avec succès.")
                )
            else:
                messages.success(
                    request,
                    _("La promotion par niveau a été exécutée avec succès pour les élèves sélectionnés.")
                )

        if total_skip:
            messages.warning(
                request,
                _("Certains élèves n'ont pas été traités, car la destination était incomplète ou le dossier était déjà traité.")
            )

        context = self._build_context(request)
        return render(request, self.template_name, context)




from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.shortcuts import redirect, render
from django.utils.translation import gettext_lazy as _
from django.views import View

from Ecole_admin.models import AnneeScolaire, Classe, Eleve, Niveau


class ChangementClasseEleveView(LoginRequiredMixin, View):
    template_name = "promotion/changement_classe_eleve.html"

    def _annee_active(self):
        return (
            AnneeScolaire.objects
            .filter(est_active=True)
            .order_by("-debut")
            .first()
            or AnneeScolaire.objects.order_by("-debut").first()
        )

    def _selected_ids(self, request):
        raw = ""
        if request.method == "POST":
            raw = request.POST.get("selected_ids", "")
        else:
            raw = request.GET.get("selected_ids", "")

        ids = []
        for val in raw.split(","):
            val = val.strip()
            if val.isdigit():
                ids.append(int(val))
        return ids

    def _get_context(self, request):
        user = request.user
        annee_active = self._annee_active()

        data = request.POST if request.method == "POST" else request.GET

        niveau_id = data.get("niveau")
        classe_source_id = data.get("classe_source")
        classe_cible_id = data.get("classe_cible")

        niveaux = Niveau.objects.filter(
            ecole=user.ecole,
            actif=True
        ).order_by("ordre", "nom")

        niveau = None
        if niveau_id:
            niveau = niveaux.filter(id=niveau_id).first()

        classes = Classe.objects.filter(
            ecole=user.ecole,
            actif=True
        ).select_related("niveau").order_by("niveau__ordre", "nom")

        if niveau:
            classes = classes.filter(niveau=niveau)
        else:
            classes = classes.none()

        classe_source = classes.filter(id=classe_source_id).first() if classe_source_id else None
        classe_cible = classes.filter(id=classe_cible_id).first() if classe_cible_id else None

        selected_ids = self._selected_ids(request)

        eleves_source = Eleve.objects.none()
        if annee_active and classe_source:
            eleves_source = (
                Eleve.objects
                .filter(
                    ecole=user.ecole,
                    annee_scolaire=annee_active,
                    classe=classe_source
                )
                .order_by("nom")
            )

        selected_students = eleves_source.filter(id__in=selected_ids)
        available_students = eleves_source.exclude(id__in=selected_ids)

        return {
            "annee_active": annee_active,
            "niveaux": niveaux,
            "classes": classes,
            "niveau": niveau,
            "classe_source": classe_source,
            "classe_cible": classe_cible,
            "available_students": available_students,
            "selected_students": selected_students,
            "selected_ids_csv": ",".join(str(i) for i in selected_ids),
        }

    def get(self, request, *args, **kwargs):
        context = self._get_context(request)
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        context = self._get_context(request)

        annee_active = context["annee_active"]
        niveau = context["niveau"]
        classe_source = context["classe_source"]
        classe_cible = context["classe_cible"]

        selected_ids = self._selected_ids(request)

        if not niveau or not classe_source or not classe_cible:
            messages.warning(
                request,
                _("Veuillez sélectionner le niveau, la classe source et la classe cible.")
            )
            return render(request, self.template_name, context)

        if classe_source == classe_cible:
            messages.warning(
                request,
                _("La classe cible doit être différente de la classe source.")
            )
            return render(request, self.template_name, context)

        if not selected_ids:
            messages.warning(
                request,
                _("Veuillez sélectionner au moins un élève.")
            )
            return render(request, self.template_name, context)

        eleves = Eleve.objects.filter(
            ecole=request.user.ecole,
            annee_scolaire=annee_active,
            classe=classe_source,
            id__in=selected_ids
        )

        total = eleves.count()

        if total == 0:
            messages.warning(
                request,
                _("Aucun élève valide à transférer.")
            )
            return render(request, self.template_name, context)

        with transaction.atomic():
            eleves.update(classe=classe_cible)

        messages.success(
            request,
            _("Le changement de classe a été effectué avec succès.")
        )

        return redirect(
            f"{request.path}?niveau={niveau.id}&classe_source={classe_source.id}&classe_cible={classe_cible.id}"
        )
    

from collections import defaultdict
from decimal import Decimal, ROUND_HALF_UP

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views import View

from Ecole_admin.models import (
    AppreciationPeriode,
    Absence,
    AnneeScolaire,
    Classe,
    DecisionPromotion,
    Eleve,
    Niveau,
    Note,
    PeriodeScolaire,
    PromotionDecisionCode,
    PromotionEleve,
    PromotionEtat,
)


def normalize_note_sur_20(note_obj):
    note_brute = Decimal(str(note_obj.note))
    points_devoir = Decimal("20")

    if note_obj.devoir_id and getattr(note_obj.devoir, "points", None):
        points_devoir = Decimal(str(note_obj.devoir.points))

    if points_devoir > 0 and points_devoir != Decimal("20"):
        note_sur_20 = (note_brute * Decimal("20")) / points_devoir
    else:
        note_sur_20 = note_brute

    if note_sur_20 > Decimal("20"):
        note_sur_20 = Decimal("20")

    return note_sur_20.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def moyenne_decimal(values):
    values = [Decimal(str(v)) for v in values if v is not None]
    if not values:
        return Decimal("0.00")
    total = sum(values, Decimal("0.00"))
    return (total / Decimal(str(len(values)))).quantize(
        Decimal("0.01"),
        rounding=ROUND_HALF_UP
    )


def map_decision_promotion_to_code(decision_label: str) -> str:
    if not decision_label:
        return PromotionDecisionCode.ATTENTE

    text = decision_label.strip().lower()

    if "redou" in text:
        return PromotionDecisionCode.REDOUBLE
    if "autor" in text:
        return PromotionDecisionCode.AUTORISE
    if "orient" in text:
        return PromotionDecisionCode.ORIENTE
    if "dipl" in text:
        return PromotionDecisionCode.DIPLOME
    if "exclu" in text:
        return PromotionDecisionCode.EXCLU
    if "admis" in text or "admi" in text:
        return PromotionDecisionCode.ADMIS

    return PromotionDecisionCode.ATTENTE


class AfficherDecisionFinaleView(LoginRequiredMixin, View):
    template_name = "promotion/afficher_decision_finale.html"

    def _build_context(self, request):
        user = request.user
        data = request.GET if request.method == "GET" else request.POST

        annee_id = data.get("annee_scolaire")
        periode_id = data.get("periode")
        niveau_id = data.get("niveau")
        classe_id = data.get("classe")
        eleve_id = data.get("eleve")

        annees = AnneeScolaire.objects.all().order_by("-debut")

        periodes = PeriodeScolaire.objects.filter(
            ecole=user.ecole
        ).order_by("debut")
        if annee_id:
            periodes = periodes.filter(annee_scolaire_id=annee_id)
        else:
            periodes = periodes.none()

        niveaux = Niveau.objects.filter(
            ecole=user.ecole,
            actif=True
        ).order_by("ordre", "nom")

        classes = Classe.objects.filter(
            ecole=user.ecole,
            actif=True
        ).select_related("niveau").order_by("niveau__ordre", "ordre", "nom")
        if niveau_id:
            classes = classes.filter(niveau_id=niveau_id)
        else:
            classes = classes.none()

        eleves = Eleve.objects.filter(
            ecole=user.ecole
        ).select_related("classe", "annee_scolaire").order_by("nom")

        if annee_id:
            eleves = eleves.filter(annee_scolaire_id=annee_id)
        else:
            eleves = eleves.none()

        if classe_id:
            eleves = eleves.filter(classe_id=classe_id)
        else:
            eleves = eleves.none()

        decisions = DecisionPromotion.objects.filter(
            ecole=user.ecole,
            actif=True
        ).order_by("decision")
        if annee_id:
            decisions = decisions.filter(annee_scolaire_id=annee_id)
        else:
            decisions = decisions.none()

        fiche = None

        if annee_id and periode_id and niveau_id and classe_id and eleve_id:
            eleve = eleves.filter(id=eleve_id).first()
            periode = periodes.filter(id=periode_id).first()
            annee = next((a for a in annees if str(a.id) == str(annee_id)), None)

            if eleve and periode and annee:
                promotion = (
                    PromotionEleve.objects
                    .filter(
                        ecole=user.ecole,
                        annee_scolaire_id=annee_id,
                        eleve_id=eleve.id,
                    )
                    .select_related(
                        "classe_actuelle",
                        "niveau_actuel",
                        "prochaine_classe",
                        "prochaine_niveau",
                        "decision_personnalisee",
                    )
                    .first()
                )

                notes_qs = (
                    Note.objects
                    .filter(
                        eleve=eleve,
                        annee_scolaire=annee,
                        ecole=user.ecole,
                        devoir__periode=periode,
                    )
                    .select_related("matiere", "devoir", "devoir__professeur")
                    .order_by("matiere__nom", "id")
                )

                notes_by_matiere = defaultdict(list)
                for n in notes_qs:
                    notes_by_matiere[n.matiere_id].append(n)

                subject_rows = []

                for _matiere_id, notes_list in notes_by_matiere.items():
                    first_note = notes_list[0]
                    matiere = first_note.matiere

                    enseignant = "-"
                    if first_note.devoir_id and first_note.devoir.professeur_id:
                        enseignant = first_note.devoir.professeur.nom_conplet

                    eleve_scores = [normalize_note_sur_20(n) for n in notes_list]
                    eleve_avg = moyenne_decimal(eleve_scores)

                    class_notes = (
                        Note.objects
                        .filter(
                            annee_scolaire=annee,
                            ecole=user.ecole,
                            eleve__classe_id=classe_id,
                            matiere_id=matiere.id,
                            devoir__periode=periode,
                        )
                        .select_related("devoir")
                    )

                    by_student = defaultdict(list)
                    for cn in class_notes:
                        by_student[cn.eleve_id].append(normalize_note_sur_20(cn))

                    class_student_avgs = {
                        sid: moyenne_decimal(vals)
                        for sid, vals in by_student.items()
                    }

                    class_avg = moyenne_decimal(list(class_student_avgs.values()))

                    rank = "-"
                    if eleve.id in class_student_avgs:
                        current = class_student_avgs[eleve.id]
                        rank = 1 + sum(
                            1 for _sid, avg in class_student_avgs.items()
                            if avg > current
                        )

                    appreciation = "-"
                    app = AppreciationPeriode.objects.filter(
                        ecole=user.ecole,
                        annee_scolaire=annee,
                        actif=True,
                        note_min__lte=eleve_avg,
                        note_max__gte=eleve_avg
                    ).order_by("note_min").first()

                    if app:
                        appreciation = app.nom

                    subject_rows.append({
                        "matiere": matiere.nom,
                        "enseignant": enseignant,
                        "nb_note": len(notes_list),
                        "rang": rank,
                        "moyenne_eleve": eleve_avg,
                        "moyenne_classe": class_avg,
                        "appreciation": appreciation,
                    })

                moyenne_generale = Decimal("0.00")
                if promotion and promotion.moyenne_annuelle and promotion.moyenne_annuelle > 0:
                    moyenne_generale = promotion.moyenne_annuelle
                else:
                    moyenne_generale = moyenne_decimal([row["moyenne_eleve"] for row in subject_rows])

                absences_periode = Absence.objects.filter(
                    eleve=eleve,
                    annee_scolaire=annee,
                    ecole=user.ecole,
                    statut="absence",
                    date__gte=periode.debut,
                    date__lte=periode.fin,
                ).count()

                retards_periode = Absence.objects.filter(
                    eleve=eleve,
                    annee_scolaire=annee,
                    ecole=user.ecole,
                    statut="retard",
                    date__gte=periode.debut,
                    date__lte=periode.fin,
                ).count()

                fiche = {
                    "eleve": eleve,
                    "annee": annee,
                    "periode": periode,
                    "promotion": promotion,
                    "rows": subject_rows,
                    "moyenne_generale": moyenne_generale,
                    "absences_periode": absences_periode,
                    "retards_periode": retards_periode,
                }

        return {
            "annees": annees,
            "periodes": periodes,
            "niveaux": niveaux,
            "classes": classes,
            "eleves": eleves,
            "decisions": decisions,
            "fiche": fiche,
            "selected_annee": annee_id or "",
            "selected_periode": periode_id or "",
            "selected_niveau": niveau_id or "",
            "selected_classe": classe_id or "",
            "selected_eleve": eleve_id or "",
        }

    def get(self, request, *args, **kwargs):
        context = self._build_context(request)
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        context = self._build_context(request)

        annee_id = request.POST.get("annee_scolaire")
        niveau_id = request.POST.get("niveau")
        classe_id = request.POST.get("classe")
        periode_id = request.POST.get("periode")
        eleve_id = request.POST.get("eleve")
        decision_id = request.POST.get("decision_personnalisee")
        commentaire = (request.POST.get("commentaire") or "").strip()

        if not (annee_id and niveau_id and classe_id and periode_id and eleve_id):
            messages.warning(request, _("Veuillez sélectionner l'année, la période, le niveau, la classe et l'élève."))
            return render(request, self.template_name, context)

        decision_obj = DecisionPromotion.objects.filter(
            id=decision_id,
            ecole=request.user.ecole,
            actif=True
        ).first()

        if not decision_obj:
            messages.warning(request, _("Veuillez sélectionner une décision."))
            return render(request, self.template_name, context)

        eleve = Eleve.objects.filter(
            id=eleve_id,
            ecole=request.user.ecole
        ).select_related("classe").first()

        annee = AnneeScolaire.objects.filter(id=annee_id).first()

        if not eleve or not annee:
            messages.warning(request, _("Impossible de trouver l'élève ou l'année scolaire."))
            return render(request, self.template_name, context)

        promotion, _created = PromotionEleve.objects.get_or_create(
            ecole=request.user.ecole,
            annee_scolaire=annee,
            eleve=eleve,
            defaults={
                "niveau_actuel": eleve.classe.niveau if eleve.classe_id else None,
                "classe_actuelle": eleve.classe,
            }
        )

        promotion.niveau_actuel = eleve.classe.niveau if eleve.classe_id else promotion.niveau_actuel
        promotion.classe_actuelle = eleve.classe
        promotion.decision_personnalisee = decision_obj
        promotion.decision_finale = map_decision_promotion_to_code(decision_obj.decision)
        promotion.commentaire = commentaire
        promotion.valide_par = request.user
        promotion.date_validation = timezone.now()
        promotion.etat = PromotionEtat.VALIDE
        promotion.est_diplome = promotion.decision_finale == PromotionDecisionCode.DIPLOME
        promotion.save()

        messages.success(request, _("La décision finale a été enregistrée avec succès."))

        return redirect(
            f"{reverse('afficher_decision_finale')}"
            f"?annee_scolaire={annee_id}&periode={periode_id}&niveau={niveau_id}&classe={classe_id}&eleve={eleve_id}"
        )
    



