from django.contrib import messages
from django.http.response import HttpResponseRedirect
from django.urls import reverse


def redirect_to_change_list(request, model, message=None, is_ok=True):
    if message:
        if is_ok:
            messages.success(request, message)
        else:
            messages.warning(request, message)
    meta = model._meta
    url = reverse(f'admin:{meta.app_label}_{meta.model_name}_changelist')
    return HttpResponseRedirect(url)

def redirect_to_change_form(model, pk):
    meta = model._meta
    url = reverse(f'admin:{meta.app_label}_{meta.model_name}_change', args=(pk,))
    return HttpResponseRedirect(url)
