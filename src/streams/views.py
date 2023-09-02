from django.shortcuts import render
from django.views.generic.base import View
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect, Http404, HttpResponseBadRequest


class HandlerTestView(View):
    def get(self, request):
        return HttpResponse('Запустили.. <a href="/admin">admin</a>')
