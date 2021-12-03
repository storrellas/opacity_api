from django.shortcuts import render

# Create your views here.
from rest_framework import viewsets, serializers

from .models import Company

class CompanySerializer(serializers.ModelSerializer):
    class Meta:
        model = Company
        fields = '__all__'

class CompanyViewSet(viewsets.ReadOnlyModelViewSet):
  queryset = Company.objects.all()
  serializer_class = CompanySerializer