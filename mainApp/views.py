from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseForbidden, HttpResponseNotFound
from django.db import IntegrityError
from django.contrib.auth import authenticate, login
from django.views.decorators.csrf import csrf_exempt
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import mixins, viewsets, permissions, generics, status
from django.contrib.auth import get_user_model
import os
import urbanairship as ua
import django
import json

import mainApp
import serializers
import models, permissions as newPermissions
from django.core.serializers.json import DjangoJSONEncoder


UA_APP_KEY = os.environ.get('UA_APP_KEY', '')
UA_MASTER_SECRET = os.environ.get('UA_MASTER_SECRET', '')
airship = ua.Airship(UA_APP_KEY, UA_MASTER_SECRET)


# User related APIs ------------------------------------------------

class UserProfileList(viewsets.ViewSet):
    def list(self, request):
        # Note this list won't return the system admin, which have no token & profile :-)
        queryset = models.UserProfile.objects.all()
        serializer = serializers.UserProfileSerializer(queryset, many=True)
        return Response(serializer.data)

    def create(self, request):
        allowedCompanies = ('auspost.com.au', 'rumor.com' )

        errorMessage = None
        try:
            password = request.DATA.get('password')
            email = request.DATA.get('email')
            atPos = email.rfind('@');
            if atPos <= 0:
                errorMessage = { 'error': 'invalid email address' }
            else:
                company = email[(atPos+1):]
                if company not in allowedCompanies:
                    errorMessage = { 'error': 'un-authorised company' }

            if errorMessage is None:
                models.UserProfile.objects.create_user(email, password)
                return _userLogin(request, email, password, True)

        except IntegrityError:
            errorMessage = { 'error': 'That username already exists' }

        return HttpResponseBadRequest(json.dumps(errorMessage), content_type='text/json')


class UserProfileDetail(mixins.RetrieveModelMixin,
                  mixins.UpdateModelMixin,
                  mixins.DestroyModelMixin,
                  generics.GenericAPIView):
    queryset = models.UserProfile.objects.all()
    serializer_class = serializers.UserProfileSerializer

    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        if request.user and request.DATA.get('password'):
            request.user.set_password(request.DATA.get('password'))
            request.user.save()
        return self.update(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        return self.destroy(request, *args, **kwargs)


class UserLogin(APIView):
    #@csrf_exempt
    def post(self, request, *args, **kwargs):
        email = request.POST.get('email')
        password = request.POST.get('password')
        return _userLogin(request, email, password)


class UserLogout(APIView):
    def get(self, request, *args, **kwargs):
        django.contrib.auth.logout(request)
        return HttpResponse()


# Supporting Functions ---------------------------------------------

def _userLogin(request, email, password, newUser=False):
    user = authenticate(email=email, password=password)
    if user is not None:
        if user.is_active:
            login(request, user)

            serializer = serializers.UserProfileSerializer(user)
            dict = serializer.data
            dict['token'] = str(user.auth_token)
            #response = HttpResponse(json.dumps(dict))
            #response.status_code = status.HTTP_201_CREATED if newUser else status.HTTP_200_OK
            #return response
            outputStatus = (status.HTTP_201_CREATED if newUser else status.HTTP_200_OK)
            return HttpResponse(json.dumps(dict), status=outputStatus)

        else:
            return HttpResponseForbidden(content='Your account is not active.')
    else:
        return HttpResponseNotFound()



# Rumor related APIs

class RumorListViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    queryset = models.Rumor.objects.all()
    serializer_class = serializers.RumorSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,
                          newPermissions.IsOwnerOrReadOnly,)

    def post(self, request, *args, **kwargs):
        requestData = request.DATA.dict()
        requestData['owner'] = request.user.id
        serializer = serializers.RumorSerializer(data=requestData)

        if serializer.is_valid() == False:
            return HttpResponseBadRequest(serializer.errors)

        rumor = serializer.save(force_insert=True)

        urban_airship_broadcast(rumor)

        return HttpResponse(json.dumps(serializers.RumorSerializer(rumor).data, cls=DjangoJSONEncoder), status=status.HTTP_201_CREATED)


def urban_airship_broadcast(rumor):
    alertText = 'New rumor: ' + rumor.title

    push = airship.create_push()
    push.audience = ua.all_
    push.notification = ua.notification(alert=alertText)
    push.device_types = ua.all_
    push.send()


class RumorDetailViewSet(viewsets.ModelViewSet):
    queryset = models.Rumor.objects.all()
    serializer_class = serializers.RumorSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,
                          newPermissions.IsOwnerOrReadOnly,)


