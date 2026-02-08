from django.urls import reverse_lazy, reverse
from django.views.generic import ListView, CreateView, DeleteView, UpdateView
from django.shortcuts import render
from Ecole_admin.models import Paiment, Eleve , Niveau , TypePaiement , TarifPaiement , AnneeScolaire , FraisEleve , PaiementFraisEleve , RecuCaisse, LigneRecuCaisse , Classe
from Ecole_admin.utils.mixins import ActiveYearMixin , EcoleAssignMixin
from django.contrib.auth.mixins import LoginRequiredMixin

from Ecole_admin.utils.utils import get_annee_active

from django.views import View
from django.shortcuts import render, redirect
from django.contrib import messages


from django.http import HttpResponse
from django.db.models import Sum
from django.utils.timezone import now

class ConfigPaiementView(View):
    template_name = "ConfugurationPaiment.html"

    def get(self, request):
        ecole = request.user.ecole
        annee = get_annee_active(request)

        niveaux = Niveau.objects.filter(ecole=ecole, actif=True).order_by("ordre", "nom")
        types = TypePaiement.objects.filter(ecole=ecole, actif=True).order_by("nom")

        niveau_id = request.GET.get("niveau") or ""
        type_id = request.GET.get("type") or ""

        tarif = None
        if niveau_id.isdigit() and type_id.isdigit():
            tarif = TarifPaiement.objects.filter(
                ecole=ecole,
                annee_scolaire=annee,
                niveau_id=int(niveau_id),
                type_paiement_id=int(type_id)
            ).first()

        context = {
            "niveaux": niveaux,
            "types": types,
            "niveau_id": niveau_id,
            "type_id": type_id,
            "tarif": tarif,
        }
        return render(request, self.template_name, context)

    def post(self, request):
        ecole = request.user.ecole
        annee = get_annee_active(request)

        niveau_id = request.POST.get("niveau") or ""
        type_id = request.POST.get("type") or ""
        montant = request.POST.get("montant") or "0"
        devise = request.POST.get("devise") or "DJF"

        if not (niveau_id.isdigit() and type_id.isdigit()):
            messages.error(request, "Veuillez choisir un niveau et un type de frais.")
            return redirect("config_paiement")

        obj, created = TarifPaiement.objects.update_or_create(
            ecole=ecole,
            annee_scolaire=annee,
            niveau_id=int(niveau_id),
            type_paiement_id=int(type_id),
            defaults={
                "montant": montant,
                "devise": devise,
                "actif": True
            }
        )

        messages.success(request, "Configuration enregistrée avec succès.")
        return redirect(f"{request.path}?niveau={niveau_id}&type={type_id}")



class PaimentListView( LoginRequiredMixin ,ListView):
    model = Paiment
    template_name = 'paiment_list.html'
    context_object_name = 'paiments'
    paginate_by = 20

    def get_queryset(self):
        queryset = Paiment.objects.filter(
            ecole=self.request.user.ecole,
            annee_scolaire = get_annee_active(self.request)
        )



        classe = self.request.GET.get("classe")
        eleve = self.request.GET.get("eleve")
        periode = self.request.GET.get("periode")

        if classe and classe != "":
            queryset = queryset.filter(eleve__classe_id=classe)

        if eleve and eleve != "":
            queryset = queryset.filter(eleve__id=eleve)
        if periode and periode != "":
            queryset = queryset.filter(periode__icontains = periode)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        queryset = self.get_queryset()
        context['classes'] = self.request.user.ecole.classe_set.all()
        context['eleves'] = Eleve.objects.filter(  ecole=self.request.user.ecole,annee_scolaire = get_annee_active(self.request)).all
        return context

class PaimentCreateView(ActiveYearMixin, EcoleAssignMixin, CreateView):
    model = Paiment
    template_name = 'paiement_creation.html'
    fields = [
        'eleve',
        'montant',
        'date_paiement',
        'periode',
        'moyen',
    ]
    success_url = reverse_lazy('liste_de_paiment')

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        annee_active = get_annee_active(self.request)
        ecole = getattr(self.request.user, "ecole", None)

        if ecole and annee_active:
            form.fields["eleve"].queryset = Eleve.objects.filter(
                ecole=ecole,
                annee_scolaire=annee_active
            )
        else:
            form.fields["eleve"].queryset = Eleve.objects.none()

        return form

    def get_initial(self):
        initial = super().get_initial()
        eleve_id = self.kwargs.get("eleve_id")
        if eleve_id:
            initial["eleve"] = eleve_id
        return initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['eleves'] = Eleve.objects.filter( ecole=self.request.user.ecole, annee_scolaire = get_annee_active(self.request))
        context['Title'] = "Effectue une paiment"
        context['Submit_text'] = 'Effectue'
        return context

    def get_success_url(self):
        eleve_id = self.kwargs.get("eleve_id")
        if eleve_id:
            return reverse("detaille", kwargs={"id": eleve_id})
        return reverse("liste_de_paiment")

