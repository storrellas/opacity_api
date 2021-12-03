import os

import pandas as pd
import numpy as np
import json

# Django imports
from django.shortcuts import render
from django.conf import settings

# DRF imports
from rest_framework import views, viewsets, serializers, exceptions
from rest_framework.response import Response

# Upload file
from rest_framework.parsers import MultiPartParser
from rest_framework.decorators import parser_classes

# Models
from .models import Company

###########################
# Serializers
###########################

class CompanySerializer(serializers.ModelSerializer):
    class Meta:
        model = Company
        fields = '__all__'

###########################
# Viewsets
###########################

class CompanyViewSet(viewsets.ModelViewSet):
  queryset = Company.objects.all()
  serializer_class = CompanySerializer

class CompanyPivotTableApiView(views.APIView):

  def get(self, request, pk, format=None):
    company = Company.objects.get(uuid=pk)
    file_path = os.path.join(settings.COMPANY_DATA, company.ref)
    df = pd.read_csv(file_path, parse_dates=["Date"])

    df["Date"] = pd.to_datetime(df['Date'])

    # Mask
    start = '12-01-2019'
    end = '12-05-2019'
    mask = (df['Date'] > start) & (df['Date'] <= end)
    df = df.loc[mask]

    # Create pivot_table
    table = pd.pivot_table(df, index=['Portfolio name'], values=["Impressions", "Clicks"], dropna=True, fill_value=0,
                              aggfunc={"Impressions": np.sum,"Clicks": np.sum})
    return Response(table)


class CompanyRawApiView(views.APIView):

  def get(self, request, pk, format=None):
    company = Company.objects.get(uuid=pk)
    file_path = os.path.join(settings.COMPANY_DATA, company.ref)
    df = pd.read_csv(file_path, parse_dates=["Date"])

    df = df.fillna(0)
    # Subset number of rows
    ret = df.loc[1:10]

    return Response({'message': ret.to_dict()})


@parser_classes((MultiPartParser, ))
class CompanyImportView(views.APIView):
  def post(self, request, pk, format=None):
    company = Company.objects.get(uuid=pk)

    # Check properly parameters
    file_node = request.FILES.get('data-file')
    if file_node is None:
      raise exceptions.ValiationError("Mising 'data-file'")

    # Read content
    file_node_content = file_node.read()    
    with open( os.path.join(settings.COMPANY_DATA, company.ref) , "wb") as f:
      f.write(file_node_content)

    return Response({'message': 'ok'}) 