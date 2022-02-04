import os
from io import StringIO
import pandas as pd
import numpy as np
import json

# Django imports
from django.shortcuts import render
from django.conf import settings

# DRF imports
from rest_framework import views, viewsets, serializers, exceptions, status
from rest_framework.response import Response

# Upload file
from rest_framework.parsers import MultiPartParser
from rest_framework.decorators import parser_classes

# Models
from .models import Company, Product

###########################
# Serializers
###########################

class CompanySerializer(serializers.ModelSerializer):
    product_commonDenominators = serializers.SerializerMethodField()
    def get_product_commonDenominators(self, obj):
      return Product.COMMON_DENOMINATOR_LIST
    class Meta:
        model = Company
        fields = '__all__'

class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = '__all__'

###########################
# Viewsets
###########################

class CompanyViewSet(viewsets.ModelViewSet):
  queryset = Company.objects.all()
  serializer_class = CompanySerializer

  def perform_create(self, serializer):
    # Incorporate generic mappings if any
    mappings = {"unmapped": [],
              "date": [],
              "values": [],
              "commonDenominators": []}
    if self.request.data.get('mappings'):
      mappings = self.request.data.get('mappings')

    serializer.save(mappings=mappings)


class ProductViewSet(viewsets.ModelViewSet):
  queryset = Product.objects.all()
  serializer_class = ProductSerializer

class CompanyPivotTableApiView(views.APIView):


  def post(self, request, pk, format=None):
    company = Company.objects.get(uuid=pk)

    # Check whether file is uploaded
    if company.ref is None:
      return Response({'message': 'No file specified'}, status=status.HTTP_400_BAD_REQUEST)
    # Check whether mappings was created
    mappings = company.mappings
    if not mappings['date'] or not mappings['commonDenominators'] or not mappings['values']:
        return Response({'message': 'No mappings specified'}, status=status.HTTP_400_BAD_REQUEST)

    # Check whether common denominator was passed
    commonDenominator = request.data.get('commonDenominator')
    if commonDenominator is None:
      return Response({'message': 'Missing commonDenominator'}, status=status.HTTP_400_BAD_REQUEST)

    # Read CSV file
    file_path = os.path.join(settings.COMPANY_DATA, company.ref)
    df = pd.read_csv(file_path, parse_dates=["Date"])

    # Filtering by CSV columns
    filtering = []
    for column in df.columns:
      if column in request.query_params:
        filtering.append( { 'key': column, 'value': request.query_params.get(column)})
    for filter_item in filtering:
      key = filter_item['key']
      value = filter_item['value']
      df = df[ df[key] == value]

    # Filtering by CD in Product
    filtering_product = {}
    for item in request.query_params:
      if item in Product.COMMON_DENOMINATOR_LIST:
        filtering_product[item] = request.query_params.get(item)

    queryset_filtering = company.products.filter(**filtering_product)
    filtering_asin_list = queryset_filtering.order_by('asin').values_list('asin', flat=True) 
    df = df[ df['Advertised ASIN'].isin(filtering_asin_list) == True]

    # Joining products and DF
    for cd in Product.COMMON_DENOMINATOR_LIST:
      df[cd] = None
    # Programmatically join with products
    for product in company.products.all().iterator():      
      for cd in Product.COMMON_DENOMINATOR_LIST:
        #df[cd] = None
        df.loc[ df['Advertised ASIN'] == product.asin, cd] = getattr(product, cd)

    # Define index and values
    pivot_index = [commonDenominator]
    pivot_values = mappings['values']
    aggfunc = {}
    for value in pivot_values:
        aggfunc[value] = np.sum

    # Some pivot value columns can have percentage and Dollar signs, so we
    # convert them to float
    special_chars = ['\$', '%']
    special_char_mapping = {}
    for pivot_value in pivot_values:
        for special_char in special_chars:
            if object == df[pivot_value].dtypes:
                if df[pivot_value].str.contains(special_char).sum() != 0:
                    special_char_mapping[pivot_value] = special_char
                    df[pivot_value] = df[pivot_value].replace({special_char: ''},
                                                              regex=True).astype(float)
                    break


    # Iterate on data ranges
    pivot_table = None
    pivot_table_list = []
    for date in request.data.get('dateRange'):
      start = date['startDate']
      end = date['endDate']

      range_mask = (df['Date'] > start) & (df['Date'] <= end)
      range_frame = df.loc[range_mask]

      # Create the tables
      range_table = pd.pivot_table(range_frame,
                                  index=pivot_index,
                                  values=pivot_values,
                                  dropna=True,
                                  fill_value=0,
                                  aggfunc=aggfunc)

      if range_table.empty:
          return Response([])

      # Add special characters back to columns
      for pivot_value, special_char in special_char_mapping.items():
          range_table[pivot_value] = special_char.replace('\\', '') + range_table[pivot_value].round(2).astype(str)

      # Rename the columns to indicate date range
      columns = {}
      for value in pivot_values:
          columns[value] = value + f' {start} to {end}'
      range_table.rename(columns=columns, inplace=True)

      # Append to df_total   
      if pivot_table is None:
        pivot_table = range_table
      else:
        pivot_table = pd.concat([pivot_table, range_table], axis=1)

      #####################
      #####################

      # Create the tables
      range_table_v2 = pd.pivot_table(range_frame,
                                  index=pivot_index,
                                  values=pivot_values,
                                  dropna=True,
                                  fill_value=0,
                                  aggfunc=aggfunc)

      if range_table_v2.empty:
          return Response([])

      # Add special characters back to columns
      for pivot_value, special_char in special_char_mapping.items():
          range_table_v2[pivot_value] = special_char.replace('\\', '') + range_table_v2[pivot_value].round(2).astype(str)

      # Rearrange columns
      columns = range_table_v2.columns.tolist()
      new_order = []
      for i in range(len(pivot_values)):
          new_order.extend(columns[i::len(pivot_values)])

      range_table_v2 = range_table_v2[new_order]

      # Treat index as regular column
      range_table_v2.reset_index(level=0, inplace=True)

      # Replace NaN by None
      range_table_v2 = range_table_v2.fillna(np.nan).replace([np.nan], [None])

      pivot_table_list.append({
        'startDate': start,
        'endDate': end,
        'data': range_table_v2.to_dict(orient="records")
      })
      

    # Rearrange columns
    columns = pivot_table.columns.tolist()
    new_order = []
    for i in range(len(pivot_values)):
        new_order.extend(columns[i::len(pivot_values)])

    pivot_table = pivot_table[new_order]

    # Treat index as regular column
    pivot_table.reset_index(level=0, inplace=True)

    # Replace NaN by None
    pivot_table = pivot_table.fillna(np.nan).replace([np.nan], [None])

    # Convert to format appropriate for react-data-grid
    #return Response({'legacy': pivot_table.to_dict(orient="records"), 'prototype': pivot_table_list})
    return Response({'legacy': pivot_table.to_dict(orient="records"), 'result': pivot_table_list})
    


