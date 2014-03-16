from rest_framework import serializers
from rest_framework.fields import Field

import models


class UserProfileSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = models.UserProfile
        fields = ('id', 'email', 'first_name', 'last_name', 'profileImage', 'description', )


class RumorCommentSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.RumorComment


class RumorSerializer(serializers.ModelSerializer):
    #comments = RumorCommentSerializer(source='rumorcomment_set', required=False, read_only=True)
    commentCount = serializers.SerializerMethodField('comment_count')
    thumbsUpCount = serializers.SerializerMethodField('thumbs_up_count')
    thumbsDownCount = serializers.SerializerMethodField('thumbs_down_count')
    thumbsVote = serializers.SerializerMethodField('thumbs_vote')
    poll = serializers.SerializerMethodField('poll_columns')

    def comment_count(self, rumor):
        return rumor.rumorcomment_set.count() if rumor is not None else 0


    def thumbs_up_count(self, rumor):
        return rumor.thumbsUpUser.count() if rumor is not None else 0

    def thumbs_down_count(self, rumor):
        return rumor.thumbsDownUser.count() if rumor is not None else 0

    def thumbs_vote(self, rumor):
        if rumor is not None:
            request = self.context.get(u'request', None)

            if request is not None and request.user is not None:
                isThumbsUp = rumor.thumbsUpUser.get_queryset().filter(id=request.user.id).exists()
                if isThumbsUp:
                    return "up"

                isThumbsDown = rumor.thumbsDownUser.get_queryset().filter(id=request.user.id).exists()
                if isThumbsDown:
                    return "down"

        return ""

    def poll_columns(self, rumor):
        if rumor is None:
            return []

        list = []
        for rumorpollcolumn in rumor.rumorpollcolumn_set.all():
            serializer = RumorPollColumnCompactSerializer(rumorpollcolumn)
            list.append(serializer.data)
        return list

    class Meta:
        model = models.Rumor
        exclude = ('thumbsUpUser', 'thumbsDownUser', )


class RumorPollColumnSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.RumorPollColumn


class RumorPollColumnCompactSerializer(serializers.ModelSerializer):
    rumorPollUserCount = serializers.SerializerMethodField('user_count')

    def user_count(self, rumorPollColumn):
        return rumorPollColumn.rumorPollUser.count()

    class Meta:
        model = models.RumorPollColumn
        exclude = ('rumorPollUser', )
