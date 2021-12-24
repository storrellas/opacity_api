import os

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

class ProductViewSet(viewsets.ModelViewSet):
  queryset = Product.objects.all()
  serializer_class = ProductSerializer

class CompanyPivotTableApiView(views.APIView):

  # def get(self, request, pk, format=None):
  #   company = Company.objects.get(uuid=pk)

  #   # Check whether file is uploaded
  #   if company.ref is None:
  #     return Response({'message': 'No file specified'}, status=status.HTTP_400_BAD_REQUEST)
  #   # Check whether mappings was created
  #   mappings = company.mappings
  #   if not mappings['date'] or not mappings['commonDenominators'] or not mappings['values']:
  #       return Response({'message': 'No mappings specified'}, status=status.HTTP_400_BAD_REQUEST)

  #   # Read CSV file
  #   file_path = os.path.join(settings.COMPANY_DATA, company.ref)
  #   df = pd.read_csv(file_path, parse_dates=["Date"])

  #   df["Date"] = pd.to_datetime(df['Date'])

  #   # Mask
  #   start = '12-01-2019'
  #   end = '12-05-2019'
  #   mask = (df['Date'] > start) & (df['Date'] <= end)
  #   df = df.loc[mask]

  #   # Create pivot_table
  #   table = pd.pivot_table(df, index=['Portfolio name'], values=["Impressions", "Clicks"], dropna=True, fill_value=0,
  #                             aggfunc={"Impressions": np.sum,"Clicks": np.sum})
  #   return Response(table)

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

    ########
    # NOTE: Pending to filter by Product.COMMON_DENOMINATOR_LIST
    ########

    # Programmatically join with products
    df['category1'] = None
    df['product_type'] = None
    df['custom_label0'] = None
    for product in company.products.all().iterator():
      for cd in Product.COMMON_DENOMINATOR_LIST:
        df.loc[ df['Advertised ASIN'] == product.asin, cd] = getattr(product, cd)

    # # Check Stats in items
    # advertised_asin_list = sorted( df['Advertised ASIN'].unique() )
    # seller_asin_list = list( queryset.order_by('asin').values_list('asin', flat=True) )
    # print(" ")
    # print("-- advertised_sku_list --")
    # print( advertised_asin_list )
    # print(" ")
    # print('-- seller_sku --')
    # print( seller_asin_list )
    # print(" ")
    # print("-- intersection --" )
    # print( list(set(advertised_asin_list) & set(seller_asin_list)))

    # def difference(list_a, list_b):
    #   a = set(list_a)
    #   b = set(list_b)
    #   c = {element for element in a if element not in b}
    #   return c
    # print(" ")
    # print("-- difference (elements in 'advertised_sku_list' not in 'seller_asin_list' --")
    # print( list(difference(advertised_asin_list, seller_asin_list)))
    # print("-- difference (elements in 'seller_asin_list' not in 'advertised_asin_list' --")
    # print( list(difference(seller_asin_list, advertised_asin_list)))

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


    # Define date ranges
    first_date_range = request.data.get('firstDateRange')
    second_date_range = request.data.get('secondDateRange')

    start0 = first_date_range['startDate']
    end0 = first_date_range['endDate']

    start1 = second_date_range['startDate']
    end1 = second_date_range['endDate']

    # Select the date ranges
    range0_mask = (df['Date'] > start0) & (df['Date'] <= end0)
    range1_mask = (df['Date'] > start1) & (df['Date'] <= end1)
    range0_frame = df.loc[range0_mask]
    range1_frame = df.loc[range1_mask]

    # Create the tables
    range0_table = pd.pivot_table(range0_frame,
                                  index=pivot_index,
                                  values=pivot_values,
                                  dropna=True,
                                  fill_value=0,
                                  aggfunc=aggfunc)

    range1_table = pd.pivot_table(range1_frame,
                                  index=pivot_index,
                                  values=pivot_values,
                                  dropna=True,
                                  fill_value=0,
                                  aggfunc=aggfunc)

    if range0_table.empty or range1_table.empty:
        return Response({})

    # Add special characters back to columns
    for pivot_value, special_char in special_char_mapping.items():
        range0_table[pivot_value] = special_char.replace('\\', '') + range0_table[pivot_value].round(2).astype(str)
        range1_table[pivot_value] = special_char.replace('\\', '') + range1_table[pivot_value].round(2).astype(str)

    # Rename the columns to indicate date range
    columns = {}
    for value in pivot_values:
        columns[value] = value + f' {start0} to {end0}'
    range0_table.rename(columns=columns, inplace=True)

    columns = {}
    for value in pivot_values:
        columns[value] = value + f' {start1} to {end1}'
    range1_table.rename(columns=columns, inplace=True)

    # Concatenate the tables into one table
    pivot_table = pd.concat([range0_table, range1_table], axis=1)

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
    return Response(pivot_table.to_dict(orient="records"))

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
    file_node_content = file_node.read()    
    with open( os.path.join(settings.COMPANY_DATA, company.ref) , "wb") as f:
      f.write(file_node_content)

    return Response({'message': 'ok'}) 