class CompanyRawApiView(views.APIView):

  def get(self, request, pk, format=None):
    company = Company.objects.get(uuid=pk)


    # Check whether file is uploaded
    if company.ref is None:
      return Response({'message': 'No file specified'}, status=status.HTTP_400_BAD_REQUEST)
    # Check whether mappings was created
    mappings = company.mappings
    if not mappings['date'] or not mappings['commonDenominators'] or not mappings['values']:
        return Response({'message': 'No mappings specified'}, status=status.HTTP_400_BAD_REQUEST)

    # Read CSV
    file_path = os.path.join(settings.COMPANY_DATA, company.ref)
    df = pd.read_csv(file_path, parse_dates=["Date"])
    # Fill NA values
    df = df.fillna(0)

    # # Subset number of rows
    # ret = df.loc[1:10]

    # NOTE: /rawData response
    # return Response({'message': ret.to_dict()})


    # NOTE: /company_raw response

    # Treat index as regular column
    df.reset_index(level=0, inplace=True)

    # Convert to format appropriate for react-data-grid
    return Response(df.to_dict(orient="records"))





@parser_classes((MultiPartParser, ))
class CompanyImportView(views.APIView):
  def post(self, request, pk, format=None):
    company = Company.objects.get(uuid=pk)

    # Check properly parameters
    file_node = request.FILES.get('data-file')
    if file_node is None:
      raise exceptions.ValiationError("Mising 'data-file'")

    # Read content
    company.ref = f"{str(company.uuid)}.csv"
    file_node_content = file_node.read()    
    with open( os.path.join(settings.COMPANY_DATA, company.ref) , "wb") as f:
      f.write(file_node_content)

    # Update company mappings
    df = pd.read_csv(StringIO(file_node_content.decode('utf-8')), sep=",")
    columns = list(df.columns)
    company.mappings = {"unmapped": columns,
              "date": [],
              "values": [],
              "commonDenominators": []}
    company.save()


    return Response(status=status.HTTP_204_NO_CONTENT)

