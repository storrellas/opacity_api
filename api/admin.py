import json
import logging

from django.contrib import admin
from django.forms import widgets
from django.db.models import JSONField 

from .models import Company, Product

logger = logging.getLogger(__name__)


class PrettyJSONWidget(widgets.Textarea):

    def format_value(self, value):
        try:
            value = json.dumps(json.loads(value), indent=2, sort_keys=True)
            # these lines will try to adjust size of TextArea to fit to content
            row_lengths = [len(r) for r in value.split('\n')]
            self.attrs['rows'] = min(max(len(row_lengths) + 2, 10), 30)
            self.attrs['cols'] = min(max(max(row_lengths) + 2, 40), 120)
            return value
        except Exception as e:
            logger.warning("Error while formatting JSON: {}".format(e))
            return super(PrettyJSONWidget, self).format_value(value)

# Register your models here.
@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
  formfield_overrides = {
    JSONField: {'widget': PrettyJSONWidget}
  }

# Register your models here.
@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
  list_display = ('seller_sku', 'asin', 'listing_id', 'company')
  ordering = ('seller_sku',)
  list_filter = ["company",]