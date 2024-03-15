# from django.contrib.auth.forms import UserCreationForm 
from News.models import User 
from django import forms
from random import sample
from string import hexdigits
from allauth.account.forms import SignupForm
from django.conf import settings
from django.contrib.auth.models import Group
from django.core.mail import send_mail
import random
from django.contrib.auth import get_user_model



class CommonSignupForm(SignupForm):
    
    def save(self, request):
        user = super(CommonSignupForm, self).save(request)
        user.is_active = False
        code = ''.join(sample(hexdigits, 5))
        user.code = code

        basic_group = Group.objects.get(name='authors')
        basic_group.user_set.add(user)

        user.save()
        send_mail(
            subject='Код активации',
            message=f'Ваш код активации {code}',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email]
        )
        return user

    # class Meta:
    #     model = get_user_model()
    #     fields = ("username",
    #                 "first_name",
    #                 "last_name",
    #                 "email",
    #                 "password1",
    #                 "password2",)