class PaimentUpdateView(UpdateView):
    model = Paiment
    template_name = 'paiement_creation.html'
    fields = [
        'eleve',
        'montant',
        'date_paiement',
        'periode',
        'moyen',
    ]
    success_url = reverse_lazy('liste_de_paiment')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['eleves'] = Eleve.objects.all()
        context['Title'] = "Modifiee une paiment"
        context['Submit_text'] = 'Modifiee'
        return context

class PaimentDeleteView(DeleteView):
    model = Paiment
    template_name = 'paiment_supprimation.html'
    success_url = reverse_lazy('liste_de_paiment')






class FraisNiveauView(View):
    template_name = "frais_niveau.html"

    def get(self, request):
        ecole = request.user.ecole

        annees = AnneeScolaire.objects.all().order_by("-id")  # adapte si tu filtres par école
        niveaux = Niveau.objects.filter(ecole=ecole, actif=True).order_by("ordre", "nom")
        types = TypePaiement.objects.filter(ecole=ecole, actif=True).order_by("nom")

        annee_id = request.GET.get("annee") or ""
        niveau_id = request.GET.get("niveau") or ""
        type_id = request.GET.get("type") or ""

        tarif = None
        frais_list = []

        if annee_id.isdigit() and niveau_id.isdigit() and type_id.isdigit():
            tarif = TarifPaiement.objects.filter(
                ecole=ecole,
                annee_scolaire_id=int(annee_id),
                niveau_id=int(niveau_id),
                type_paiement_id=int(type_id),
                actif=True
            ).first()

            # si déjà généré, on liste ce qui existe
            frais_list = FraisEleve.objects.filter(
                ecole=ecole,
                annee_scolaire_id=int(annee_id),
                niveau_id=int(niveau_id),
                type_paiement_id=int(type_id)
            ).select_related("eleve", "niveau").order_by("eleve__nom")

        return render(request, self.template_name, {
            "annees": annees,
            "niveaux": niveaux,
            "types": types,
            "annee_id": annee_id,
            "niveau_id": niveau_id,
            "type_id": type_id,
            "tarif": tarif,
            "frais_list": frais_list,
        })

    def post(self, request):
        ecole = request.user.ecole

        annee_id = request.POST.get("annee") or ""
        niveau_id = request.POST.get("niveau") or ""
        type_id = request.POST.get("type") or ""

        if not (annee_id.isdigit() and niveau_id.isdigit() and type_id.isdigit()):
            messages.error(request, "Veuillez choisir Année scolaire + Niveau + Type de frais.")
            return redirect("finance_frais")

        tarif = TarifPaiement.objects.filter(
            ecole=ecole,
            annee_scolaire_id=int(annee_id),
            niveau_id=int(niveau_id),
            type_paiement_id=int(type_id),
            actif=True
        ).first()

        if not tarif:
            messages.error(request, "Aucun tarif trouvé pour ce Niveau / Type / Année. Configure d'abord le tarif.")
            return redirect(f"{request.path}?annee={annee_id}&niveau={niveau_id}&type={type_id}")

        # ✅ tous les élèves du niveau (toutes classes)
        eleves = Eleve.objects.filter(
            ecole=ecole,
            annee_scolaire_id=int(annee_id),
            classe__niveau_id=int(niveau_id)
        ).select_related("classe", "classe__niveau").order_by("nom")

        count = 0
        for e in eleves:
            FraisEleve.objects.update_or_create(
                ecole=ecole,
                annee_scolaire_id=int(annee_id),
                eleve=e,
                type_paiement_id=int(type_id),
                defaults={
                    "niveau_id": int(niveau_id),
                    "montant": tarif.montant,
                    "devise": tarif.devise,
                }
            )
            count += 1

        messages.success(request, f"Frais générés pour {count} élèves.")
        return redirect(f"{request.path}?annee={annee_id}&niveau={niveau_id}&type={type_id}")




