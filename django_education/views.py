# -*-coding: utf-8 -*-

from django.shortcuts import render, redirect, HttpResponseRedirect
from .models import Utilisateur, sequence, sequence_info, famille_competence, competence, cours, cours_info,\
    td, td_info, tp, ilot,tp_info, khole, Note, Etudiant, Professeur, langue_vivante, DS, systeme, parametre, fichier_systeme,\
    image_systeme, video, ressource, item_synthese, fiche_synthese, reponse_item_synthese

from quiz.models import Quiz, Category, Progress
from django.utils import timezone
from django.db.models import Sum, Avg, Func
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django_tex.shortcuts import render_to_pdf

from .forms import ContactForm, ReponseItemSyntheseForm
import datetime
from jchart import Chart
from jchart.config import Axes, DataSet, rgba
from math import ceil
from .filters import SystemeFiltre
from django.http import HttpResponse
from urllib.request import urlopen
import unicodedata

github='https://github.com/Costadoat/'

def remove_accents(input_str):
    nfkd_form = unicodedata.normalize('NFKD', input_str)
    return u"".join([c for c in nfkd_form if not unicodedata.combining(c)])

def rentree_scolaire():
    rentree = datetime.datetime.now(tz=timezone.utc)
    unjour = datetime.timedelta(days=1)
    while rentree.month!=8 or rentree.day!=27:
        rentree -= unjour
    return rentree

def index(request):
    return render(request,'index.html')


def upload_eleves(request):

    def remove_space(nom_init):
        nom=nom_init
        while nom[0]==' ':
            nom=nom[1:]
        while nom[-1]==' ':
            nom=nom[:-1]
        return nom

    if request.method == 'POST':
        if 'upload_eleves' in request.POST:
            new_persons = request.FILES['myfile']
            imported_data = new_persons.read().decode("utf-8")
            lignes = imported_data.split("\n")
            for ligne1 in lignes[1:-1]:
                ligne=ligne1.split(';')
                mail=remove_space(ligne[3])
                nom=remove_space(ligne[1])
                prenom=remove_space(ligne[2])
                #La façon dont sont générés les mots de passe est disponible en ligne, il faut donc absolument les modifier.
                user = Utilisateur.objects.create_user(username=mail, email=mail, first_name=prenom, last_name=nom, \
                                                       password=nom.replace('-','').replace("'","").replace(' ','')[0:6].lower() \
                                                                +prenom.replace('-','').replace("'","").replace(' ','')[0:2].lower()\
                                                       , is_student=True)
                etudiant = Etudiant(user=user, annee='PTSI', lv1=langue_vivante.objects.get(langue='Anglais'))
                etudiant.save()
        elif 'upload_ds' in request.POST:
            new_persons = request.FILES['myfile']
            imported_data = new_persons.read().decode("iso8859-1")
            lignes = imported_data.split("\n")
            print(imported_data[0])
        return render(request, 'simple_upload.html',{'done': True})
    return render(request, 'simple_upload.html')

def afficher_systeme(request, id_systeme):
    systeme_a_afficher=systeme.objects.get(id=id_systeme)
    courss=cours.objects.filter(systeme=systeme_a_afficher)
    tds=td.objects.filter(systeme=systeme_a_afficher)
    ilots=ilot.objects.filter(systeme=systeme_a_afficher)
    kholes=khole.objects.filter(systeme=systeme_a_afficher)
    dss=DS.objects.filter(sujet_support__systeme=systeme_a_afficher)
    parametres=parametre.objects.filter(systeme=systeme_a_afficher)
    fichiers=fichier_systeme.objects.filter(systeme=systeme_a_afficher)
    images=image_systeme.objects.filter(systeme=systeme_a_afficher)
    utilise=False
    if len(courss)+len(tds)+len(ilots)+len(kholes)+len(dss)>0:
        utilise=True
    return render(request, 'systeme.html', {'systeme':systeme_a_afficher, 'courss':courss, 'tds':tds,\
                                            'ilots':ilots,'kholes':kholes,'dss':dss,'utilise':utilise, 'parametres':parametres,\
                                            'exist_parametre':len(parametres)>0, 'fichiers':fichiers,\
                                            'exist_fichier':len(fichiers)>0, 'images':images,\
                                            'exist_image':len(images)>0
        })


