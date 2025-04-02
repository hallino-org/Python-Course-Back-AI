from rest_framework import viewsets, permissions
from rest_framework.response import Response
from django.shortcuts import get_object_or_404

from .models import Category
from .serializers import CategorySerializer


class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for categories."""

    queryset = Category.objects.filter(is_active=True)
    serializer_class = CategorySerializer
    lookup_field = 'slug'
    lookup_value_regex = '[\w-]+|[0-9]+'

    def get_object(self):
        """
        Returns the object the view is displaying.
        Supports both slug and primary key lookups.
        """
        queryset = self.filter_queryset(self.get_queryset())
        
        # Get the lookup value
        lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field
        lookup_value = self.kwargs[lookup_url_kwarg]
        
        # Try to determine if the lookup value is a primary key (integer)
        try:
            pk = int(lookup_value)
            obj = get_object_or_404(queryset, pk=pk)
        except (ValueError, TypeError):
            # If conversion to int fails, use the lookup_field (slug)
            filter_kwargs = {self.lookup_field: lookup_value}
            obj = get_object_or_404(queryset, **filter_kwargs)
            
        # May raise a permission denied
        self.check_object_permissions(self.request, obj)
        
        return obj

    def get_permissions(self):
        if self.action in ["list", "retrieve"]:
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated()]
