from django.forms import ModelForm
from .models import *
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django import forms
import pandas as pd

class createuserform(UserCreationForm):
    class Meta:
        model=User
        fields=['username','password'] 
 
class emailform(forms.Form):
    figure_id = forms.CharField(label='檔案ID', max_length=100, required=False)
    email = forms.EmailField(required=False)
    
