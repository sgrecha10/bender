from django.contrib import messages
from django.http.response import HttpResponseRedirect
from django.urls import reverse


def redirect_to_change_list(request, model, message=None):
    msg = message[0]
    if msg:
        if message[1]:
            messages.success(request, msg)
        else:
            messages.warning(request, msg)
    meta = model._meta
    url = reverse(f'admin:{meta.app_label}_{meta.model_name}_changelist')
    return HttpResponseRedirect(url)
