from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('hot/', views.hot, name='hot'),
    path('tag/<str:tag_name>/', views.tag, name='tag'),
    path('question/<int:question_id>/', views.question, name='question'),
    path('ask/', views.ask, name='ask'),
    path('question/<int:question_id>/answer/', views.add_answer, name='add_answer'),
    path('question/<int:question_id>/vote/<str:value>/', views.vote_question, name='vote_question'),
    path('answer/<int:answer_id>/vote/<str:value>/', views.vote_answer, name='vote_answer'),
]
