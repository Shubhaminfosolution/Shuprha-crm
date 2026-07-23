from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.db import transaction
import json

from .models import Proposal, Invoice, LineItem, ServicePreset
from .forms import ProposalForm, InvoiceForm, ProposalLineItemFormSet, InvoiceLineItemFormSet


# ─────────────────────────────────────────
# HELPER — service presets as JSON for JS
# ─────────────────────────────────────────
def get_presets_json():
    presets = ServicePreset.objects.filter(is_active=True).values('id', 'name', 'default_rate', 'description')
    return json.dumps(list(presets), default=str)


# ══════════════════════════════════════════
# PROPOSAL VIEWS
# ══════════════════════════════════════════

@login_required
def proposal_list(request):
    proposals = Proposal.objects.select_related('lead').all()

    # Filter by status
    status = request.GET.get('status')
    if status:
        proposals = proposals.filter(status=status)

    context = {
        'proposals':    proposals,
        'status_filter': status,
        'status_choices': Proposal.STATUS_CHOICES,
    }
    return render(request, 'templates/proposal_list.html', context)


@login_required
def proposal_create(request):
    if request.method == 'POST':
        form    = ProposalForm(request.POST)
        formset = ProposalLineItemFormSet(request.POST)

        if form.is_valid() and formset.is_valid():
            with transaction.atomic():
                proposal = form.save(commit=False)
                proposal.created_by = request.user
                proposal.save()

                formset.instance = proposal
                formset.save()

            messages.success(request, f'Proposal {proposal.proposal_number} created successfully.')
            return redirect('invoices:proposal_detail', pk=proposal.pk)
        else:
            messages.error(request, 'Please fix the errors below.')
    else:
        form    = ProposalForm()
        formset = ProposalLineItemFormSet()

    context = {
        'form':         form,
        'formset':      formset,
        'presets_json': get_presets_json(),
        'page_title':   'New Proposal',
        'form_action':  'Create Proposal',
    }
    return render(request, 'templates/proposal_form.html', context)


@login_required
def proposal_detail(request, pk):
    proposal = get_object_or_404(Proposal.objects.select_related('lead', 'created_by'), pk=pk)
    line_items = proposal.line_items.select_related('service_preset').all()

    context = {
        'proposal':   proposal,
        'line_items': line_items,
    }
    return render(request, 'templates/proposal_detail.html', context)


@login_required
def proposal_edit(request, pk):
    proposal = get_object_or_404(Proposal, pk=pk)

    if proposal.converted_to_invoice:
        messages.warning(request, 'This proposal has already been converted to an invoice and cannot be edited.')
        return redirect('invoices:proposal_detail', pk=pk)

    if request.method == 'POST':
        form    = ProposalForm(request.POST, instance=proposal)
        formset = ProposalLineItemFormSet(request.POST, instance=proposal)

        if form.is_valid() and formset.is_valid():
            with transaction.atomic():
                form.save()
                formset.save()

            messages.success(request, f'Proposal {proposal.proposal_number} updated.')
            return redirect('invoices:proposal_detail', pk=proposal.pk)
        else:
            messages.error(request, 'Please fix the errors below.')
    else:
        form    = ProposalForm(instance=proposal)
        formset = ProposalLineItemFormSet(instance=proposal)

    context = {
        'form':         form,
        'formset':      formset,
        'presets_json': get_presets_json(),
        'proposal':     proposal,
        'page_title':   f'Edit {proposal.proposal_number}',
        'form_action':  'Update Proposal',
    }
    return render(request, 'templates/proposal_form.html', context)


@login_required
def proposal_delete(request, pk):
    proposal = get_object_or_404(Proposal, pk=pk)

    if proposal.converted_to_invoice:
        messages.error(request, 'Cannot delete a proposal that has been converted to an invoice.')
        return redirect('invoices:proposal_detail', pk=pk)

    if request.method == 'POST':
        number = proposal.proposal_number
        proposal.delete()
        messages.success(request, f'Proposal {number} deleted.')
        return redirect('invoices:proposal_list')

    return render(request, 'templates/confirm_delete.html', {
        'object':       proposal,
        'object_type':  'Proposal',
        'cancel_url':   f'/templates/proposals/{pk}/',
    })


# ─────────────────────────────────────────
# CONVERT PROPOSAL → INVOICE
# ─────────────────────────────────────────
@login_required
def proposal_convert(request, pk):
    proposal = get_object_or_404(Proposal, pk=pk)

    if proposal.converted_to_invoice:
        messages.warning(request, 'This proposal is already converted to an invoice.')
        return redirect('invoices:invoice_detail', pk=proposal.invoice.pk)

    if request.method == 'POST':
        form    = InvoiceForm(request.POST)
        formset = InvoiceLineItemFormSet(request.POST)

        if form.is_valid() and formset.is_valid():
            with transaction.atomic():
                invoice = form.save(commit=False)
                invoice.proposal   = proposal
                invoice.created_by = request.user
                invoice.save()

                formset.instance = invoice
                formset.save()

                # Mark proposal as converted
                proposal.converted_to_invoice = True
                proposal.status = 'accepted'
                proposal.save()

            messages.success(request, f'Proposal converted to Invoice {invoice.invoice_number}.')
            return redirect('invoices:invoice_detail', pk=invoice.pk)
        else:
            messages.error(request, 'Please fix the errors below.')
    else:
        # Pre-fill invoice form from proposal data
        initial_data = {
            'lead':  proposal.lead,
            'title': proposal.title,
            'discount': proposal.discount,
            'notes': proposal.notes,
        }
        form = InvoiceForm(initial=initial_data)

        # Pre-fill line items from proposal
        existing_items = list(proposal.line_items.values(
            'service_preset', 'description', 'quantity', 'unit_price', 'order'
        ))
        from django.forms import inlineformset_factory
        from .forms import LineItemForm
        PrefilledFormSet = inlineformset_factory(
            Invoice, LineItem,
            form=LineItemForm,
            extra=len(existing_items) if existing_items else 1,
            can_delete=True,
            fk_name='invoice',
        )
        formset = PrefilledFormSet(initial=existing_items)

    context = {
        'form':         form,
        'formset':      formset,
        'presets_json': get_presets_json(),
        'proposal':     proposal,
        'page_title':   f'Convert {proposal.proposal_number} to Invoice',
        'form_action':  'Create Invoice',
        'is_convert':   True,
    }
    return render(request, 'templates/invoice_form.html', context)


