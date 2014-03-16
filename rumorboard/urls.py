from django.conf.urls import patterns, include, url
from mainApp import views

from django.contrib import admin

admin.autodiscover()

user_profile_list = views.UserProfileList.as_view({
    'get': 'list',
    'post': 'create'
})

rumor_list = views.RumorListViewSet.as_view({
    'get': 'list',
#    'post': 'create'
})
rumor_detail = views.RumorDetailViewSet.as_view({
    'get': 'retrieve',
    'put': 'update',
#    'patch': 'partial_update',
    'delete': 'destroy'
})

#rumor_poll = views.RumorPoll.as_view({
#    'get': 'list',
#    'post': 'create',
#})


urlpatterns = patterns('',
    # User APIs -------------------------------------------

    # 1. get user list; 2. create new user
    url(r'^users/$', user_profile_list, name='user-profile-list'),

    # 1. get user info; 2. update user info; 3. delete user
	url(r'^users/(?P<pk>[0-9]+)/$', views.UserProfileDetail.as_view(), name='user-profile'),

    # user login
    url(r'^users/login/$', views.UserLogin.as_view(), name='user-login'),

    # user logout
    url(r'^users/logout/$', views.UserLogout.as_view(), name='user-logout'),


    # Rumor APIs ------------------------------------------
    # 1. get rumor list with rumor comments; 2. create a new rumor
    url(r'^rumors/$', rumor_list, name='rumor-list'),

    # 1. get rumor info; 2. update rumor info; 3. delete rumor
    url(r'^rumors/(?P<pk>[0-9]+)/$', rumor_detail, name='rumor-detail'),


    # Rumor Comment APIs ----------------------------------
    # 1. create a new rumor comment; 2. list all comments for a rumor
    url(r'^rumors/(?P<pk>[0-9]+)/comments/$', views.RumorCommentList.as_view(), name='rumor-comment-list'),

    # 1. delete rumor comment
    url(r'^rumors/(?P<pk>[0-9]+)/comments/(?P<pkComment>[0-9]+)/$', views.RumorCommentDetail.as_view(), name='rumor-comment-detail'),


    # Rumor Thumbs Up/Down APIs ---------------------------
    # Thumbs Up & Thumbs Down
    url(r'^rumors/(?P<pk>[0-9]+)/thumbs/$', views.RumorThumbsList.as_view(), name='rumor-thumbs'),
    url(r'^rumors/(?P<pk>[0-9]+)/thumbs/(?P<param>[a-z]+)/$', views.RumorThumbsCreate.as_view(), name='rumor-thumbs'),


    # Rumor Poll Column APIs ------------------------------
    #url(r'^rumors/(?P<pk>[0-9]+)/poll/$', rumor_poll, name='rumor-poll'),
    url(r'^rumors/(?P<pk>[0-9]+)/poll/$', views.RumorPoll.as_view(), name='rumor-poll'),
    url(r'^rumors/(?P<pk>[0-9]+)/poll/(?P<pkPollColumn>[0-9]+)/$', views.RumorPollDetail.as_view(), name='rumor-poll-detail'),


    # Admin APIs ------------------------------------------
    url(r'^admin/', include(admin.site.urls)),

    # API docs --------------------------------------------
    url(r'^docs/', include('rest_framework_swagger.urls')),


    # Testing ---------------------------------------------
    #url(r'^test_lab/(?P<pk>[0-9]+)/', views.test),
)


from django.contrib.staticfiles.urls import staticfiles_urlpatterns
urlpatterns += staticfiles_urlpatterns()