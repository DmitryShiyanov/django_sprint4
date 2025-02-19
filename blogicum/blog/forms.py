from django.contrib.auth import get_user_model
from django import forms
from .models import Post, Comment

User = get_user_model()


class ProfileEdit(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'username', 'email']


class NewPost(forms.ModelForm):
    class Meta:
        model = Post
        fields = '__all__'
        exclude = ['author']
        widgets = {
            'pub_date': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
        }


class AddComment(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['text']