# ══════════════════════════════════════════
# INVOICE VIEWS
# ══════════════════════════════════════════

@login_required
def invoice_list(request):
    invoices = Invoice.objects.select_related('lead', 'proposal').all()

    status = request.GET.get('status')
    if status:
        invoices = invoices.filter(payment_status=status)

    context = {
        'invoices':      invoices,
        'status_filter': status,
        'status_choices': Invoice.PAYMENT_STATUS,
    }
    return render(request, 'templates/invoice_list.html', context)


@login_required
def invoice_create(request):
    if request.method == 'POST':
        form    = InvoiceForm(request.POST)
        formset = InvoiceLineItemFormSet(request.POST)

        if form.is_valid() and formset.is_valid():
            with transaction.atomic():
                invoice = form.save(commit=False)
                invoice.created_by = request.user
                invoice.save()

                formset.instance = invoice
                formset.save()

            messages.success(request, f'Invoice {invoice.invoice_number} created successfully.')
            return redirect('invoices:invoice_detail', pk=invoice.pk)
        else:
            messages.error(request, 'Please fix the errors below.')
    else:
        form    = InvoiceForm()
        formset = InvoiceLineItemFormSet()

    context = {
        'form':         form,
        'formset':      formset,
        'presets_json': get_presets_json(),
        'page_title':   'New Invoice',
        'form_action':  'Create Invoice',
    }
    return render(request, 'templates/invoice_form.html', context)


@login_required
def invoice_detail(request, pk):
    invoice    = get_object_or_404(Invoice.objects.select_related('lead', 'proposal', 'created_by'), pk=pk)
    line_items = invoice.line_items.select_related('service_preset').all()

    context = {
        'invoice':    invoice,
        'line_items': line_items,
    }
    return render(request, 'templates/invoice_detail.html', context)


@login_required
def invoice_edit(request, pk):
    invoice = get_object_or_404(Invoice, pk=pk)

    if request.method == 'POST':
        form    = InvoiceForm(request.POST, instance=invoice)
        formset = InvoiceLineItemFormSet(request.POST, instance=invoice)

        if form.is_valid() and formset.is_valid():
            with transaction.atomic():
                form.save()
                formset.save()

            messages.success(request, f'Invoice {invoice.invoice_number} updated.')
            return redirect('invoices:invoice_detail', pk=invoice.pk)
        else:
            messages.error(request, 'Please fix the errors below.')
    else:
        form    = InvoiceForm(instance=invoice)
        formset = InvoiceLineItemFormSet(instance=invoice)

    context = {
        'form':        form,
        'formset':     formset,
        'presets_json': get_presets_json(),
        'invoice':     invoice,
        'page_title':  f'Edit {invoice.invoice_number}',
        'form_action': 'Update Invoice',
    }
    return render(request, 'templates/invoice_form.html', context)


@login_required
def invoice_delete(request, pk):
    invoice = get_object_or_404(Invoice, pk=pk)

    if request.method == 'POST':
        # Unmark proposal conversion if linked
        if invoice.proposal:
            invoice.proposal.converted_to_invoice = False
            invoice.proposal.save()

        number = invoice.invoice_number
        invoice.delete()
        messages.success(request, f'Invoice {number} deleted.')
        return redirect('invoices:invoice_list')

    return render(request, 'templates/confirm_delete.html', {
        'object':      invoice,
        'object_type': 'Invoice',
        'cancel_url':  f'/templates/invoices/{pk}/',
    })


# ─────────────────────────────────────────
# PDF DOWNLOAD (WeasyPrint)
# ─────────────────────────────────────────
@login_required
def proposal_pdf(request, pk):
    proposal   = get_object_or_404(Proposal.objects.select_related('lead'), pk=pk)
    line_items = proposal.line_items.select_related('service_preset').all()

    html_string = render_to_string('templates/pdf/proposal_pdf.html', {
        'proposal':   proposal,
        'line_items': line_items,
    })

    try:
        from weasyprint import HTML
        pdf_file = HTML(string=html_string, base_url=request.build_absolute_uri('/')).write_pdf()
        response = HttpResponse(pdf_file, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{proposal.proposal_number}.pdf"'
        return response
    except ImportError:
        return HttpResponse('WeasyPrint is not installed. Run: pip install weasyprint', status=500)


@login_required
def invoice_pdf(request, pk):
    invoice    = get_object_or_404(Invoice.objects.select_related('lead'), pk=pk)
    line_items = invoice.line_items.select_related('service_preset').all()

    html_string = render_to_string('templates/pdf/invoice_pdf.html', {
        'invoice':    invoice,
        'line_items': line_items,
    })

    try:
        from weasyprint import HTML
        pdf_file = HTML(string=html_string, base_url=request.build_absolute_uri('/')).write_pdf()
        response = HttpResponse(pdf_file, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{invoice.invoice_number}.pdf"'
        return response
    except ImportError:
        return HttpResponse('WeasyPrint is not installed. Run: pip install weasyprint', status=500) 