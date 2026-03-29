from decimal import Decimal

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count, Sum, F, Q, DecimalField, ExpressionWrapper
from django.db.models.functions import Coalesce
from django.shortcuts import get_object_or_404
from django.views.generic import TemplateView
from django.utils.translation import gettext_lazy as _

from Ecole_admin.models import (
    AnneeScolaire,
    Niveau,
    Classe,
    Eleve,
    Matier,
    Proffeseur,
    Note,
    Absence,
    ProfesseurAbsence,
    Paiment,
    FraisEleve,
    PaiementFraisEleve,
    RecuCaisse,
    ConvocationParent,
    Violence,
    Degradation,
    Employe,
    EmployeAbsence,
    EmploiDuTemps,
    Ressource,
    Batiment,
    Salle,
    Devoir,
    DispenseMatiere,
    PeriodeScolaire,
)


class ReportBaseMixin(LoginRequiredMixin):
    template_name = "rapports/base_report.html"
    report_title = "Rapport"
    report_subtitle = ""
    page_group = "Académique"

    def get_ecole(self):
        return getattr(self.request.user, "ecole", None)

    def get_annee(self):
        annee_id = self.request.GET.get("annee")
        qs = AnneeScolaire.objects.all().order_by("-debut")
        if annee_id:
            try:
                return qs.get(pk=annee_id)
            except AnneeScolaire.DoesNotExist:
                pass
        return qs.filter(est_active=True).first() or qs.first()

    def get_common_filters(self):
        return {
            "niveau_id": self.request.GET.get("niveau", "").strip(),
            "classe_id": self.request.GET.get("classe", "").strip(),
            "trimestre": self.request.GET.get("trimestre", "").strip(),
            "periode_id": self.request.GET.get("periode", "").strip(),
            "date_debut": self.request.GET.get("date_debut", "").strip(),
            "date_fin": self.request.GET.get("date_fin", "").strip(),
            "q": self.request.GET.get("q", "").strip(),
        }

    def get_filter_options(self):
        ecole = self.get_ecole()
        annee = self.get_annee()

        niveaux = Niveau.objects.all()
        classes = Classe.objects.select_related("niveau").all()
        periodes = PeriodeScolaire.objects.all()

        if ecole:
            niveaux = niveaux.filter(ecole=ecole)
            classes = classes.filter(ecole=ecole)
            periodes = periodes.filter(ecole=ecole)

        if annee:
            periodes = periodes.filter(annee_scolaire=annee)

        return {
            "annees": AnneeScolaire.objects.all().order_by("-debut"),
            "niveaux": niveaux.order_by("ordre", "nom"),
            "classes": classes.order_by("niveau__ordre", "nom"),
            "periodes": periodes.order_by("debut"),
        }

    def apply_date_filter(self, qs, field_name="date"):
        date_debut = self.request.GET.get("date_debut")
        date_fin = self.request.GET.get("date_fin")

        if date_debut:
            qs = qs.filter(**{f"{field_name}__gte": date_debut})
        if date_fin:
            qs = qs.filter(**{f"{field_name}__lte": date_fin})
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            "report_title": self.report_title,
            "report_subtitle": self.report_subtitle,
            "page_group": self.page_group,
            "selected_annee": self.get_annee(),
            "selected_ecole": self.get_ecole(),
            "filters": self.get_common_filters(),
        })
        context.update(self.get_filter_options())
        return context


class RapportCentreView(ReportBaseMixin, TemplateView):
    template_name = "rapports/rapport_centre.html"
    report_title = "Rapport Centre"
    report_subtitle = "Centre de rapports complet avec filtres"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["sections"] = [
            {
                "title": _("Académique"),
                "reports": [
                    (_("Liste des élèves par classe"), "rapport_eleves_par_classe"),
                    (_("Effectif par niveau / classe"), "rapport_effectif_niveau_classe"),
                    (_("Résumé des notes par classe"), "rapport_notes_classe"),
                    (_("Devoirs par professeur"), "rapport_devoirs_professeur"),
                    (_("Dispenses par matière"), "rapport_dispenses_matiere"),
                ],
            },
            {
                "title": _("Présence / Absences"),
                "reports": [
                    (_("Absences des élèves"), "rapport_absences_eleves"),
                    (_("Absences des professeurs"), "rapport_absences_professeurs"),
                    (_("Absences des employés"), "rapport_absences_employes"),
                ],
            },
            {
                "title": _("Finance / Gestionnaire"),
                "reports": [
                    (_("Paiements des élèves"), "rapport_paiements_eleves"),
                    (_("Frais dus / soldes"), "rapport_frais_dus"),
                    (_("Reçus de caisse"), "rapport_recus_caisse"),
                ],
            },
            {
                "title": _("Discipline"),
                "reports": [
                    (_("Convocations des parents"), "rapport_convocations_parents"),
                    (_("Cas de violence"), "rapport_violence"),
                    (_("Dégradations"), "rapport_degradations"),
                ],
            },
            {
                "title": _("Organisation / Administration"),
                "reports": [
                    (_("Liste des employés"), "rapport_employes"),
                    (_("Emploi du temps par classe"), "rapport_emploi_temps_classe"),
                    (_("Ressources pédagogiques"), "rapport_ressources_pedagogiques"),
                    (_("Bâtiments et salles"), "rapport_batiments_salles"),
                ],
            },
        ]
        return context


