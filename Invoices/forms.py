from django import forms
from django.forms import inlineformset_factory
from .models import Proposal, Invoice, LineItem, ServicePreset


# ─────────────────────────────────────────
# SHARED WIDGET STYLES
# ─────────────────────────────────────────
INPUT_CLASS  = 'w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500'
SELECT_CLASS = 'w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white'
DATE_CLASS   = 'w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500'
TEXTAREA_CLASS = 'w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500'


# ─────────────────────────────────────────
# PROPOSAL FORM
# ─────────────────────────────────────────
class ProposalForm(forms.ModelForm):

    class Meta:
        model  = Proposal
        fields = [
            'lead', 'title', 'status',
            'issue_date', 'valid_until',
            'discount', 'notes',
        ]
        # gst_percentage intentionally excluded (hidden until registration)
        widgets = {
            'lead':        forms.Select(attrs={'class': SELECT_CLASS}),
            'title':       forms.TextInput(attrs={'class': INPUT_CLASS, 'placeholder': 'e.g. Social Media + SEO Package'}),
            'status':      forms.Select(attrs={'class': SELECT_CLASS}),
            'issue_date':  forms.DateInput(attrs={'class': DATE_CLASS, 'type': 'date'}),
            'valid_until': forms.DateInput(attrs={'class': DATE_CLASS, 'type': 'date'}),
            'discount':    forms.NumberInput(attrs={'class': INPUT_CLASS, 'placeholder': '0', 'min': '0'}),
            'notes':       forms.Textarea(attrs={'class': TEXTAREA_CLASS, 'rows': 3, 'placeholder': 'Any additional notes for the client...'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Show lead as "First Last" in dropdown
        from Leads.models import Lead
        self.fields['lead'].queryset = Lead.objects.all().order_by('first_name')
        self.fields['lead'].label_from_instance = lambda obj: f"{obj.first_name} {obj.last_name}"
        self.fields['discount'].required = False
        self.fields['notes'].required    = False


# ─────────────────────────────────────────
# INVOICE FORM
# ─────────────────────────────────────────
class InvoiceForm(forms.ModelForm):

    class Meta:
        model  = Invoice
        fields = [
            'lead', 'title', 'payment_status',
            'issue_date', 'due_date',
            'discount', 'amount_paid', 'notes',
        ]
        # gst_percentage intentionally excluded (hidden until registration)
        widgets = {
            'lead':           forms.Select(attrs={'class': SELECT_CLASS}),
            'title':          forms.TextInput(attrs={'class': INPUT_CLASS, 'placeholder': 'e.g. Social Media Management — March'}),
            'payment_status': forms.Select(attrs={'class': SELECT_CLASS}),
            'issue_date':     forms.DateInput(attrs={'class': DATE_CLASS, 'type': 'date'}),
            'due_date':       forms.DateInput(attrs={'class': DATE_CLASS, 'type': 'date'}),
            'discount':       forms.NumberInput(attrs={'class': INPUT_CLASS, 'placeholder': '0', 'min': '0'}),
            'amount_paid':    forms.NumberInput(attrs={'class': INPUT_CLASS, 'placeholder': '0', 'min': '0'}),
            'notes':          forms.Textarea(attrs={'class': TEXTAREA_CLASS, 'rows': 3, 'placeholder': 'Payment instructions or notes...'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from Leads.models import Lead
        self.fields['lead'].queryset = Lead.objects.all().order_by('first_name')
        self.fields['lead'].label_from_instance = lambda obj: f"{obj.first_name} {obj.last_name}"
        self.fields['discount'].required    = False
        self.fields['amount_paid'].required = False
        self.fields['notes'].required       = False


# ─────────────────────────────────────────
# LINE ITEM FORM
# ─────────────────────────────────────────
class LineItemForm(forms.ModelForm):

    class Meta:
        model  = LineItem
        fields = ['service_preset', 'description', 'quantity', 'unit_price', 'order']
        widgets = {
            'service_preset': forms.Select(attrs={
                'class': SELECT_CLASS + ' service-preset-select',
                'onchange': 'fillFromPreset(this)',
            }),
            'description': forms.TextInput(attrs={
                'class': INPUT_CLASS + ' line-description',
                'placeholder': 'Service description',
            }),
            'quantity': forms.NumberInput(attrs={
                'class': INPUT_CLASS + ' line-qty',
                'placeholder': '1', 'min': '0.01', 'step': '0.01',
                'oninput': 'recalcRow(this)',
            }),
            'unit_price': forms.NumberInput(attrs={
                'class': INPUT_CLASS + ' line-price',
                'placeholder': '0.00', 'min': '0',
                'oninput': 'recalcRow(this)',
            }),
            'order': forms.HiddenInput(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['service_preset'].queryset = ServicePreset.objects.filter(is_active=True)
        self.fields['service_preset'].required = False
        self.fields['service_preset'].empty_label = '— Select service —'


# ─────────────────────────────────────────
# INLINE FORMSETS
# ─────────────────────────────────────────
ProposalLineItemFormSet = inlineformset_factory(
    Proposal, LineItem,
    form=LineItemForm,
    fields=['service_preset', 'description', 'quantity', 'unit_price', 'order'],
    extra=1,
    can_delete=True,
    fk_name='proposal',
)

InvoiceLineItemFormSet = inlineformset_factory(
    Invoice, LineItem,
    form=LineItemForm,
    fields=['service_preset', 'description', 'quantity', 'unit_price', 'order'],
    extra=1,
    can_delete=True,
    fk_name='invoice',
)