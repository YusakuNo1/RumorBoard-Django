from django.test import TestCase
from rest_framework import status
from django.core.exceptions import ObjectDoesNotExist
import random, math, string, json
from django.core.serializers.json import DjangoJSONEncoder

import models, config


class TestUserModel(TestCase):
    fixtures = ['users.json']

    TEST_USER_NAME = 'testuser@auspost.com.au'
    TEST_USER_NAME_TMP = 'testuser_tmp@auspost.com.au'
    TEST_USER_NAME_INVALID1 = 'testuser_tmp'
    TEST_USER_NAME_INVALID2 = 'testuser_tmp@aaa.com.au'
    TEST_USER_PASSWORD = '111'
    TEST_USER_PROFILE_DESC = 'testuser_profile_description'

    def setUp(self):
        self.testUser = models.UserProfile.objects.create_user(email=self.TEST_USER_NAME, password=self.TEST_USER_PASSWORD)
        pass

    def tearDown(self):
        pass


    # User API testing -------------------------------------------------

    # POST http://site_name/users/login with data
    def _login_user(self):
        data = {'email': self.TEST_USER_NAME, 'password': self.TEST_USER_PASSWORD, }
        response = self.client.post("/users/login/", data)
        jsonData = json.loads(response.content)
        token = jsonData['token'] if ('token' in jsonData) else None
        id = jsonData['id'] if ('id' in jsonData) else 0
        return (response.status_code, id, token)

    def _gen_auth_header(self, token):
        return {
            'HTTP_AUTHORIZATION': 'Token ' + token,
        }


    # POST http://site_name/users with data for TEST_USER_NAME_TMP
    def test_create_user(self):
        print '\n[in test_create_user]'

        # None email username
        data = {'email': self.TEST_USER_NAME_INVALID1, 'password': '111', }
        response = self.client.post("/users/", data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.content)

        # Not valid email
        data = {'email': self.TEST_USER_NAME_INVALID2, 'password': '111', }
        response = self.client.post("/users/", data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.content)

        data = {'email': self.TEST_USER_NAME_TMP, 'password': '111', }
        response = self.client.post("/users/", data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        jsonData = json.loads(response.content)
        self.assertTrue(('token' in jsonData) and (jsonData['token'] is not None, "can't find the token"))


    def test_login_user(self):
        print '\n[in test_login_user]'
        status_code, id, token = self._login_user()
        self.assertEqual(status_code, status.HTTP_200_OK)
        self.assertTrue(token is not None, "can't find the token")


    # GET http://site_name/users/logout
    def test_logout_user(self):
        print '\n[in test_logout_user]'
        response = self.client.get("/users/logout/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)


    def test_list_users(self):
        print '\n[in test_list_users]'
        self._login_user()
        response = self.client.get("/users/?format=json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)


    def test_fetch_user_detail(self):
        print '\n[in test_fetch_user_detail]'
        data = {'email': self.TEST_USER_NAME, 'password': self.TEST_USER_PASSWORD, }
        response = self.client.post("/users/login/", data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        jsonData = json.loads(response.content)
        response = self.client.get("/users/" + str(jsonData['id']) + '/?format=json', **self._gen_auth_header(jsonData['token']))
#        print '\n[David]: ' + response.content
        newJsonData = json.loads(response.content)

        try:
            for key in newJsonData:
                if jsonData[key] != newJsonData[key]:
                    raise Exception('Failed field: ' + key)
        except Exception, e:
            print(e)
            self.fail('/users/[User Id] API failed: old one is ' + str(jsonData) + ' but new one is ' + str(newJsonData))



    # Rumor API testing ------------------------------------------------

    def _create_random_rumor(self):
        data = "{ \"owner\": " + str(self.testUser.id) + ", \"title\": \"rumor\", \"content\": \"rumor content\", \"anonymous\": true }"
        jsonData = json.loads(data)
        jsonData['title'] = jsonData['title'] + str(int(random.random() * 1000))
        response = self.client.post("/rumors/", jsonData)
        return (jsonData, response)


    # GET http://site_name/rumors
    def test_list_rumors(self):
        print '\n[in test_list_rumors]'
        self._login_user()
        MAX_NEW_RUMOR = 5              # Note: this value must be smaller than the size of page in rest framework
        for i in range(0, MAX_NEW_RUMOR):
            self._create_random_rumor()

        response = self.client.get("/rumors/?format=json")
        newJsonData = json.loads(response.content)
        newJsonData = newJsonData['results']
        self.assertTrue(len(newJsonData) >= MAX_NEW_RUMOR, "Failed to create rumors, created " + str(MAX_NEW_RUMOR) + " but got " + str(len(newJsonData)) + " back!")


     # POST http://site_name/rumors
    def test_create_rumor(self):
        print '\n[in test_create_rumor]'
        self._login_user()
        jsonData, response = self._create_random_rumor()
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        newJsonData = json.loads(response.content)
        self.assertTrue(jsonData['title'] == newJsonData['title'], "rumor text is wrong")
        self.assertTrue(jsonData['content'] == newJsonData['content'], "content text is wrong")


    def _common_rumor_info(self, funcName):
        print '\n[in ' + funcName + ']'
        self._login_user()
        jsonData, response = self._create_random_rumor()
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        return jsonData, response

    # GET http://site_name/rumors/[rumor_id]/
    def test_get_rumor_info(self):
        jsonData, response = self._common_rumor_info('test_get_rumor_info')
        jsonData = json.loads(response.content)
        response = self.client.get("/rumors/" + str(jsonData['id']) + "/?format=json")
#        print 'here!!! ' + response.content
        newJsonData = json.loads(response.content)
        try:
            for key in jsonData:
                if key == u'thumbsUpCount' or key == u'thumbsDownCount' or key == u'commentCount' or key == u'contentImage':
                    continue

                if jsonData[key] != newJsonData[key]:
                    raise Exception('Failed field: ' + key)
        except Exception, e:
            print e
            self.fail('/users/[User Id] API failed: old one is ' + str(jsonData) + ' but new one is ' + str(newJsonData))

    # PUT http://site_name/rumors/[rumor_id]/
    def test_update_rumor_info(self):
        jsonData, response = self._common_rumor_info('test_update_rumor_info')
        jsonData = json.loads(response.content)
        updatedJsonData = jsonData
        UPDATED_FLAG = '-updated'
        updatedJsonData['title'] = updatedJsonData['title'] + UPDATED_FLAG
        response = self.client.put("/rumors/" + str(jsonData['id']) + "/?format=json", json.dumps(updatedJsonData), content_type='application/json')
        newJsonData = json.loads(response.content)
        self.assertTrue(jsonData['title'] == newJsonData['title'], 'Failed to update rumor title from old: ' + jsonData['title'] + ' to ' + newJsonData['title'])

    # DELETE http://site_name/rumors/[rumor_id]/
    def test_delete_rumor_info(self):
        jsonData, response = self._common_rumor_info('test_delete_rumor_info')
        jsonData = json.loads(response.content)
        response = self.client.delete("/rumors/" + str(jsonData['id']) + "/?format=json")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT, 'Failed to delete rumor Id: ' + str(jsonData['id']) + ' with response status code: ' + str(response.status_code))



    # Rumor Comment API testing ----------------------------------------

    def _create_random_rumor_comment(self, rumorId):
        jsonData = {}
        jsonData['content'] = 'new comment for rumor: ' + str(rumorId) + str(int(random.random()*1000))
        response = self.client.post("/rumors/" + str(rumorId) + "/comments/", jsonData)
        return (jsonData, response)


    # POST http://site_name/rumors/[rumor_id]/comments/
    def test_create_rumor_comment(self):
        print '\n[in test_create_rumor_comment]'
        self._login_user()
        jsonData, response = self._create_random_rumor()
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        jsonData = json.loads(response.content)
        rumorId = jsonData['id']
        jsonData, response = self._create_random_rumor_comment(rumorId)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, "Failed to create rumor comment")


    # GET http://site_name/rumors/[rumor_id]/comments/
    def test_list_rumor_comments(self):
        print '\n[in test_list_rumor_comments]'
        self._login_user()
        jsonData, response = self._create_random_rumor()
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        jsonData = json.loads(response.content)

        rumorId = jsonData['id']
        MAX_RUMOR_COMMENTS = 4              # Note: please make sure this value is less than the page size for rest framework
        for i in range(0, MAX_RUMOR_COMMENTS):
            jsonData, response = self._create_random_rumor_comment(rumorId)
            self.assertEqual(response.status_code, status.HTTP_201_CREATED, "Failed to create rumor comment")
        response = self.client.get("/rumors/" + str(rumorId) + "/comments/")
        newJsonData = json.loads(response.content)
        self.assertTrue(response.status_code == status.HTTP_200_OK and MAX_RUMOR_COMMENTS == len(newJsonData), "Failed to list rumor comments")


    # DELETE http://site_name/rumors/[rumor_id]/comments/[comment_id]
    def test_delete_rumor_comment(self):
        print '\n[in test_delete_rumor_comment]'
        self._login_user()
        jsonData, response = self._create_random_rumor()
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        jsonData = json.loads(response.content)

        rumorId = jsonData['id']
        MAX_RUMOR_COMMENTS = 4              # Note: please make sure this value is less than the page size for rest framework
        rumorCommentIds = []
        for i in range(0, MAX_RUMOR_COMMENTS):
            jsonData, response = self._create_random_rumor_comment(rumorId)
            self.assertEqual(response.status_code, status.HTTP_201_CREATED, "Failed to create rumor comment")
            jsonData = json.loads(response.content)
            rumorCommentIds.append(jsonData['id'])

        for rumorCommentId in rumorCommentIds:
            response = self.client.delete("/rumors/" + str(rumorId) + "/comments/" + str(rumorCommentId) + "/")
            self.assertTrue(response.status_code == status.HTTP_204_NO_CONTENT, "Failed to delete rumor comment")

        response = self.client.get("/rumors/" + str(rumorId) + "/comments/")
        newJsonData = json.loads(response.content)
        self.assertTrue(response.status_code == status.HTTP_200_OK and 0 == len(newJsonData), "Failed to list rumor comments")



    # Rumor Thumbs Up/Down API testing ---------------------------------

    # GET  http://site_name/rumors/[rumor_id]/thumbs/
    # POST http://site_name/rumors/[rumor_id]/thumbs/up/
    # POST http://site_name/rumors/[rumor_id]/thumbs/down/
    def _thumbs_up_or_down(self, isUp):
        print '\n[in test_thumbs_up]' if isUp else '\n[in test_thumbs_down]'
        self._login_user()
        jsonData, response = self._create_random_rumor()
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        createdRumorJsonData = json.loads(response.content)
        rumorId = createdRumorJsonData['id']

        response = self.client.post("/rumors/" + str(rumorId) + ("/thumbs/up/" if isUp else "/thumbs/down/"))
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        response = self.client.get("/rumors/" + str(rumorId) + "/thumbs/")
        thumbsUpRumorJsonData = json.loads(response.content)

        idList = thumbsUpRumorJsonData['thumbsUp' if isUp else 'thumbsDown']
        self.assertTrue(self.testUser.id in idList)

        response = self.client.post("/rumors/" + str(rumorId) + "/thumbs/random_stuff/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_thumbs_up(self):
        self._thumbs_up_or_down(True)

    def test_thumbs_down(self):
        self._thumbs_up_or_down(False)


    # Rumor Poll API testing -------------------------------------------

    def _common_rumor_poll(self, funcName):
        print '\n[in ' + funcName + ']'

        pollData = {}
        pollData['content'] = '[{\"name\": \"column 01\",\"columnIndex\": 0}, {\"name\": \"column 02\",\"columnIndex\": 1}]'

        self._login_user()
        jsonData, response = self._create_random_rumor()
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        jsonData = json.loads(response.content)
        rumorId = jsonData['id']

        response = self.client.post("/rumors/" + str(rumorId) + "/poll/", pollData)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT, "Failed to create rumor comment")
        return (rumorId, pollData, response)


    # GET  http://site_name/rumors/[rumor_id]/poll/
    def test_get_poll(self):
        rumorId, pollData, response = self._common_rumor_poll('test_create_poll')

        response = self.client.get("/rumors/" + str(rumorId) + "/poll/")
        self.assertEqual(response.status_code, status.HTTP_200_OK, "Failed to get rumor poll")

        pollJsonArray = json.loads(pollData['content'])
        newPollJsonArray = json.loads(response.content)
        for key in pollJsonArray[0]:
            self.assertTrue(pollJsonArray[0][key] == newPollJsonArray[0][key])


    # POST http://site_name/rumors/[rumor_id]/poll/
    def test_create_poll(self):
        jsonData, pollData, response = self._common_rumor_poll('test_create_poll')


    # POST http://site_name/rumors/[rumor_id]/poll/[poll_column_id]/
    def test_create_poll_vote(self):
        rumorId, _, _ = self._common_rumor_poll('test_create_poll_vote')

        response = self.client.get("/rumors/" + str(rumorId) + "/poll/")
        self.assertEqual(response.status_code, status.HTTP_200_OK, "Failed to get rumor poll")
        pollData = json.loads(response.content)[0]

        response = self.client.post("/rumors/" + str(rumorId) + "/poll/" + str(pollData['id']) + "/")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT, "Failed to create rumor poll")

        response = self.client.get("/rumors/" + str(rumorId) + "/poll/")
        self.assertEqual(response.status_code, status.HTTP_200_OK, "Failed to get rumor poll")

        pollData = json.loads(response.content)[0]
        isFound = False
        for aRumorPollUser in pollData['rumorPollUser']:
            if aRumorPollUser == self.testUser.id:
                isFound = True

        self.assertTrue(isFound, "Can't find the poll column which is voted just now")