class RapportElevesParClasseView(ReportBaseMixin, TemplateView):
    template_name = "rapports/eleves_par_classe.html"
    report_title = _("Rapport liste des élèves par classe")
    page_group = "Académique"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        ecole = self.get_ecole()
        annee = self.get_annee()

        qs = Eleve.objects.select_related("classe", "classe__niveau", "annee_scolaire", "ecole").all()

        if ecole:
            qs = qs.filter(ecole=ecole)
        if annee:
            qs = qs.filter(annee_scolaire=annee)

        niveau_id = self.request.GET.get("niveau")
        classe_id = self.request.GET.get("classe")
        q = self.request.GET.get("q")

        if niveau_id:
            qs = qs.filter(classe__niveau_id=niveau_id)
        if classe_id:
            qs = qs.filter(classe_id=classe_id)
        if q:
            qs = qs.filter(
                Q(nom__icontains=q) |
                Q(identifiant__icontains=q) |
                Q(parent__icontains=q) |
                Q(telephone_parent__icontains=q)
            )

        context["rows"] = qs.order_by("classe__niveau__ordre", "classe__nom", "nom")
        return context


class RapportEffectifNiveauClasseView(ReportBaseMixin, TemplateView):
    template_name = "rapports/effectif_niveau_classe.html"
    report_title = report_title = _("Rapport effectif par niveau et classe")
    page_group = "Académique"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        ecole = self.get_ecole()
        annee = self.get_annee()

        qs = Classe.objects.select_related("niveau").annotate(
            total_eleves=Count("eleves", distinct=True),
            total_garcons=Count("eleves", filter=Q(eleves__Sexe="M"), distinct=True),
            total_filles=Count("eleves", filter=Q(eleves__Sexe="F"), distinct=True),
        )

        if ecole:
            qs = qs.filter(ecole=ecole)

        if annee:
            qs = qs.filter(eleves__annee_scolaire=annee).distinct()

        niveau_id = self.request.GET.get("niveau")
        classe_id = self.request.GET.get("classe")

        if niveau_id:
            qs = qs.filter(niveau_id=niveau_id)
        if classe_id:
            qs = qs.filter(id=classe_id)

        context["rows"] = qs.order_by("niveau__ordre", "nom")
        return context


class RapportNotesClasseView(ReportBaseMixin, TemplateView):
    template_name = "rapports/notes_classe.html"
    report_title = _("Rapport résumé des notes par classe")
    page_group = "Académique"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        ecole = self.get_ecole()
        annee = self.get_annee()

        qs = Note.objects.select_related(
            "eleve", "eleve__classe", "eleve__classe__niveau", "matiere", "devoir", "annee_scolaire"
        ).all()

        if ecole:
            qs = qs.filter(ecole=ecole)
        if annee:
            qs = qs.filter(annee_scolaire=annee)

        niveau_id = self.request.GET.get("niveau")
        classe_id = self.request.GET.get("classe")
        trimestre = self.request.GET.get("trimestre")
        q = self.request.GET.get("q")

        if niveau_id:
            qs = qs.filter(eleve__classe__niveau_id=niveau_id)
        if classe_id:
            qs = qs.filter(eleve__classe_id=classe_id)
        if trimestre:
            qs = qs.filter(trimestre=trimestre)
        if q:
            qs = qs.filter(
                Q(eleve__nom__icontains=q) |
                Q(matiere__nom__icontains=q) |
                Q(devoir__nom__icontains=q)
            )

        qs = qs.annotate(
            note_ponderee=ExpressionWrapper(
                F("note") * F("coefficient"),
                output_field=DecimalField(max_digits=12, decimal_places=2)
            )
        ).order_by("eleve__classe__nom", "eleve__nom", "matiere__nom")

        total_notes = qs.aggregate(
            somme=Coalesce(Sum("note_ponderee"), Decimal("0.00")),
            coeffs=Coalesce(Sum("coefficient"), 0)
        )
        moyenne_generale = Decimal("0.00")
        if total_notes["coeffs"]:
            moyenne_generale = total_notes["somme"] / Decimal(total_notes["coeffs"])

        context["rows"] = qs
        context["moyenne_generale"] = round(moyenne_generale, 2)
        return context


