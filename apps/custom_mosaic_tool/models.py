# Copyright 2016 United States Government as represented by the Administrator
# of the National Aeronautics and Space Administration. All Rights Reserved.
#
# Portion of this code is Copyright Geoscience Australia, Licensed under the
# Apache License, Version 2.0 (the "License"); you may not use this file
# except in compliance with the License. You may obtain a copy of the License
# at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# The CEOS 2 platform is licensed under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# http://www.apache.org/licenses/LICENSE-2.0.
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

from django.db import models
from django.core.exceptions import ValidationError

from apps.dc_algorithm.models import Area, Compositor, Satellite, AnimationType
from apps.dc_algorithm.models import (Query as BaseQuery, Metadata as BaseMetadata, Result as BaseResult, ResultType as
                                      BaseResultType, UserHistory as BaseUserHistory)

import datetime


class UserHistory(BaseUserHistory):
    """
    Extends the base user history adding additional fields
    See the dc_algorithm.UserHistory docstring for more information
    """
    pass


class ResultType(BaseResultType):
    """
    extends base result type, adding additional fields required by app.
    See the dc_algorithm.ResultType docstring for more information.
    """

    red = models.CharField(max_length=25)
    green = models.CharField(max_length=25)
    blue = models.CharField(max_length=25)
    fill = models.CharField(max_length=25, default="red")


class Query(BaseQuery):
    """

    Extends base query, adds app specific elements. See the dc_algorithm.Query docstring for more information
    Defines the get_or_create_query_from_post as required, adds new fields, recreates the unique together
    field, and resets the abstract property. Functions are added to get human readable names for various properties,
    foreign keys should define __str__ for a human readable name.

    """
    query_type = models.ForeignKey(ResultType)
    animated_product = models.ForeignKey(AnimationType)
    compositor = models.ForeignKey(Compositor)

    class Meta(BaseQuery.Meta):
        unique_together = (
            ('platform', 'product', 'time_start', 'time_end', 'latitude_max', 'latitude_min', 'longitude_max',
             'longitude_min', 'title', 'description', 'query_type', 'animated_product', 'compositor'))
        abstract = True

    def get_fields_with_labels(self, labels, field_names):
        for idx, label in enumerate(labels):
            yield [label, getattr(self, field_names[idx])]

    @classmethod
    def get_or_create_query_from_post(cls, form_data):
        """Implements the get_or_create_query_from_post func required by base class

        See the get_or_create_query_from_post docstring for more information.
        Parses out the time start/end, creates the product, and formats the title/description

        Args:
            form_data: python dict containing either a single obj or a list formatted with post_data_to_dict

        Returns:
            Tuple containing the query model and a boolean value signifying if it was created or loaded.

        """
        query_data = form_data
        query_data['product'] = Satellite.objects.get(
            satellite_id=query_data['platform']).product_prefix + Area.objects.get(
                area_id=query_data['area_id']).area_id
        query_data['title'] = "Custom Mosaic Query" if 'title' not in form_data or form_data[
            'title'] == '' else form_data['title']
        query_data['description'] = "None" if 'description' not in form_data or form_data[
            'description'] == '' else form_data['description']

        valid_query_fields = [field.name for field in cls._meta.get_fields()]
        query_data = {key: query_data[key] for key in valid_query_fields if key in query_data}

        try:
            query = cls.objects.get(**query_data)
            return query, False
        except cls.DoesNotExist:
            query = cls(**query_data)
            query.save()
            return query, True


class Metadata(BaseMetadata):
    """
    Extends base metadata, adding additional fields and adding abstract=True.

    zipped_metadata_fields is required. 

    See the dc_algorithm.Metadata docstring for more information
    """
    satellite_list = models.CharField(max_length=100000, default="")
    zipped_metadata_fields = [
        'acquisition_list', 'clean_pixels_per_acquisition', 'clean_pixel_percentages_per_acquisition', 'satellite_list'
    ]

    class Meta(BaseMetadata.Meta):
        abstract = True


class Result(BaseResult):
    """
    Extends base result, adding additional fields and adding abstract=True
    See the dc_algorithm.Result docstring for more information
    """

    # result path + other data. More to come.
    result_filled_path = models.CharField(max_length=250, default="")
    animation_path = models.CharField(max_length=250, default="None")
    data_path = models.CharField(max_length=250, default="")
    data_netcdf_path = models.CharField(max_length=250, default="")

    class Meta(BaseResult.Meta):
        abstract = True

    def get_progress(self):
        """
        Super of base class - replace if total scenes and scenes processed
        won't give true progress.
        """
        super().get_progress()


class CustomMosaicTask(Query, Metadata, Result):
    """
    Combines the Query, Metadata, and Result abstract models
    """
    pass
