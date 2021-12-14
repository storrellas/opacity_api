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
    seller_sku = models.CharField(max_length=100)
    asin = models.CharField(max_length=100)
    name = models.CharField(max_length=100)
    listing_id = models.CharField(max_length=100)
    status = models.CharField(max_length=100)
    variant_type = models.CharField(max_length=100)
    category1 = models.CharField(max_length=100)
    category2 = models.CharField(max_length=100)
    product_type = models.CharField(max_length=100)
    color_size = models.CharField(max_length=100)
    custom_label0 = models.CharField(max_length=100)
    custom_label1 = models.CharField(max_length=100)
    custom_label2 = models.CharField(max_length=100)
    custom_label3 = models.CharField(max_length=100)
    custom_label4 = models.CharField(max_length=100)
    
    def __str__(self):
        return "%s" % self.name