class RapportDevoirsProfesseurView(ReportBaseMixin, TemplateView):
    template_name = "rapports/devoirs_professeur.html"
    report_title = _("Rapport devoirs par professeur")
    page_group = "Académique"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        ecole = self.get_ecole()
        annee = self.get_annee()

        qs = Devoir.objects.select_related(
            "professeur", "niveau", "matiere", "periode", "annee_scolaire"
        ).prefetch_related("classes")

        if ecole:
            qs = qs.filter(ecole=ecole)
        if annee:
            qs = qs.filter(annee_scolaire=annee)

        niveau_id = self.request.GET.get("niveau")
        periode_id = self.request.GET.get("periode")
        q = self.request.GET.get("q")

        if niveau_id:
            qs = qs.filter(niveau_id=niveau_id)
        if periode_id:
            qs = qs.filter(periode_id=periode_id)
        if q:
            qs = qs.filter(
                Q(nom__icontains=q) |
                Q(professeur__nom_conplet__icontains=q) |
                Q(matiere__nom__icontains=q)
            )

        context["rows"] = qs.order_by("-date_creation")
        return context


class RapportDispensesMatiereView(ReportBaseMixin, TemplateView):
    template_name = "rapports/dispenses_matiere.html"
    report_title = _("Rapport dispenses par matière")
    page_group = "Académique"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        ecole = self.get_ecole()
        annee = self.get_annee()

        qs = DispenseMatiere.objects.select_related(
            "eleve", "eleve__classe", "eleve__classe__niveau", "matiere", "periode"
        )

        if ecole:
            qs = qs.filter(ecole=ecole)
        if annee:
            qs = qs.filter(annee_scolaire=annee)

        niveau_id = self.request.GET.get("niveau")
        classe_id = self.request.GET.get("classe")
        periode_id = self.request.GET.get("periode")
        q = self.request.GET.get("q")

        if niveau_id:
            qs = qs.filter(eleve__classe__niveau_id=niveau_id)
        if classe_id:
            qs = qs.filter(eleve__classe_id=classe_id)
        if periode_id:
            qs = qs.filter(periode_id=periode_id)
        if q:
            qs = qs.filter(
                Q(eleve__nom__icontains=q) |
                Q(matiere__nom__icontains=q) |
                Q(motif__icontains=q)
            )

        context["rows"] = qs.order_by("-created_at")
        return context


class RapportAbsencesElevesView(ReportBaseMixin, TemplateView):
    template_name = "rapports/absences_eleves.html"
    report_title = _("Rapport absences des élèves")
    page_group = "Présence / Absences"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        ecole = self.get_ecole()
        annee = self.get_annee()

        qs = Absence.objects.select_related(
            "eleve", "eleve__classe", "eleve__classe__niveau", "annee_scolaire"
        ).all()

        if ecole:
            qs = qs.filter(ecole=ecole)
        if annee:
            qs = qs.filter(annee_scolaire=annee)

        niveau_id = self.request.GET.get("niveau")
        classe_id = self.request.GET.get("classe")
        q = self.request.GET.get("q")

        if niveau_id:
            qs = qs.filter(eleve__classe__niveau_id=niveau_id)
        if classe_id:
            qs = qs.filter(eleve__classe_id=classe_id)
        if q:
            qs = qs.filter(
                Q(eleve__nom__icontains=q) |
                Q(motif__icontains=q) |
                Q(statut__icontains=q)
            )

        qs = self.apply_date_filter(qs, "date")

        context["rows"] = qs.order_by("-date", "eleve__nom")
        context["resume"] = qs.aggregate(
            total=Count("id"),
            presents=Count("id", filter=Q(statut="present")),
            absences=Count("id", filter=Q(statut="absence")),
            retards=Count("id", filter=Q(statut="retard")),
        )
        return context