def set_rumor_thumbs(pk, request, param):
    user = request.user
    rumor = models.Rumor.objects.get(pk=pk)

    if param == 'up':
        rumor.thumbsUpUser.add(user)
        rumor.thumbsDownUser.remove(user)
    elif param == 'down':
        rumor.thumbsUpUser.remove(user)
        rumor.thumbsDownUser.add(user)
    else:
        return HttpResponse(status=status.HTTP_404_NOT_FOUND)

    #thumbsUpCount = rumor.thumbsUpUser.count()
    #thumbsDownCount = rumor.thumbsDownUser.count()

    #response = get_rumor_thumbs(pk, user)
    #response.status_code = status.HTTP_201_CREATED
    #return response
    #response = HttpResponse(json.dumps({"thumbsUpCount": thumbsUpCount, "thumbsDownCount": thumbsDownCount}), content_type='application/json')
    #response.status_code = status.HTTP_201_CREATED
    #return response
    return HttpResponse(json.dumps(serializers.RumorSerializer(rumor, context={u'request': request}).data, cls=DjangoJSONEncoder), status=status.HTTP_201_CREATED)


def get_rumor_thumbs(pk, user):
    rumor = models.Rumor.objects.get(pk=pk)

    thumbsUpSet = rumor.thumbsUpUser.get_queryset()
    thumbsDownSet = rumor.thumbsDownUser.get_queryset()

    #thumbsUpJson = [ serializers.UserProfileSerializer(userProfile).data for userProfile in thumbsUpSet ]
    #thumbsDownJson = [ serializers.UserProfileSerializer(userProfile).data for userProfile in thumbsDownSet ]

    thumbsUpJson = [ userProfile.id for userProfile in thumbsUpSet ]
    thumbsDownJson = [ userProfile.id for userProfile in thumbsDownSet ]

    return HttpResponse(json.dumps({"thumbsUp": thumbsUpJson, "thumbsDown": thumbsDownJson}), content_type='application/json')


class RumorThumbsList(APIView):
    def get(self, request, pk):
        return get_rumor_thumbs(pk, request.user)


class RumorThumbsCreate(APIView):
    def post(self, request, pk, param):
        return set_rumor_thumbs(pk, request, param)


class RumorCommentList(APIView):
    def get(self, request, pk):
        rumor = models.Rumor.objects.get(pk=pk)
        serializer = serializers.RumorCommentSerializer(rumor.rumorcomment_set.all(), many=True)
        return mainApp.JSONResponse(serializer.data)

    def post(self, request, pk):
        rumorComment = models.RumorComment(owner=request.user,
                                           rumor=models.Rumor.objects.get(pk=pk),
                                           content=request.DATA['content'])
        rumorComment.save()
        serializer = serializers.RumorCommentSerializer(rumorComment)
        response = mainApp.JSONResponse(serializer.data)
        response.status_code = status.HTTP_201_CREATED
        return response


class RumorCommentDetail(APIView):
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,
                          newPermissions.IsOwnerOrReadOnly,)

    def delete(self, request, pk, pkComment):
        rumor = models.Rumor.objects.get(pk=pk)
        rumorComment = rumor.rumorcomment_set.get(pk=pkComment)
        rumorComment.delete()
        return HttpResponse(status=status.HTTP_204_NO_CONTENT)


class RumorPoll(APIView):
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,
                          newPermissions.IsOwnerOrReadOnly,)

    def post(self, request, pk):
        rumor = models.Rumor.objects.get(pk=pk)
        if rumor.rumorpollcolumn_set.count() > 0:
            return HttpResponseBadRequest(reason='The poll exists')

        jsonString = request.POST.get('content')
        jsonArray = json.loads(jsonString)
        for jsonObject in jsonArray:
            jsonObject['rumor'] = rumor.id
            serializer = serializers.RumorPollColumnSerializer(data=jsonObject)
            if serializer.is_valid():
                serializer.save()
            else:
                return HttpResponseBadRequest(reason='Failed to de-serializer the content')
        return HttpResponse(status=status.HTTP_204_NO_CONTENT)

    def get(self, request, pk):
        rumor = models.Rumor.objects.get(pk=pk)
        list = []
        for rumorpollcolumn in rumor.rumorpollcolumn_set.all():
            serializer = serializers.RumorPollColumnSerializer(rumorpollcolumn)
            list.append(serializer.data)
        return HttpResponse(json.dumps(list, cls=DjangoJSONEncoder))


class RumorPollDetail(APIView):
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,
                          newPermissions.IsOwnerOrReadOnly,)

    def post(self, request, pk, pkPollColumn):
        rumor = models.Rumor.objects.get(pk=pk)
        pkPollColumn = int(pkPollColumn)

        for rumorPollColumn in rumor.rumorpollcolumn_set.all():
            if rumorPollColumn.id == pkPollColumn:
                rumorPollColumn.rumorPollUser.add(request.user)
            else:
                rumorPollColumn.rumorPollUser.remove(request.user)

        return HttpResponse(status=status.HTTP_204_NO_CONTENT)



# Only for Testing

#def test(request, pk):
#    rumor = models.Rumor.objects.get(pk=pk)
#    serializer = serializers.RumorThumbsSerializer(rumor)
#    return HttpResponse(serializer.data)