def lister_ressources_si(request):
    sequences=sequence.objects.all()
    return render(request, 'sequences.html', {'sequences':sequences, 'si':True})

def lister_ressources_info(request):
    sequences=sequence_info.objects.all()
    dossier_ds = github + 'Informatique/raw/main/DS/'
    return render(request, 'sequences.html', {'sequences':sequences, 'dossier_ds':dossier_ds, 'info':True})

def lister_ds_si(request):
    dss=DS.objects.all()
    liste_ds=[]
    annee=[str(dss[0].annee()),[]]
    for ds in dss:
        if str(ds.annee())!=annee[0]:
            liste_ds.append(annee)
            annee=[str(ds.annee()),[]]
        annee[1].append(ds)
    liste_ds.append(annee)
    return render(request, 'annales_ds.html', {'liste_ds':liste_ds, 'si':True})

def afficher_sequence_si(request, id_sequence):
    sequence_a_afficher=sequence.objects.get(numero=id_sequence)
    courss=cours.objects.filter(sequence__numero=id_sequence)
    videos=video.objects.filter(ressource__sequence__numero=id_sequence)
    tds=td.objects.filter(sequence__numero=id_sequence)
    tps=tp.objects.filter(sequence__numero=id_sequence)
    liste_ilots=[]
    for tp_one in tps:
        ilots=ilot.objects.filter(tp=tp_one)
        #print(ilots[0].systeme.nom)
        liste_ilots.append([tp_one,ilots])
    kholes=khole.objects.filter(sequence__numero=id_sequence)
    quizzes=Quiz.objects.filter(category__category__startswith="SI-S%02d" % id_sequence)
    return render(request, 'sequence.html', {'sequence':sequence_a_afficher,'courss':courss,'tds':tds,'tps':liste_ilots,'kholes':kholes,'quizzes':quizzes,'videos':videos,'si':True})

def afficher_sequence_videos(request, id_sequence):
    sequence_a_afficher=sequence.objects.get(numero=id_sequence)
    videos=video.objects.filter(ressource__sequence=sequence_a_afficher)
    type_page='la séquence '+sequence_a_afficher.str_numero()+': '+sequence_a_afficher.nom
    return render(request, 'videos.html',{'sequence':sequence_a_afficher,'videos':videos,'type_page':type_page})

def afficher_ressource_videos(request, id_sequence, id_ressource):
    sequence_a_afficher=sequence.objects.get(numero=id_sequence)
    ressource_a_afficher=ressource.objects.get(id=id_ressource)
    videos=video.objects.filter(ressource=id_ressource)
    type_page='le '+ressource_a_afficher.type_de_ressource()[0]+' '+ressource_a_afficher.str_numero()+': '+ressource_a_afficher.nom
    return render(request, 'videos.html',{'sequence':sequence_a_afficher,'ressource':ressource_a_afficher,'videos':videos,'type_page':type_page})

def afficher_sequence_info(request, id_sequence):
    sequence_a_afficher=sequence_info.objects.get(id=id_sequence)
    courss=cours_info.objects.filter(sequence=id_sequence)
    tds=td_info.objects.filter(sequence=id_sequence)
    tps=tp_info.objects.filter(sequence=id_sequence)
    quizzes=Quiz.objects.filter(category__category="Info-S%02d" % id_sequence)
    return render(request, 'sequence.html', {'sequence':sequence_a_afficher,'courss':courss,'tds':tds,'tps':tps,'quizzes':quizzes,'info':True})


