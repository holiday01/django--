from django.shortcuts import render
from django.shortcuts import redirect,render
from django.contrib.auth import login,logout,authenticate
from .forms import *
from .models import *
from django.http import HttpResponse
import io
import random
import py_avataaars as pa
from py_avataaars import PyAvataaar
import os
from django.core.cache import cache
import numpy as np
def home(request):
    return render(request,'Quiz/home.html')

def price(request):
    return render(request,'Quiz/price.html')

def upload_hs(request):
    return render(request,'Quiz/upload_hs.html')

def question(request):
    if request.method == 'POST':
        questions=testQuesModel.objects.all()
        l = 0
        o = 0
        final=0
        res = "我們建議你預約以下幾個心理諮商："
        #label = ["職場諮商","人際諮商","看醫生","多做休閒活動","原生家庭諮商","婚姻/親子諮商"]
        label = ["職場諮商","婚姻/親子諮商"]
        for q in questions:
            l += 1
            if "option1" ==  request.POST.get(q.question):
                o += 0
            elif "option2" ==  request.POST.get(q.question):
                o += 1
            elif "option3" ==  request.POST.get(q.question):
                o += 2
            elif "option4" ==  request.POST.get(q.question):
                o += 3
            elif "option5" ==  request.POST.get(q.question):
                o += 5
            if (l % 5) == 0:
                final += o
                if o >= 15:
                    #res = res + label[int(l/5)] + "  "
                    res = res + label[int(l/5-1)] + "  "
                if final > 35:
                    warn = "麻煩盡快聯絡我們"
                    img = "worse.jpeg"
                elif final < 10:
                    warn = "你非常棒"
                    img = "good.jpeg"
                    res = "歡迎參觀全人快樂中心"
                else:
                    warn = "可以考慮加入全人聊天社團"
                    img = "medium.jpeg"
                o = 0
        context = {'questions':o, "res":res, "warn": warn, "img":img}
        return render(request,'Quiz/result1.html',context)
    else:
        questions=testQuesModel.objects.all()
        context = {'questions':questions}
        return render(request,'Quiz/question.html',context)
 
 
def registerPage(request):
    if request.user.is_authenticated:
        return redirect('home') 
    else: 
        form = createuserform()
        if request.method=='POST':
            form = createuserform(request.POST)
            if form.is_valid() :
                user=form.save()
                return redirect('login')
        context={
            'form':form,
        }
        return render(request,'Quiz/register.html',context)
 
def loginPage(request):
    if request.user.is_authenticated:
        return redirect('home')
    else:
       if request.method=="POST":
        username=request.POST.get('username')
        password=request.POST.get('password')
        user=authenticate(request,username=username,password=password)
        if user is not None:
            login(request,user)
            return redirect('/')
       context={}
       return render(request,'Quiz/login.html',context)
 
def logoutPage(request):
    logout(request)
    return redirect('/')

def avatar_image(name, seed=None):

    if seed != "random":
        random.seed(seed)

    bytes = io.BytesIO()

    def r(enum_):
        return random.choice(list(enum_))
    avatar = pa.PyAvataaar(
    style=r(pa.AvatarStyle),
    skin_color=r(pa.SkinColor),
    hair_color=r(pa.HairColor),
    facial_hair_type=r(pa.FacialHairType),
    facial_hair_color=r(pa.HairColor),
    top_type=r(pa.TopType),
    hat_color=r(pa.Color),
    mouth_type=r(pa.MouthType),
    eye_type=r(pa.EyesType),
    eyebrow_type=r(pa.EyebrowType),
    nose_type=r(pa.NoseType),
    accessories_type=r(pa.AccessoriesType),
    clothe_type=r(pa.ClotheType),
    clothe_color=r(pa.Color),
    clothe_graphic_type=r(pa.ClotheGraphicType),
    )
    avatar.render_png_file('./static/avatar'+str(name)+'.png')


def show_avatar(request):
    send_class = emailform 
    global image
    global name
    if 'create' in request.POST:
        name = np.random.randint(0,10000)
        image = "avatar"+str(name)+".png"
        context={
            'name' : name,
            'image': image,
            'send' : send_class
        }
        avatar = avatar_image(name)
    
    elif 'sent' in request.POST:
            e = request.POST["email"]
            image = "avatar"+ str(request.POST["figure_id"]) +".png"
            send_cmd = "python3.8 /home/ubuntu/DjangoQuiz/smtp.py --message hello --target " +e + " --data /home/ubuntu/DjangoQuiz/static/" + image
            os.system(send_cmd)
            context={
            'image': image,
            'send' : send_class,
            'mes' : "寄送成功"
        }
    else:
        image = "avatar1.png"
        context={
            'image':image,
        }
    return render(request,'Quiz/avatar.html',context)
# Create your views here.