class PaiementFraisView(View): 
    template_name = "paiement_frais.html"

    def get(self, request):
        ecole = request.user.ecole

        annees = AnneeScolaire.objects.all().order_by("-id")
        niveaux = Niveau.objects.filter(ecole=ecole, actif=True).order_by("ordre", "nom")
        types = TypePaiement.objects.filter(ecole=ecole, actif=True).order_by("nom")

        annee_id = request.GET.get("annee") or ""
        niveau_id = request.GET.get("niveau") or ""
        type_id = request.GET.get("type") or ""

        annee_obj = None
        niveau_obj = None
        type_obj = None

        if annee_id.isdigit():
            annee_obj = AnneeScolaire.objects.filter(id=int(annee_id)).first()

        if niveau_id.isdigit():
            niveau_obj = Niveau.objects.filter(id=int(niveau_id)).first()

        if type_id.isdigit():
            type_obj = TypePaiement.objects.filter(id=int(type_id)).first()


        rows = []

        if annee_id.isdigit() and niveau_id.isdigit() and type_id.isdigit():
            frais_qs = FraisEleve.objects.filter(
                ecole=ecole,
                annee_scolaire_id=int(annee_id),
                niveau_id=int(niveau_id),
                type_paiement_id=int(type_id),
            ).select_related("eleve", "eleve__classe", "eleve__classe__niveau", "type_paiement")

            # Pré-calcul paiements par frais_eleve
            pay_map = {
                x["frais_eleve_id"]: (x["total"] or 0)
                for x in PaiementFraisEleve.objects.filter(
                    ecole=ecole,
                    annee_scolaire_id=int(annee_id),
                    frais_eleve__in=frais_qs
                ).values("frais_eleve_id").annotate(total=Sum("montant"))
            }

            # mode de paiement (dernier paiement)
            mode_map = {
                p.frais_eleve_id: p.get_mode_display()
                for p in PaiementFraisEleve.objects.filter(
                    ecole=ecole,
                    annee_scolaire_id=int(annee_id),
                    frais_eleve__in=frais_qs
                ).order_by("frais_eleve_id", "-date_paiement")
            }

            for f in frais_qs:
                paye = pay_map.get(f.id, 0)
                restant = float(f.montant) - float(paye)
                if restant < 0:
                    restant = 0

                rows.append({
                    "eleve": f.eleve.nom,
                    "niveau": f"{f.eleve.classe.niveau} - {f.eleve.classe.nom}",
                    "type": f.type_paiement.nom,
                    "mode": mode_map.get(f.id, "—"),
                    "facture": f.montant,
                    "paye": paye,
                    "restant": restant,
                    "devise": f.devise
                })

        return render(request, self.template_name, {
            "annees": annees,
            "niveaux": niveaux,
            "types": types,
            "annee_id": annee_id,
            "niveau_id": niveau_id,
            "type_id": type_id,
            "annee_obj": annee_obj,
            "niveau_obj": niveau_obj,
            "type_obj": type_obj,
            "rows": rows
        })



def export_paiement_csv(request):
    ecole = request.user.ecole
    annee_id = request.GET.get("annee") or ""
    niveau_id = request.GET.get("niveau") or ""
    type_id = request.GET.get("type") or ""

    if not (annee_id.isdigit() and niveau_id.isdigit() and type_id.isdigit()):
        return HttpResponse("Filtres invalides", status=400)

    frais_qs = FraisEleve.objects.filter(
        ecole=ecole,
        annee_scolaire_id=int(annee_id),
        niveau_id=int(niveau_id),
        type_paiement_id=int(type_id),
    ).select_related("eleve", "eleve__classe", "eleve__classe__niveau", "type_paiement")

    pay_map = {
        x["frais_eleve_id"]: (x["total"] or 0)
        for x in PaiementFraisEleve.objects.filter(
            ecole=ecole,
            annee_scolaire_id=int(annee_id),
            frais_eleve__in=frais_qs
        ).values("frais_eleve_id").annotate(total=Sum("montant"))
    }

    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="paiement_frais.csv"'
    response.write("Eleve;Niveau;Type;Facture;Paye;Restant;Devise\n")

    for f in frais_qs:
        paye = pay_map.get(f.id, 0)
        restant = float(f.montant) - float(paye)
        if restant < 0:
            restant = 0
        response.write(f"{f.eleve.nom};{f.eleve.classe.niveau} - {f.eleve.classe.nom};{f.type_paiement.nom};{f.montant};{paye};{restant};{f.devise}\n")

    return response