class RapportAbsencesProfesseursView(ReportBaseMixin, TemplateView):
    template_name = "rapports/absences_professeurs.html"
    report_title = _("Rapport absences des professeurs")
    page_group = "Présence / Absences"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        ecole = self.get_ecole()
        annee = self.get_annee()

        qs = ProfesseurAbsence.objects.select_related("professeur", "annee_scolaire").all()

        if ecole:
            qs = qs.filter(ecole=ecole)
        if annee:
            qs = qs.filter(annee_scolaire=annee)

        q = self.request.GET.get("q")
        if q:
            qs = qs.filter(
                Q(professeur__nom_conplet__icontains=q) |
                Q(motif__icontains=q)
            )

        qs = self.apply_date_filter(qs, "date")

        context["rows"] = qs.order_by("-date", "professeur__nom_conplet")
        return context


class RapportAbsencesEmployesView(ReportBaseMixin, TemplateView):
    template_name = "rapports/absences_employes.html"
    report_title = _("Rapport absences des employés")
    page_group = "Présence / Absences"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        ecole = self.get_ecole()
        annee = self.get_annee()

        qs = EmployeAbsence.objects.select_related("employe", "annee_scolaire").all()

        if ecole:
            qs = qs.filter(ecole=ecole)
        if annee:
            qs = qs.filter(annee_scolaire=annee)

        q = self.request.GET.get("q")
        if q:
            qs = qs.filter(
                Q(employe__nom_complet__icontains=q) |
                Q(employe__fonction__icontains=q) |
                Q(motif__icontains=q)
            )

        qs = self.apply_date_filter(qs, "date")

        context["rows"] = qs.order_by("-date", "employe__nom_complet")
        return context


class RapportPaiementsElevesView(ReportBaseMixin, TemplateView):
    template_name = "rapports/paiements_eleves.html"
    report_title = _("Rapport paiements des élèves")
    page_group = "Finance / Gestionnaire"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        ecole = self.get_ecole()
        annee = self.get_annee()

        qs = Paiment.objects.select_related(
            "eleve", "eleve__classe", "eleve__classe__niveau", "type_paiement", "annee_scolaire"
        ).all()

        if ecole:
            qs = qs.filter(ecole=ecole)
        if annee:
            qs = qs.filter(annee_scolaire=annee)

        niveau_id = self.request.GET.get("niveau")
        classe_id = self.request.GET.get("classe")
        q = self.request.GET.get("q")

        if niveau_id:
            qs = qs.filter(eleve__classe__niveau_id=niveau_id)
        if classe_id:
            qs = qs.filter(eleve__classe_id=classe_id)
        if q:
            qs = qs.filter(
                Q(eleve__nom__icontains=q) |
                Q(type_paiement__nom__icontains=q) |
                Q(periode__icontains=q) |
                Q(moyen__icontains=q)
            )

        qs = self.apply_date_filter(qs, "date_paiement")

        context["rows"] = qs.order_by("-date_paiement", "eleve__nom")
        context["total_paye"] = qs.aggregate(total=Coalesce(Sum("montant"), Decimal("0.00")))["total"]
        return context


class RapportFraisDusView(ReportBaseMixin, TemplateView):
    template_name = "rapports/frais_dus.html"
    report_title = _("Rapport frais dus / soldes")
    page_group = "Finance / Gestionnaire"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        ecole = self.get_ecole()
        annee = self.get_annee()

        qs = FraisEleve.objects.select_related(
            "eleve", "eleve__classe", "eleve__classe__niveau", "type_paiement", "niveau"
        ).annotate(
            total_paye_calc=Coalesce(Sum("paiements__montant"), Decimal("0.00"))
        )

        if ecole:
            qs = qs.filter(ecole=ecole)
        if annee:
            qs = qs.filter(annee_scolaire=annee)

        niveau_id = self.request.GET.get("niveau")
        classe_id = self.request.GET.get("classe")
        q = self.request.GET.get("q")

        if niveau_id:
            qs = qs.filter(eleve__classe__niveau_id=niveau_id)
        if classe_id:
            qs = qs.filter(eleve__classe_id=classe_id)
        if q:
            qs = qs.filter(
                Q(eleve__nom__icontains=q) |
                Q(type_paiement__nom__icontains=q)
            )

        rows = []
        total_du = Decimal("0.00")
        total_paye = Decimal("0.00")
        total_reste = Decimal("0.00")

        for item in qs.order_by("eleve__nom"):
            montant = item.montant or Decimal("0.00")
            paye = item.total_paye_calc or Decimal("0.00")
            reste = montant - paye
            rows.append({
                "obj": item,
                "montant_du": montant,
                "montant_paye": paye,
                "reste": reste,
                "statut_calcule": "Payé" if reste <= 0 else "Impayé",
            })
            total_du += montant
            total_paye += paye
            total_reste += reste

        context["rows"] = rows
        context["total_du"] = total_du
        context["total_paye"] = total_paye
        context["total_reste"] = total_reste
        return context


