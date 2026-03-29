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