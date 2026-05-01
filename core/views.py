from django.shortcuts import render
from django.views.generic import *
from django.contrib.auth.mixins import LoginRequiredMixin,UserPassesTestMixin
from django.contrib.auth.views import LoginView
from .forms import *
from .models import *
from django.urls import reverse_lazy
import json
from django.http import JsonResponse
from groq import Groq

class RegisterView(CreateView):
    form_class = UserRegisterForm
    template_name = 'registration/register.html'
    success_url = reverse_lazy('login') # После успеха — на страницу входа

class MyLoginView(LoginView):
    template_name = 'registration/login.html'

class RoadmapListView(ListView):
    model = Roadmap
    template_name = 'roadmap_list.html'
    context_object_name = 'roadmaps'

class RoadmapDetailView(DetailView):
    model = Roadmap
    template_name = 'roadmap_detail.html'
    context_object_name = 'roadmap'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        stacks = self.object.nodes.filter(node_type='stack').prefetch_related('children').order_by('order')
        if user.is_authenticated:
            completed_ids = set(UserProgress.objects.filter(user=user, is_completed=True).values_list('node_id', flat=True))

            previous_stack_completed = True 

            for stack in stacks:
                stack.is_completed = stack.id in completed_ids

                stack.is_accessible = previous_stack_completed

                if not stack.is_completed:
                    previous_stack_completed = False

                for topic in stack.children.all():
                    topic.is_completed = topic.id in completed_ids
                    topic.is_accessible = stack.is_accessible 

        context['stacks'] = stacks
        return context
    

class NodeDetailView(LoginRequiredMixin, DetailView):
    model = Node
    template_name = 'node_detail.html' 
    context_object_name = 'node'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Получаем все саб-темы
        subtopics = list(self.object.children.all().order_by('order'))
        
        # Делим список пополам для левой и правой колонки
        half = len(subtopics) // 2 + len(subtopics) % 2
        context['left_subtopics'] = subtopics[:half]
        context['right_subtopics'] = subtopics[half:]
        
        return context
    


import json
import os
import traceback
from django.views import View
from django.http import JsonResponse
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from groq import Groq
from dotenv import load_dotenv
from .models import Node

# Загружаем переменные из .env
load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

class GenerateSubtopicView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        return self.request.user.is_staff

    def post(self, request, pk):
        try:
            # Читаем данные из тела запроса
            data = json.loads(request.body)
            subtopic_title = data.get('title')
            
            if not subtopic_title:
                return JsonResponse({'status': 'error', 'message': 'Название не получено'}, status=400)

            parent_node = Node.objects.get(pk=pk)

            # ... (начало метода post остается прежним)

            # Формируем сложный промпт на английском
            system_prompt = (
                "You are an expert Python Backend Instructor. Your goal is to create a high-quality educational module. "
                "You must return the response strictly in JSON format with two keys: 'theory' and 'practice'.\n\n"
                "1. 'theory': Provide a detailed explanation of the topic in Russian. Include clear, well-commented Python code examples. "
                "Use Markdown for formatting (bold text, code blocks).\n"
                "2. 'practice': Create a hands-on coding assignment in Russian based on the theory. "
                "It should challenge the student to apply what they just learned."
            )

            user_prompt = f"Create a comprehensive lesson about '{subtopic_title}' for the '{parent_node.title}' module."

            chat_completion = client.chat.completions.create(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                model="llama-3.1-8b-instant",
                response_format={"type": "json_object"}
            )

            ai_response = json.loads(chat_completion.choices[0].message.content)
            
            # Сохраняем теорию в Description, а задание в Content
            new_node = Node.objects.create(
                title=subtopic_title,
                parent=parent_node,
                roadmap=parent_node.roadmap,
                node_type='subtopic',
                description=ai_response.get('theory'), # Теория с кодом
                content=ai_response.get('practice'),    # Задание (как ты и просил)
                order=parent_node.children.count() * 10
            )

            return JsonResponse({'status': 'success', 'id': new_node.id})

        except Node.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Родительская тема не найдена'}, status=404)
        except Exception as e:
            # Печатаем полный текст ошибки в консоль, чтобы ты его увидел
            print("--- ОШИБКА В ГЕНЕРАЦИИ ---")
            traceback.print_exc() 
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
    