from django.http import HttpResponse
from django.views.decorators.http import require_GET
from django.utils.html import escape
from django.views import View
from django.shortcuts import render, redirect
from django.contrib import messages
from django.db import transaction
from django.db.models import Sum

# =========================
# AJAX
# =========================
@require_GET
def ajax_classes_by_niveau(request):
    ecole = request.user.ecole
    niveau_id = request.GET.get("niveau_id") or ""

    html = ['<option value="">Sélectionner...</option>']
    qs = Classe.objects.filter(ecole=ecole, actif=True)

    if niveau_id.isdigit():
        qs = qs.filter(niveau_id=int(niveau_id))

    for c in qs.order_by("nom"):
        html.append(f'<option value="{c.id}">{escape(c.nom)}</option>')

    return HttpResponse("".join(html))


@require_GET
def ajax_eleves_by_classe(request):
    ecole = request.user.ecole
    annee = get_annee_active(request)
    classe_id = request.GET.get("classe_id") or ""

    html = ['<option value="">Sélectionner...</option>']

    qs = Eleve.objects.filter(ecole=ecole)
    if annee:
        qs = qs.filter(annee_scolaire=annee)

    if classe_id.isdigit():
        qs = qs.filter(classe_id=int(classe_id))

    for e in qs.order_by("nom"):
        html.append(f'<option value="{e.id}">{escape(e.nom)}</option>')

    return HttpResponse("".join(html))


# =========================
# CAISSE
# =========================
def _next_recu_number():
    from django.utils.timezone import now
    year = now().year
    last = RecuCaisse.objects.filter(numero__startswith=f"RC-{year}-").order_by("-numero").first()
    if not last:
        return f"RC-{year}-00001"
    last_num = int(last.numero.split("-")[-1])
    return f"RC-{year}-{last_num+1:05d}"