def lister_competences(request):
    competences=famille_competence.objects.all()
    return render(request, 'competences.html', {'competences':competences})


def afficher_famille_competence(request, id_famille):
    famille=famille_competence.objects.get(id=id_famille)
    competence_a_afficher=competence.objects.filter(famille=id_famille)
    return render(request, 'competence.html', {'famille':famille,'competences':competence_a_afficher})

def afficher_competence(request, id_famille, id_competence):
    famille=famille_competence.objects.get(id=id_famille)
    competence_a_afficher=competence.objects.get(id=id_competence)
    courss=cours.objects.filter(competence=id_competence)
    tds=td.objects.filter(competence=id_competence)
    tps=tp.objects.filter(competence=id_competence)
    kholes=khole.objects.filter(competence=id_competence)
    notes=Note.objects.filter(competence=id_competence).values('ds','numero')
    liste_notes=[]
    liste_ds=[]
    for note in notes:
        if str(note['ds']) not in liste_ds:
            liste_ds.append(str(note['ds']))
            liste_notes.append([DS.objects.get(id=note['ds']),[]])
        idx=liste_ds.index(str(note['ds']))
        if str(note['numero']) not in liste_notes[idx][1]:
            liste_notes[idx][1].append(str(note['numero']))
    for ds in liste_notes:
        ds[1]=','.join(ds[1])
    if request.user.is_authenticated:
        if request.user.is_student:
            etudiant=Etudiant.objects.get(user=request.user)
            chart_afficher=CompetenceChart(etudiant,competence_a_afficher)
        else:
            chart_afficher=False
    else:
        chart_afficher=False
    return render(request, 'competence_seule.html', {'chart':chart_afficher ,'famille':famille,'competence':competence_a_afficher,\
                                    'courss':courss,'tds':tds,'tps':tps,'kholes':kholes,'dss':liste_notes})


class CompetenceChart(Chart):
    chart_type = 'line'

    def __init__(self, etudiant,competence):
        Chart.__init__(self)
        notes_eleve=Note.objects.filter(competence=competence).filter(etudiant=etudiant).values('ds__date','ds','numero','value')
        self.liste_note=[]
        self.liste_date=[]
        for note in notes_eleve:
            self.liste_note.append(note['value'])
            self.liste_date.append(str(note['ds__date'])+' ('+str(note['numero'])+')')
        self.nom_dataset=competence.nom

    def get_labels(self):
        return self.liste_date

    def get_datasets(self, **kwargs):
        return [DataSet(label=self.nom_dataset,
                        color=(64, 135, 196),
                        data=self.liste_note)]


@login_required(login_url='/accounts/login/')
def resultats_vierge(request):
    etudiants = Etudiant.objects.filter(user__date_joined__gte=rentree_scolaire()).values('user')[0]['user']
    return redirect('/resultats/'+str(etudiants)+'/')

