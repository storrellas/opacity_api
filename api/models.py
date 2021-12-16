from django.db import models
import uuid

from django.db import models

class BaseModel(models.Model):
    uuid = models.UUIDField( primary_key = True, default = uuid.uuid4, editable = False) 

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        abstract = True

class Company(BaseModel):
    name = models.CharField(max_length=100)
    ref = models.CharField(max_length=100)
    mappings = models.JSONField(blank=True, null=True)

    class Meta:
        verbose_name_plural = "companies"

    def __str__(self):
        return "%s" % self.name


class Product(BaseModel):
    COMMON_DENOMINATOR_LIST = ['category1', 'category2', 'product_type', \
                                'custom_label0', 'custom_label1', 'custom_label2', 'custom_label3', 'custom_label4']

    company = models.ForeignKey(Company, related_name='products', 
                                on_delete=models.SET_NULL, null=True)
    seller_sku = models.CharField(max_length=100, blank=True, null=True)
    asin = models.CharField(max_length=100, blank=True, null=True)
    name = models.CharField(max_length=500, blank=True, null=True)
    listing_id = models.CharField(max_length=100, blank=True, null=True)
    status = models.CharField(max_length=100, blank=True, null=True)
    variant_type = models.CharField(max_length=100, blank=True, null=True)
    category1 = models.CharField(max_length=100, blank=True, null=True)
    category2 = models.CharField(max_length=100, blank=True, null=True)
    product_type = models.CharField(max_length=100, blank=True, null=True)
    color = models.CharField(max_length=100, blank=True, null=True)
    size = models.CharField(max_length=100, blank=True, null=True)
    custom_label0 = models.CharField(max_length=100, blank=True, null=True)
    custom_label1 = models.CharField(max_length=100, blank=True, null=True)
    custom_label2 = models.CharField(max_length=100, blank=True, null=True)
    custom_label3 = models.CharField(max_length=100, blank=True, null=True)
    custom_label4 = models.CharField(max_length=100, blank=True, null=True)
    
    def __str__(self):
        return "%s" % self.seller_sku


