from rest_framework import serializers

from ..models import Branch, Project


class ProjectSerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        model = Project
        fields = ('url', 'name')


class BranchSerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        model = Branch
        fields = ('url', 'name', 'project')
