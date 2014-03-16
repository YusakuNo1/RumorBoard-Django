from django.db import models
from django.contrib.auth.models import User, AbstractBaseUser, PermissionsMixin, BaseUserManager
from django_boto.s3.storage import S3Storage
import config
import rumorboard.settings as settings


s3 = S3Storage(bucket_name='babylyricsus')


class UserProfileManager(BaseUserManager):
    def create_user(self, email, password=None):
        if not email:
            raise ValueError('Users must have an email address')

        user = self.model(
            email = UserProfileManager.normalize_email(email),
        )

        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password):
        user = self.create_user(email,
            password=password,
        )
        user.is_admin = True
        user.save(using=self._db)
        return user


class UserProfile(AbstractBaseUser, PermissionsMixin, models.Model):
    email = models.EmailField(
        verbose_name='email address',
        max_length=config.EMAIL_FIELD_LENGTH,
        unique=True,
        db_index=True,
    )

    first_name = models.CharField(max_length=config.NAME_FIELD_LENGTH, blank=True)
    last_name = models.CharField(max_length=config.NAME_FIELD_LENGTH, blank=True)

    profileImage = models.ImageField(storage=s3, upload_to = settings.AWS_S3_FOLDER + '/profile/', default=None, null=True, blank=True)
    description = models.CharField(max_length=config.USER_DESCRIPTION_LENGTH, default='', blank=True)

    is_active = models.BooleanField(default=True)
    is_admin = models.BooleanField(default=False)

    objects = UserProfileManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    def get_full_name(self):
        # The user is identified by their email address
        return self.email

    def get_short_name(self):
        # The user is identified by their email address
        return self.email

    def __unicode__(self):
        return self.email

    def has_perm(self, perm, obj=None):
        "Does the user have a specific permission?"
        # Simplest possible answer: Yes, always
        return True

    def has_module_perms(self, app_label):
        "Does the user have permissions to view the app `app_label`?"
        # Simplest possible answer: Yes, always
        return True

    @property
    def is_staff(self):
        "Is the user a member of staff?"
        # Simplest possible answer: All admins are staff
        return self.is_admin


class Rumor(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    owner = models.ForeignKey(settings.AUTH_USER_MODEL)
    title = models.CharField(max_length=config.TITLE_LENGTH, null=True, blank=True)
    content = models.CharField(max_length=config.CONTENT_LENGTH)
    contentImage = models.ImageField(storage=s3, upload_to = settings.AWS_S3_FOLDER + '/rumor/', default=None, null=True, blank=True)
    anonymous = models.BooleanField(default=True)
    thumbsUpUser = models.ManyToManyField(UserProfile, related_name='thumbsUpUser', blank=True)
    thumbsDownUser = models.ManyToManyField(UserProfile, related_name='thumbsDownUser', blank=True)

    def __unicode__(self):
        return self.title if (self.title is not None and len(self.title) > 0) else self.content


class RumorComment(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    owner = models.ForeignKey(settings.AUTH_USER_MODEL)
    rumor = models.ForeignKey(Rumor)
    content = models.CharField(max_length=config.CONTENT_LENGTH, null=True, blank=True)
    #rating = models.IntegerField(default=config.RumorCommentRating.NoRating)

    def __unicode__(self):
        return self.content


#class RumorPoll(models.Model):
#    rumor = models.OneToOneField(Rumor)
#
#    def __unicode__(self):
#        return self.rumor.title if (self.rumor.title is not None and len(self.rumor.title) > 0) else self.rumor.content


class RumorPollColumn(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    rumor = models.ForeignKey(Rumor)
    name = models.CharField(max_length=config.TITLE_LENGTH)
    columnIndex = models.IntegerField()
    rumorPollUser = models.ManyToManyField(UserProfile, related_name='rumorPollUser', blank=True)

    def __unicode__(self):
        return self.rumor.title + ': ' + self.name