class CaisseView(View):
    template_name = "caisse.html"

    def get(self, request):
        ecole = request.user.ecole
        annee = get_annee_active(request)

        niveaux = Niveau.objects.filter(ecole=ecole, actif=True).order_by("ordre", "nom")
        types = TypePaiement.objects.filter(ecole=ecole, actif=True).order_by("nom")

        niveau_id = request.GET.get("niveau") or ""
        classe_id = request.GET.get("classe") or ""
        eleve_id = request.GET.get("eleve") or ""

        # ✅ FIX: si eleve est donné, déduire classe + niveau automatiquement
        if eleve_id.isdigit():
            eleve_tmp = Eleve.objects.filter(
                id=int(eleve_id), ecole=ecole
            ).select_related("classe", "classe__niveau").first()

            if eleve_tmp and eleve_tmp.classe_id:
                classe_id = str(eleve_tmp.classe_id)
                if hasattr(eleve_tmp.classe, "niveau_id"):
                    niveau_id = str(eleve_tmp.classe.niveau_id)

        # ✅ FIX: si classe est donnée mais niveau vide → déduire niveau
        if classe_id.isdigit() and not niveau_id.isdigit():
            c = Classe.objects.filter(id=int(classe_id), ecole=ecole).select_related("niveau").first()
            if c:
                niveau_id = str(c.niveau_id)

        eleve = None
        frais_rows = []

        if eleve_id.isdigit():
            eleve = Eleve.objects.filter(
                id=int(eleve_id), ecole=ecole
            ).select_related("classe", "classe__niveau").first()

            # si tu veux forcer annee active seulement, décommente :
            # if annee:
            #     eleve = Eleve.objects.filter(id=int(eleve_id), ecole=ecole, annee_scolaire=annee).select_related("classe", "classe__niveau").first()

        if eleve and annee:
            frais_qs = FraisEleve.objects.filter(
                ecole=ecole, annee_scolaire=annee, eleve=eleve
            ).select_related("type_paiement")

            pay_map = {
                x["frais_eleve_id"]: (x["total"] or 0)
                for x in PaiementFraisEleve.objects.filter(
                    ecole=ecole, annee_scolaire=annee, frais_eleve__in=frais_qs
                ).values("frais_eleve_id").annotate(total=Sum("montant"))
            }

            for f in frais_qs:
                paye = pay_map.get(f.id, 0)
                restant = float(f.montant) - float(paye)
                if restant < 0:
                    restant = 0
                frais_rows.append({
                    "id": f.id,
                    "type": f.type_paiement.nom,
                    "facture": f.montant,
                    "paye": paye,
                    "restant": restant,
                    "devise": f.devise
                })

        return render(request, self.template_name, {
            "niveaux": niveaux,
            "types": types,
            "niveau_id": niveau_id,
            "classe_id": classe_id,
            "eleve_id": eleve_id,
            "eleve": eleve,
            "frais_rows": frais_rows,
        })

    from django.utils.timezone import now

    @transaction.atomic
    def post(self, request):
        ecole = request.user.ecole
        annee = get_annee_active(request)

        eleve_id = request.POST.get("eleve") or ""
        mode = request.POST.get("mode") or "especes"
        devise = request.POST.get("devise") or "DJF"
        note = (request.POST.get("note") or "").strip()

        if not eleve_id.isdigit():
            messages.error(request, "Choisis d'abord un élève.")
            return redirect("caisse")

        eleve = Eleve.objects.filter(id=int(eleve_id), ecole=ecole).first()
        if not eleve or not annee:
            messages.error(request, "Élève ou année scolaire invalide.")
            return redirect("caisse")

        date_str = now().strftime("%Y%m%d")

        frais_ids = FraisEleve.objects.filter(
            ecole=ecole,
            annee_scolaire=annee,
            eleve=eleve
        ).values_list("id", flat=True)

        total = 0
        lignes = []

        for fid in frais_ids:
            amount_str = request.POST.get(f"pay_amount_{fid}") or ""
            if not amount_str:
                continue

            try:
                amount = float(amount_str)
            except:
                continue

            if amount <= 0:
                continue

            frais = FraisEleve.objects.select_related("type_paiement").filter(
                id=fid,
                ecole=ecole,
                annee_scolaire=annee,
                eleve=eleve
            ).first()
            if not frais:
                continue

            # ✅ RÉFÉRENCE AUTO
            reference_auto = f"PAY-{date_str}-F{frais.id}"

            # total déjà payé pour ce frais
            deja_paye = (
                PaiementFraisEleve.objects.filter(
                    ecole=ecole,
                    annee_scolaire=annee,
                    frais_eleve=frais
                ).aggregate(s=Sum("montant"))["s"] or 0
            )

            restant = float(frais.montant) - float(deja_paye)
            if restant <= 0:
                # déjà soldé → on ignore ce paiement
                continue

            # si l'utilisateur met plus que le restant, on limite ou on refuse
            if amount > restant:
                messages.error(request, f"Montant trop élevé pour '{frais.type_paiement.nom}'. Restant: {restant} {frais.devise}.")
                return redirect(f"{request.path}?eleve={eleve.id}")


            PaiementFraisEleve.objects.create(
                ecole=ecole,
                annee_scolaire=annee,
                frais_eleve=frais,
                montant=amount,
                devise=frais.devise,
                mode=mode,
                reference=reference_auto
            )

            lignes.append((frais, amount, frais.devise))
            total += amount

        if total <= 0:
            messages.error(request, "Saisis au moins un montant à payer.")
            return redirect(f"{request.path}?eleve={eleve.id}")

        recu = RecuCaisse.objects.create(
            ecole=ecole,
            annee_scolaire=annee,
            eleve=eleve,
            caissier=request.user,
            numero=_next_recu_number(),
            total=total,
            devise=devise,
            mode=mode,
            note=note
        )

        for frais, amount, dev in lignes:
            LigneRecuCaisse.objects.create(
                recu=recu,
                frais_eleve=frais,
                montant=amount,
                devise=dev
            )

        messages.success(request, "Paiement enregistré. Référence générée automatiquement.")
        return redirect("recu_print", pk=recu.pk)


from django.views.generic import DetailView

from django.db.models import Sum

def recu_print(request, pk):
    recu = RecuCaisse.objects.select_related("eleve", "annee_scolaire", "caissier").get(pk=pk)

    rows = []
    for l in recu.lignes.select_related("frais_eleve", "frais_eleve__type_paiement"):
        frais = l.frais_eleve

        total_paye = (PaiementFraisEleve.objects
                      .filter(ecole=recu.ecole, annee_scolaire=recu.annee_scolaire, frais_eleve=frais)
                      .aggregate(s=Sum("montant"))["s"] or 0)

        restant = float(frais.montant) - float(total_paye)
        if restant < 0:
            restant = 0

        rows.append({
            "type": frais.type_paiement.nom,
            "facture": frais.montant,
            "paye": total_paye,
            "reste": restant,
            "devise": frais.devise,
            "paye_ce_recu": l.montant,
        })

    return render(request, "recu_print.html", {"object": recu, "rows": rows})


