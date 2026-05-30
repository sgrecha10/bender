from django.contrib import messages
from django.http.response import HttpResponseRedirect
from django.urls import reverse
from django.utils.html import format_html


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


def colored_status_display(obj):
    colors = {
        obj.Status.PENDING: '#b08968',
        obj.Status.PROCESSING: '#6c8ebf',
        obj.Status.SUCCESS: '#6a994e',
        obj.Status.FAILED: '#b56576',
    }

    return format_html(
        '<span style="background:{}; color:white; '
        'padding:3px 8px; border-radius:6px;">{}</span>',
        colors.get(obj.status, '#666'),
        obj.get_status_display(),
    )