class RapportRecusCaisseView(ReportBaseMixin, TemplateView):
    template_name = "rapports/recus_caisse.html"
    report_title = _("Rapport reçus de caisse")
    page_group = "Finance / Gestionnaire"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        ecole = self.get_ecole()
        annee = self.get_annee()

        qs = RecuCaisse.objects.select_related(
            "eleve", "eleve__classe", "caissier", "annee_scolaire"
        ).all()

        if ecole:
            qs = qs.filter(ecole=ecole)
        if annee:
            qs = qs.filter(annee_scolaire=annee)

        classe_id = self.request.GET.get("classe")
        q = self.request.GET.get("q")

        if classe_id:
            qs = qs.filter(eleve__classe_id=classe_id)
        if q:
            qs = qs.filter(
                Q(numero__icontains=q) |
                Q(eleve__nom__icontains=q) |
                Q(reference__icontains=q) |
                Q(statut__icontains=q)
            )

        qs = self.apply_date_filter(qs, "date_operation")

        context["rows"] = qs.order_by("-date_operation")
        context["total_recus"] = qs.aggregate(total=Coalesce(Sum("total"), Decimal("0.00")))["total"]
        return context


class RapportConvocationsParentsView(ReportBaseMixin, TemplateView):
    template_name = "rapports/convocations_parents.html"
    report_title = _("Rapport convocations des parents")
    page_group = "Discipline"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        ecole = self.get_ecole()
        annee = self.get_annee()

        qs = ConvocationParent.objects.select_related(
            "niveau", "classe", "eleve", "raison", "parent_user", "cree_par"
        ).all()

        if ecole:
            qs = qs.filter(ecole=ecole)
        if annee:
            qs = qs.filter(annee_scolaire=annee)

        niveau_id = self.request.GET.get("niveau")
        classe_id = self.request.GET.get("classe")
        q = self.request.GET.get("q")

        if niveau_id:
            qs = qs.filter(niveau_id=niveau_id)
        if classe_id:
            qs = qs.filter(classe_id=classe_id)
        if q:
            qs = qs.filter(
                Q(eleve__nom__icontains=q) |
                Q(raison__libelle__icontains=q) |
                Q(message__icontains=q)
            )

        qs = self.apply_date_filter(qs, "date_convocation")

        context["rows"] = qs.order_by("-date_convocation")
        return context


class RapportViolenceView(ReportBaseMixin, TemplateView):
    template_name = "rapports/violence.html"
    report_title = _("Rapport cas de violence")
    page_group = "Discipline"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        q = self.request.GET.get("q")

        qs = Violence.objects.select_related("agresseur", "victime").all()

        if q:
            qs = qs.filter(
                Q(agresseur__nom__icontains=q) |
                Q(victime__nom__icontains=q) |
                Q(forme_agression__icontains=q) |
                Q(cause_violence__icontains=q)
            )

        qs = self.apply_date_filter(qs, "date")

        ecole = self.get_ecole()
        annee = self.get_annee()
        if ecole:
            qs = qs.filter(
                Q(agresseur__ecole=ecole) | Q(victime__ecole=ecole)
            )
        if annee:
            qs = qs.filter(
                Q(agresseur__annee_scolaire=annee) | Q(victime__annee_scolaire=annee)
            )

        context["rows"] = qs.order_by("-date")
        return context