from django.views import View
from django.shortcuts import render
from django.db.models import Q, Sum
from datetime import datetime



class JournalCaisseView(View):
    template_name = "journal_caisse.html"

    def get(self, request):
        ecole = request.user.ecole

        q = (request.GET.get("q") or "").strip()
        mode = (request.GET.get("mode") or "").strip()
        d1 = (request.GET.get("d1") or "").strip()
        d2 = (request.GET.get("d2") or "").strip()

        qs = RecuCaisse.objects.filter(ecole=ecole).select_related(
            "eleve", "eleve__classe", "eleve__classe__niveau", "caissier", "annee_scolaire"
        ).order_by("-date_operation")

        if mode:
            qs = qs.filter(mode=mode)

        if d1:
            try:
                qs = qs.filter(date_operation__date__gte=datetime.strptime(d1, "%Y-%m-%d").date())
            except:
                pass

        if d2:
            try:
                qs = qs.filter(date_operation__date__lte=datetime.strptime(d2, "%Y-%m-%d").date())
            except:
                pass

        if q:
            qs = qs.filter(
                Q(numero__icontains=q) |
                Q(eleve__nom__icontains=q) |
                Q(eleve__classe__nom__icontains=q)
            )

        # ✅ Totaux uniquement sur reçus valides
        valid_qs = qs.filter(statut="valide")
        totals = valid_qs.values("mode").annotate(total=Sum("total")).order_by("mode")
        grand_total = valid_qs.aggregate(t=Sum("total"))["t"] or 0

        return render(request, self.template_name, {
            "rows": qs[:500],
            "q": q, "mode": mode, "d1": d1, "d2": d2,
            "totals": totals, "grand_total": grand_total
        })


from django.views import View
from django.shortcuts import render, get_object_or_404
from django.db.models import Sum



class HistoriqueEleveView(View):
    template_name = "historique_eleve.html"

    def get(self, request, eleve_id):
        ecole = request.user.ecole
        annee = get_annee_active(request)

        eleve = get_object_or_404(Eleve, id=eleve_id, ecole=ecole, annee_scolaire=annee)

        recus = RecuCaisse.objects.filter(
            ecole=ecole, annee_scolaire=annee, eleve=eleve
        ).prefetch_related(
            "lignes", "lignes__frais_eleve", "lignes__frais_eleve__type_paiement"
        ).select_related("caissier").order_by("-date_operation")

        total_paye = recus.filter(statut="valide").aggregate(t=Sum("total"))["t"] or 0

        return render(request, self.template_name, {
            "eleve": eleve,
            "recus": recus,
            "total_paye": total_paye
        })




from django.views import View
from django.shortcuts import render
from django.db.models import Sum
from django.utils.timezone import localdate


class ClotureCaisseView(View):
    template_name = "cloture_caisse.html"

    def get(self, request):
        ecole = request.user.ecole
        day = request.GET.get("day") or str(localdate())

        qs = RecuCaisse.objects.filter(
            ecole=ecole,
            date_operation__date=day,
            statut="valide"
        )

        totals = qs.values("mode").annotate(total=Sum("total")).order_by("mode")
        grand_total = qs.aggregate(t=Sum("total"))["t"] or 0

        return render(request, self.template_name, {
            "day": day,
            "totals": totals,
            "grand_total": grand_total,
            "rows": qs.select_related("eleve", "caissier").order_by("-date_operation")[:200]
        })


from django.shortcuts import get_object_or_404, redirect
from django.utils import timezone
from django.contrib import messages
from django.views.decorators.http import require_POST



@require_POST
def annuler_recu(request, recu_id):
    ecole = request.user.ecole
    motif = (request.POST.get("motif") or "").strip()

    recu = get_object_or_404(RecuCaisse, pk=recu_id, ecole=ecole)

    if recu.statut == "annule":
        messages.info(request, "Ce reçu est déjà annulé.")
        return redirect("journal_caisse")

    recu.statut = "annule"
    recu.annule_par = request.user
    recu.date_annulation = timezone.now()
    recu.motif_annulation = motif
    recu.save(update_fields=["statut", "annule_par", "date_annulation", "motif_annulation"])

    messages.success(request, "Reçu annulé avec succès.")
    return redirect("journal_caisse")
