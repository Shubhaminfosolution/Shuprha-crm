import os
import django


os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Company.settings')
django.setup()

import tablib
from Leads.resources import LeadResource

with open(r'C:\Users\shubh\Downloads\Eval8_imp.csv', encoding='utf-8') as f:
    data = f.read()

dataset = tablib.Dataset().load(data, headers=True)
resource = LeadResource()
result = resource.import_data(dataset, dry_run=False, raise_errors=True)
print(f"Total rows: {result.total_rows}")
print(f"Invalid rows: {len(result.invalid_rows)}")