class RapportDegradationsView(ReportBaseMixin, TemplateView):
    template_name = "rapports/degradations.html"
    report_title = _("Rapport dégradations")
    page_group = "Discipline"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        qs = Degradation.objects.select_related("eleve", "eleve__classe", "cree_par").all()

        ecole = self.get_ecole()
        annee = self.get_annee()
        q = self.request.GET.get("q")
        classe_id = self.request.GET.get("classe")

        if ecole:
            qs = qs.filter(eleve__ecole=ecole)
        if annee:
            qs = qs.filter(eleve__annee_scolaire=annee)
        if classe_id:
            qs = qs.filter(eleve__classe_id=classe_id)
        if q:
            qs = qs.filter(
                Q(eleve__nom__icontains=q) |
                Q(degradation_commise__icontains=q) |
                Q(decision_prise__icontains=q) |
                Q(decision_autre__icontains=q)
            )

        qs = self.apply_date_filter(qs, "date")

        context["rows"] = qs.order_by("-date")
        return context


class RapportEmployesView(ReportBaseMixin, TemplateView):
    template_name = "rapports/employes.html"
    report_title = _("Rapport liste des employés")
    page_group = "Organisation / Administration"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        qs = Employe.objects.all()
        ecole = self.get_ecole()
        q = self.request.GET.get("q")

        if ecole:
            qs = qs.filter(ecole=ecole)
        if q:
            qs = qs.filter(
                Q(nom_complet__icontains=q) |
                Q(matricule__icontains=q) |
                Q(fonction__icontains=q) |
                Q(bureau__icontains=q)
            )

        context["rows"] = qs.order_by("nom_complet")
        context["resume"] = qs.aggregate(
            total=Count("id"),
            actifs=Count("id", filter=Q(statut="active")),
            inactifs=Count("id", filter=Q(statut="inactive")),
            hommes=Count("id", filter=Q(sexe="M")),
            femmes=Count("id", filter=Q(sexe="F")),
        )
        return context


class RapportEmploiTempsClasseView(ReportBaseMixin, TemplateView):
    template_name = "rapports/emploi_temps_classe.html"
    report_title = _("Rapport emploi du temps par classe")
    page_group = "Organisation / Administration"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        qs = EmploiDuTemps.objects.select_related(
            "classe", "classe__niveau", "matiere", "professeur", "salle", "annee_scolaire"
        ).all()

        ecole = self.get_ecole()
        annee = self.get_annee()
        niveau_id = self.request.GET.get("niveau")
        classe_id = self.request.GET.get("classe")
        q = self.request.GET.get("q")

        if ecole:
            qs = qs.filter(ecole=ecole)
        if annee:
            qs = qs.filter(annee_scolaire=annee)
        if niveau_id:
            qs = qs.filter(classe__niveau_id=niveau_id)
        if classe_id:
            qs = qs.filter(classe_id=classe_id)
        if q:
            qs = qs.filter(
                Q(classe__nom__icontains=q) |
                Q(matiere__nom__icontains=q) |
                Q(professeur__nom_conplet__icontains=q) |
                Q(salle__nom__icontains=q)
            )

        context["rows"] = qs.order_by("classe__niveau__ordre", "classe__nom", "jour", "heure_debut")
        return context


class RapportRessourcesPedagogiquesView(ReportBaseMixin, TemplateView):
    template_name = "rapports/ressources_pedagogiques.html"
    report_title = _("Rapport ressources pédagogiques")
    page_group = "Organisation / Administration"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        qs = Ressource.objects.select_related("professeur", "matier", "annee_scolaire").all()

        ecole = self.get_ecole()
        annee = self.get_annee()
        q = self.request.GET.get("q")

        if ecole:
            qs = qs.filter(ecole=ecole)
        if annee:
            qs = qs.filter(annee_scolaire=annee)
        if q:
            qs = qs.filter(
                Q(professeur__nom_conplet__icontains=q) |
                Q(matier__nom__icontains=q) |
                Q(description__icontains=q)
            )

        context["rows"] = qs.order_by("-created_at")
        return context


class RapportBatimentsSallesView(ReportBaseMixin, TemplateView):
    template_name = "rapports/batiments_salles.html"
    report_title = _("Rapport bâtiments et salles")
    page_group = "Organisation / Administration"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        qs = Salle.objects.select_related("batiment", "ecole").all()
        ecole = self.get_ecole()
        q = self.request.GET.get("q")

        if ecole:
            qs = qs.filter(ecole=ecole)
        if q:
            qs = qs.filter(
                Q(nom__icontains=q) |
                Q(batiment__nom__icontains=q) |
                Q(description__icontains=q)
            )

        context["rows"] = qs.order_by("batiment__nom", "etage", "nom")
        return context