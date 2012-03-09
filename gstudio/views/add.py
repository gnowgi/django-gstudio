"""Views for Gstudio forms"""
from django.http import HttpResponse
from django.http import HttpResponseRedirect
from django.template import RequestContext
from django.shortcuts import render_to_response
from datetime import datetime
from gstudio.forms import *


def addmetatype(request):
    if request.method == 'POST':
        formset = MetatypeForm(request.POST)
        if formset.is_valid():
            formset.save()
            return HttpResponseRedirect("/gstudio/")
 
 
        
    else:
       
        formset = MetatypeForm()


    variables = RequestContext(request,{'formset':formset})
    template = "gstudioforms/gstudiometatypeform.html"
    return render_to_response(template, variables)

    
    
def addobjecttype(request):
        if request.method == 'POST':
            formset = ObjecttypeForm(request.POST)
            if formset.is_valid():
                formset.save()
                return HttpResponseRedirect("/gstudio/")
 
            
                    
        else:

            formset = ObjecttypeForm()

        template = "gstudioforms/gstudioobjecttypeform.html"
        variables = RequestContext(request,{'formset':formset})
        return render_to_response(template, variables)

def addrelationtype(request):
        if request.method == 'POST':
            formset = RelationtypeForm(request.POST)
            if formset.is_valid():
                formset.save()
                return HttpResponseRedirect("/gstudio/")
            
                    
        else:

            formset = RelationtypeForm()

        template = "gstudioforms/gstudiorelationtypeform.html"
        variables = RequestContext(request,{'formset':formset})
        return render_to_response(template, variables)


def addattributetype(request):
        if request.method == 'POST':
            formset = AttributetypeForm(request.POST)
            if formset.is_valid():
                formset.save()
                return HttpResponseRedirect("/gstudio/")
            
                    
        else:

            formset = AttributetypeForm()

        template = "gstudioforms/gstudioattributetypeform.html"
        variables = RequestContext(request,{'formset':formset})
        return render_to_response(template, variables)


def addsystemtype(request):
        if request.method == 'POST':
            formset = SystemtypeForm(request.POST)
            if formset.is_valid():
                formset.save()
                return HttpResponseRedirect("/gstudio/")
            
                    
        else:

            formset = SystemtypeForm()

        template = "gstudioforms/gstudiosystemtypeform.html"
        variables = RequestContext(request,{'formset':formset})
        return render_to_response(template, variables)

def addprocesstype(request):
        if request.method == 'POST':
            formset = ProcesstypeForm(request.POST)
            if formset.is_valid():
                formset.save()
                return HttpResponseRedirect("/gstudio/")
            
                    
        else:

            formset = ProcesstypeForm()

        template = "gstudioforms/gstudioprocesstypeform.html"
        variables = RequestContext(request,{'formset':formset})
        return render_to_response(template, variables)

def addattribute(request):
        if request.method == 'POST':
            formset = AttributeForm(request.POST)
            if formset.is_valid():
                formset.save()
                return HttpResponseRedirect("/gstudio/")
            
                    
        else:

            formset = AttributeForm()

        template = "gstudioforms/gstudioattributeform.html"
        variables = RequestContext(request,{'formset':formset})
        return render_to_response(template, variables)

def addrelation(request):
        if request.method == 'POST':
            formset = RelationForm(request.POST)
            if formset.is_valid():
                formset.save()
                return HttpResponseRedirect("/gstudio/")
            
                    
        else:

            formset = RelationForm()

        template = "gstudioforms/gstudiorelationform.html"
        variables = RequestContext(request,{'formset':formset})
        return render_to_response(template, variables)

def addcomplement(request):
        if request.method == 'POST':
            formset = ComplementForm(request.POST)
            if formset.is_valid():
                formset.save()
                return HttpResponseRedirect("/gstudio/")
            
                    
        else:

            formset = ComplementForm()

        template = "gstudioforms/gstudiocomplementform.html"
        variables = RequestContext(request,{'formset':formset})
        return render_to_response(template, variables)

def addunion(request):
        if request.method == 'POST':
            formset = UnionForm(request.POST)
            if formset.is_valid():
                formset.save()
                return HttpResponseRedirect("/gstudio/")
            
                    
        else:

            formset = UnionForm()

        template = "gstudioforms/gstudiounionform.html"
        variables = RequestContext(request,{'formset':formset})
        return render_to_response(template, variables)

def addintersection(request):
        if request.method == 'POST':
            formset = IntersectionForm(request.POST)
            if formset.is_valid():
                formset.save()
                return HttpResponseRedirect("/gstudio/")
            
                    
        else:

            formset = IntersectionForm()

        template = "gstudioforms/gstudiointersectionform.html"
        variables = RequestContext(request,{'formset':formset})
        return render_to_response(template, variables)












