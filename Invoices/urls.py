from django.urls import path
from . import views

app_name = 'invoices'

urlpatterns = [

    # ── Proposals ─────────────────────────────────────────
    path('proposals/',                  views.proposal_list,    name='proposal_list'),
    path('proposals/new/',              views.proposal_create,  name='proposal_create'),
    path('proposals/<int:pk>/',         views.proposal_detail,  name='proposal_detail'),
    path('proposals/<int:pk>/edit/',    views.proposal_edit,    name='proposal_edit'),
    path('proposals/<int:pk>/delete/',  views.proposal_delete,  name='proposal_delete'),
    path('proposals/<int:pk>/convert/', views.proposal_convert, name='proposal_convert'),
    path('proposals/<int:pk>/pdf/',     views.proposal_pdf,     name='proposal_pdf'),

    # ── Invoices ──────────────────────────────────────────
    path('invoices/',                   views.invoice_list,     name='invoice_list'),
    path('invoices/new/',               views.invoice_create,   name='invoice_create'),
    path('invoices/<int:pk>/',          views.invoice_detail,   name='invoice_detail'),
    path('invoices/<int:pk>/edit/',     views.invoice_edit,     name='invoice_edit'),
    path('invoices/<int:pk>/delete/',   views.invoice_delete,   name='invoice_delete'),
    path('invoices/<int:pk>/pdf/',      views.invoice_pdf,      name='invoice_pdf'),

]