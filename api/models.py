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