@login_required(login_url='/accounts/login/')
def resultats_quizz(request):
    #sittings=Sitting.objects.all().order_by('user')
    eleves=Etudiant.objects.filter(annee='PTSI').select_related('progress')\
        .values('user__last_name','user__first_name', 'user__progress__score').order_by('user__last_name','user__first_name')
    categories=Category.objects.all()
    cats=[]
    for categorie in categories:
        cats.append(categorie.category)
    notes_triees=[]
    for eleve in eleves:
        notes=str(eleve['user__progress__score']).split(',')[:-1]
        notes_triees_eleve=[['#FFFFFF','-/-'] for i in range(len(cats))]
        for i in range(len(notes)//3):
            test_col=float(notes[3*i+1])/float(notes[3*i+2])
            if test_col<0.3:
                color='#f01547'
            elif test_col >=0.3 and test_col<0.7:
                color='#ff5733'
            elif test_col>=0.7:
                color='#3dd614'
            notes_triees_eleve[cats.index(notes[3*i])]=[color,str(notes[3*i+1])+'/'+str(notes[3*i+2])]
        notes_triees.append([eleve['user__last_name'].replace(' "','').replace('" ','').replace('"',''), \
                             eleve['user__first_name'].replace(' "','').replace('" ','').replace('"',''),notes_triees_eleve])
    context = {
    'notes_triees':notes_triees, 'cats':cats
    }
    return render(request, 'resultats_quizz.html', context)

@login_required(login_url='/accounts/login/')
def resultats_quizz_eleve(request):
    progres=Progress.objects.get(user=request.user)
    categories=Category.objects.all()
    cats=[]
    for categorie in categories:
        cats.append(categorie.category)
    notes_triees=[]
    notes=str(progres.score).split(',')[:-1]
    notes_triees_eleve=[['#FFFFFF','-/-'] for i in range(len(cats))]
    for i in range(len(notes)//3):
        test_col=float(notes[3*i+1])/float(notes[3*i+2])
        if test_col<0.3:
            color='#f01547'
        elif test_col >=0.3 and test_col<0.7:
            color='#ff5733'
        elif test_col>=0.7:
            color='#3dd614'
        notes_triees_eleve[cats.index(notes[3*i])]=[color,str(notes[3*i+1])+'/'+str(notes[3*i+2])]
    print(notes_triees_eleve)
    notes_triees.append([request.user.first_name,request.user.last_name,notes_triees_eleve])
    context = {
    'notes_triees':notes_triees, 'cats':cats
    }
    return render(request, 'resultats_quizz.html', context)

@login_required(login_url='/accounts/login/')
def ds_eleve(request, id_etudiant):
    if request.user.is_teacher or (request.user.is_student and request.user.id==id_etudiant):
        dss=Note.objects.filter(etudiant=id_etudiant).values('ds').order_by('ds').distinct()
    else:
        return render(request, '/index')

    liste_ds=[]
    for ds in dss:
        ds=DS.objects.get(id=ds['ds'])
        liste_ds.append([ds,ds.notes_eleve_liste(id_etudiant),range(1,len(ds.notes_eleve_liste(id_etudiant))+1),\
                         ds.coefficients_liste(),ds.parties_liste(),ds.note_eleve(id_etudiant),ds.classement_eleve(id_etudiant)])
    context = {
        'chart': DetailsCharts(id_etudiant), 'liste_ds': liste_ds, 'ds': True,
    }

    return render(request, 'resultats.html', context)

@login_required(login_url='/accounts/login/')
def resultats(request, id_etudiant):
    if request.user.is_teacher or (request.user.is_student and request.user.id==id_etudiant):
        context = {
            'chart': ResultatsCharts(id_etudiant), 'general': True,
        }
        return render(request, 'resultats.html', context)
    else:
        return render(request, '/index')

@login_required(login_url='/accounts/login/')
def details(request, id_etudiant):
    if request.user.is_teacher or (request.user.is_student and request.user.id==id_etudiant):
        context = {
           'chart': DetailsCharts(id_etudiant), 'details': True,
        }
        return render(request, 'resultats.html', context)
    else:
        return render(request, '/index')
    
class Round(Func):
    function = 'ROUND'
    arity = 2


class ResultatsCharts(Chart):

    chart_type = 'radar'
    options = {
        'scale': {'ticks': {
                'suggestedMin': 0,
                'suggestedMax': 5,
                'stepSize': 1,

            }}
    }
    def __init__(self, id_etudiant):
        Chart.__init__(self)
        self.etudiants = Etudiant.objects.filter(user__date_joined__gte=rentree_scolaire()).values('user','user__last_name', 'user__first_name')
        self.etudiant_note = Etudiant.objects.filter(user=id_etudiant).values('user','user__last_name', 'user__first_name')
        notes_glob = Note.objects.filter(etudiant=id_etudiant).exclude(value=9).exclude(competence=0)\
            .values('competence__famille__nom').annotate(moyenne=Round(Avg('value'),2))\
            .order_by('competence__famille__nom')
        notes_glob_classe = Note.objects.filter(etudiant__user__date_joined__gte=rentree_scolaire()).exclude(value=9).exclude(competence=0)\
            .values('competence__famille__nom').annotate(moyenne=Round(Avg('value'),2))\
            .order_by('competence__famille__nom')

        self.liste_label=[]
        self.notes_eleve=[]
        self.notes_classe=[]

        for note in notes_glob_classe:
            self.liste_label.append(note['competence__famille__nom'])
            self.notes_classe.append(note['moyenne'])

        index=0

        for note in notes_glob:
            while note['competence__famille__nom']!=self.liste_label[index]:
                self.notes_eleve.append(0)
                index+=1
            self.notes_eleve.append(note['moyenne'])
            index+=1

    def get_options(self):
        options = {
            "scale": {
                "display": False,
                "ticks": {
                    "minDataValue": 0,
                    "maxDataValue": 5
                }
            }
        }
        return options

    def get_notes_glob(self):
        return zip(self.liste_label,self.notes_eleve,self.notes_classe)

    def get_labels(self):
        return self.liste_label

    def get_etudiant_note(self):
        return self.etudiant_note

    def get_etudiants(self):
        return self.etudiants

    def get_datasets(self, **kwargs):
        return [DataSet(label="Elève",
                        color=(64 , 135, 196),
                        data=self.notes_eleve),
                DataSet(label="Classe",
                        color=(179, 181, 198),
                        data=self.notes_classe)]

class DetailsCharts(Chart):
    chart_type = 'bar'
    options= {
            "scales": {
                "yAxes": [{
                    "ticks": {
                        "suggestedMin": 0,
                        "suggestedMax": 5
                    }
                }]
            }
    }

    def __init__(self, id_etudiant):
        Chart.__init__(self)
        self.etudiants = Etudiant.objects.filter(user__date_joined__gte=rentree_scolaire()).values('user','user__last_name', 'user__first_name')
        self.etudiant_note = Etudiant.objects.filter(user=id_etudiant).values('user','user__last_name', 'user__first_name')
        notes = Note.objects.filter(etudiant__user=id_etudiant).exclude(value=9).exclude(competence=0)\
            .values('competence', 'competence__famille', 'competence__nom', 'competence__reference', 'competence__famille__nom')\
            .annotate(moyenne=Round(Avg('value'),2)).order_by('competence__reference')
        notes_toute_classe = Note.objects.filter(etudiant__user__date_joined__gte=rentree_scolaire())\
            .exclude(value=9).exclude(competence=0).values('competence', 'competence__famille', 'competence__nom', 'competence__reference', 'competence__famille__nom')\
            .annotate(moyenne=Round(Avg('value'),2)).order_by('competence__reference')
        self.liste_label=[]
        self.liste_comp=[]
        self.notes_eleve=[]
        self.notes_classe=[]

        for note in notes_toute_classe:
            self.liste_comp.append([note['competence'],note['competence__famille'],note['competence__reference'],note['competence__nom'],"","danger"])
            self.liste_label.append(note['competence__reference'])
            self.notes_classe.append(note['moyenne'])

        index=0

        for note in notes:
            while note['competence']!=self.liste_comp[index][0]:
                self.liste_comp[index][4]=0
                self.notes_eleve.append(0)
                index+=1
            if note['moyenne']!=None:
                if float(note['moyenne'])>3.5:
                    self.liste_comp[index][5]="success"
                elif float(note['moyenne'])>1.5:
                    self.liste_comp[index][5]="warning"
                self.notes_eleve.append(note['moyenne'])
                self.liste_comp[index][4]=note['moyenne']
            index+=1

    def get_liste_comp(self):
        return self.liste_comp

    def get_etudiant_note(self):
        return self.etudiant_note

    def get_etudiants(self):
        return self.etudiants

    def get_notes_glob(self):
        return zip(self.liste_label,self.notes_eleve,self.notes_classe)

    def get_labels(self):
        return self.liste_label

    def get_datasets(self, **kwargs):
        return [DataSet(label="Elève",
                        color=(64 , 135, 196),
                        data=self.notes_eleve),
                DataSet(label="Classe",
                        color=(179, 181, 198),
                        data=self.notes_classe)]

def relative_url_view(request, nomquiz, action, year, month, day, ext, nom):
    return redirect('/static/uploads/'+year+'/'+month+'/'+day+'/'+nom+'.'+ext)

def relative_url_view_systeme(request, ext, nom, id_systeme, action):
    return redirect('/static/systemes/'+nom+'.'+ext)

def contact(request):
    # if this is a POST request we need to process the form data
    if request.method == 'POST':
        # create a form instance and populate it with data from the request:
        form = ContactForm(request.POST)
        # check whether it's valid:
        if form.is_valid():
            subject = form.cleaned_data['subject']
            message = form.cleaned_data['message']
            sender = form.cleaned_data['sender']
            cc_myself = form.cleaned_data['cc_myself']

            recipients = ['costadoat@crans.org']
            if cc_myself:
                recipients.append(sender)
            if subject and message and sender:
                send_mail('[Costadoat.fr] '+subject, message, sender, recipients)
                return HttpResponseRedirect('/thanks/')

    # if a GET (or any other method) we'll create a blank form
    else:
        if request.user.is_authenticated:
            form = ContactForm(initial={'sender': request.user.email})
        else:
            form = ContactForm()
    return render(request, 'contact.html', {'form': form, 'thanks': False})

def thanks(request):
    return render(request, 'contact.html', {'thanks': True})

def afficher_sysml(request,id_systeme):
    return render(request, 'sysml.html', {'thanks': True, 'id_systeme':id_systeme})

def relative_url_sysml(request, id_systeme, dossier, data):
    nom_systeme=systeme.objects.get(id=id_systeme)
    return redirect(remove_accents('https://github.com/Costadoat/Sciences-Ingenieur/raw/master/Systemes/'+str(nom_systeme)+'/SysMl/'+dossier+'/'+data))


def relative_url_image_sysml(request, id_systeme, data):
    return redirect('/static/sysml_player/images/'+data)

def afficher_data_js(request, id_systeme):
    nom_systeme=systeme.objects.get(id=id_systeme)
    url=remove_accents('https://raw.githubusercontent.com/Costadoat/Sciences-Ingenieur/master/Systemes/'+str(nom_systeme)+'/SysMl/data.js')
    return HttpResponse(urlopen(url).read())

@login_required(login_url='/accounts/login/')
def fiche_ressource_edit(request,id_sequence,id_ressource,id_etudiant=None):
    fiche = fiche_synthese.objects.get(ressource__id=id_ressource)
    items=item_synthese.objects.filter(fiche_synthese=fiche)
    number=len(items)
    if request.user.is_authenticated:
        if request.user.is_student or (request.user.is_teacher and id_etudiant!=None):
            if id_etudiant==None:
                etudiant=Etudiant.objects.get(user=request.user)
            else:
                etudiant=Etudiant.objects.get(user__id=id_etudiant)
            # if this is a POST request we need to process the form data
            if request.method == 'POST':
                # create a form instance and populate it with data from the request:
                form = ReponseItemSyntheseForm(request.POST,fiche=fiche)
                if form.is_valid():
                    for i in range(number):
                        reponse=reponse_item_synthese.objects.update_or_create(item_synthese=items[i],etudiant=etudiant,\
                            defaults={'reponse':form[items[i].reference()].value() },)
            else:
                reponses=reponse_item_synthese.objects.filter(item_synthese__fiche_synthese=fiche,etudiant=etudiant)
                mes_reponses={}
                for reponse in reponses:
                    mes_reponses[str(reponse.item_synthese.reference())]=str(reponse.reponse)
                form = ReponseItemSyntheseForm(initial=mes_reponses,fiche=fiche)
            return render(request, 'fiche_synthese.html', {'Fiche': fiche,'Form': form, 'edit': True})
        elif request.user.is_teacher:
            return redirect('.')
    else:
        return redirect('/accounts/login/')


@login_required(login_url='/accounts/login/')
def generer_fiche_synthese(request,id_sequence,id_ressource,id_etudiant=None):
    fiche = fiche_synthese.objects.get(ressource__sequence__id=id_sequence,ressource__numero=id_ressource)
    items=item_synthese.objects.filter(fiche_synthese=fiche)
    if request.user.is_authenticated:
        if request.user.is_student:
            utilisateur=Etudiant.objects.get(user=request.user)
        elif request.user.is_teacher:
            if id_etudiant!=None:
                utilisateur=Etudiant.objects.get(user__id=id_etudiant)
            else:
                utilisateur=Professeur.objects.get(user=request.user)
        fiche_display=[]
        for item in items:
            if request.user.is_student:
                if reponse_item_synthese.objects.filter(item_synthese=item,etudiant=utilisateur):
                    reponse=reponse_item_synthese.objects.get(item_synthese=item,etudiant=utilisateur)
                else:
                    reponse=None
            elif request.user.is_teacher:
                if id_etudiant==None:
                    reponse=item
                else:
                    reponse=reponse_item_synthese.objects.get(item_synthese=item,etudiant__user__id=id_etudiant)
            fiche_display.append([item,reponse])
        context={'Fiche': fiche,'Items': fiche_display, 'edit': False,'Utilisateur': utilisateur, 'prof_etudiant':(id_etudiant!=None)}
        return fiche,context
    else:
        return render(request, '/accounts/login/')

@login_required(login_url='/accounts/login/')
def fiche_ressource_display(request,id_sequence,id_ressource,id_etudiant=None):
    fiche,context=generer_fiche_synthese(request,id_sequence,id_ressource,id_etudiant)
    return render(request, 'fiche_synthese.html', context)

@login_required(login_url='/accounts/login/')
def generer_fiche_synthese_PDF(request,id_sequence,id_ressource,id_etudiant=None):
    fiche,context=generer_fiche_synthese(request,id_sequence,id_ressource,id_etudiant)
    template_name = 'fiche_pdf_template.tex'
    return render_to_pdf(request, template_name, context, filename='test.pdf')

@login_required(login_url='/accounts/login/')
def gen_liste_fiches_ressource_eleve(eleve):
    les_fiches=[]
    fiches = fiche_synthese.objects.all()
    for fiche in fiches:
        vide=True
        reponses = reponse_item_synthese.objects.filter(etudiant=eleve,item_synthese__fiche_synthese=fiche)
        for reponse in reponses:
            if reponse.reponse!="":
                vide=False
        les_fiches.append([fiche,reponses,vide])
    context = {'Fiches': les_fiches}
    return context, les_fiches

@login_required(login_url='/accounts/login/')
def liste_fiches_ressource(request, *args):
    if request.user.is_authenticated:
        if request.user.is_student:
            utilisateur=Etudiant.objects.get(user=request.user)
            context=gen_liste_fiches_ressource_eleve(utilisateur)[0]
            return render(request, 'liste_fiches.html', context)
        elif request.user.is_teacher:
            eleves=Etudiant.objects.filter(annee='PTSI').order_by('user__last_name','user__first_name')
            les_fiches=[]
            for eleve in eleves:
                la_fiche=gen_liste_fiches_ressource_eleve(eleve)[1]
                les_fiches.append([eleve,la_fiche])
            context = {'Eleves': les_fiches}
            return render(request, 'liste_fiches_prof.html', context)
        else:
            return render(request, '/accounts/login/')
    else:
        return render(request, '/accounts/login/')

