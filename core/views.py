from django.shortcuts import render,get_object_or_404,redirect
from django.views.generic import *
from django.contrib.auth.mixins import LoginRequiredMixin,UserPassesTestMixin
from django.contrib.auth.views import LoginView
from .forms import *
from .models import *
from django.urls import reverse_lazy
import json
from groq import Groq
import os
from dotenv import load_dotenv
from django.contrib import messages
from django.contrib.auth import login


load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# Authentication

class RegisterView(CreateView):
    form_class = UserRegisterForm
    template_name = 'registration/register.html'
    success_url = reverse_lazy('verify')
    def form_valid(self, form):
        response = super().form_valid(form)
        self.object.profile.generate_and_send_code()
        login(self.request, self.object)
        return response 
    
class VerifyEmailView(LoginRequiredMixin,FormView):
    template_name = 'registration/verify_email.html'
    form_class = VerificationForm
    success_url = reverse_lazy('login')

    def form_valid(self, form):
        user = self.request.user
        entered_code = form.cleaned_data['code']
        profile = user.profile

        if profile.verification_code == entered_code:
            profile.is_verified = True
            profile.verification_code = None
            profile.save()
            messages.success(self.request, "Почта успешно подтверждена! Добро пожаловать.")
            return super().form_valid(form)
        
        messages.error(self.request, "Неверный код. Проверьте почту еще раз.")
        return self.form_invalid(form)

class MyLoginView(LoginView):
    template_name = 'registration/login.html'

    def get_success_url(self):
        user = self.request.user
        if hasattr(user, 'profile') and not user.profile.is_verified:
            if not user.profile.verification_code:
                user.profile.generate_and_send_code()
            return reverse_lazy('verify')
        return super().get_success_url()


# Profile
from django.db.models import Avg, Count, Q
from .models import Roadmap, UserProgress, Submission

class ProfileView(LoginRequiredMixin, DetailView):
    template_name = 'profile/dashboard.html'
    context_object_name = 'profile'

    def get_object(self):
        return self.request.user.profile

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        # 1. Прогресс по Roadmap (для каждого курса)
        roadmaps_stats = []
        for roadmap in Roadmap.objects.all():
            total_nodes = roadmap.nodes.count()
            completed_nodes = UserProgress.objects.filter(
                user=user, 
                node__roadmap=roadmap, 
                is_completed=True
            ).count()
            
            percent = int((completed_nodes / total_nodes) * 100) if total_nodes > 0 else 0
            
            # Находим текущий этап (первый не пройденный)
            current_node = roadmap.nodes.exclude(
                id__in=UserProgress.objects.filter(user=user, is_completed=True).values_list('node_id', flat=True)
            ).first()

            roadmaps_stats.append({
                'title': roadmap.title,
                'percent': percent,
                'current_step': current_node.title if current_node else "Завершено! 🎉"
            })
        
        context['roadmaps_stats'] = roadmaps_stats

        # 2. История AI-проверок (последние 5)
        context['recent_submissions'] = Submission.objects.filter(user=user).order_by('-created_at')[:5]

        # 3. Аналитика
        stats = Submission.objects.filter(user=user).aggregate(
            avg_score=Avg('ai_score'),
            total_attempts=Count('id'),
            success_rate=Count('id', filter=Q(is_passed=True))
        )
        
        if stats['total_attempts'] > 0:
            stats['success_percent'] = int((stats['success_rate'] / stats['total_attempts']) * 100)
        else:
            stats['success_percent'] = 0
            
        context['analytics'] = stats

        return context
    
class SettingsView(LoginRequiredMixin, View):
    def get(self, request):
        user_form = UserUpdateForm(instance=request.user)
        profile_form = ProfileUpdateForm(instance=request.user.profile)
        print('User',user_form)
        return render(request, 'profile/settings.html', {
            'user_form': user_form,
            'profile_form': profile_form
        })

    def post(self, request):
        user_form = UserUpdateForm(request.POST, instance=request.user)
        profile_form = ProfileUpdateForm(request.POST, request.FILES, instance=request.user.profile)

        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, 'Профиль успешно обновлен!')
            return redirect('settings')
        
        return render(request, 'profile/settings.html', {
            'user_form': user_form,
            'profile_form': profile_form
        }) 

class SubmissionListView(LoginRequiredMixin, ListView):
    model = Submission
    template_name = 'profile/submissions.html'
    context_object_name = 'submissions'
    paginate_by = 10

    def get_queryset(self):
        # Показываем только ответы текущего пользователя, сначала новые
        return Submission.objects.filter(user=self.request.user).order_by('-created_at')
    
class LeaderboardView(ListView):
    model = Profile
    template_name = 'profile/leaderboard.html'
    context_object_name = 'profiles' # общее имя для всех профилей
    
    def get_queryset(self):
        # Возвращаем топ-50 по очкам
        return Profile.objects.order_by('-points')[:50]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        all_profiles = self.get_queryset()
        
        # Разбиваем на логические группы для шаблона
        context['podium'] = all_profiles[:3]  # Топ-3
        context['others'] = all_profiles[3:]  # Остальные (с 4-го места)
        return context

class UserProfileDetailView(DetailView):
    model = User
    template_name = 'profile/public_profile.html'
    context_object_name = 'viewed_user'

    def get_object(self):
        return get_object_or_404(User, username=self.kwargs.get('username'))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        viewed_user = self.get_object()
        
        # Добавляем в контекст данные профиля и последние достижения
        context['profile'] = viewed_user.profile
        context['recent_submissions'] = Submission.objects.filter(
            user=viewed_user, 
            is_passed=True
        ).order_by('-created_at')[:5]
        
        return context

# Roadmap and AI-actions

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

        # 1. Получаем все стэки (у которых нет родителя)
        stacks = self.object.nodes.filter(parent__isnull=True).order_by('order')

        if user.is_authenticated:
            # 2. Собираем ID всех нод, которые пользователь уже завершил
            completed_ids = set(
                UserProgress.objects.filter(user=user, is_completed=True)
                .values_list('node_id', flat=True)
            )

            # Флаг для доступа к следующему Стэку
            can_open_next_stack = True 

            for stack in stacks:
                # Назначаем свойства динамически (их нет в модели, но они будут в объекте в шаблоне)
                stack.is_completed = stack.id in completed_ids
                stack.is_accessible = can_open_next_stack

                # Внутри стэка: первый топик доступен, если доступен сам стэк
                can_open_next_topic = stack.is_accessible
                
                # Получаем дочерние темы (Topics) этого стэка
                topics = stack.children.all().order_by('order')
                
                for topic in topics:
                    topic.is_completed = topic.id in completed_ids
                    topic.is_accessible = can_open_next_topic
                    
                    # Логика цепочки: следующий топик откроется, только если ТЕКУЩИЙ завершен
                    can_open_next_topic = topic.is_completed

                # Навешиваем список обработанных топиков обратно на объект стэка
                stack.dynamic_topics = topics

                # Чтобы открылся СЛЕДУЮЩИЙ Стэк (например, PostgreSQL), 
                # нужно чтобы последний топик текущего стэка был пройден
                can_open_next_stack = can_open_next_topic
        else:
            # Для неавторизованных либо закрываем всё, либо открываем только первый стэк
            for stack in stacks:
                stack.is_accessible = False
                stack.dynamic_topics = stack.children.all().order_by('order')

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

        previous_passed = True
        
        for sub in subtopics:
            # Устанавливаем флаг блокировки для текущего узла
            sub.is_locked = not previous_passed
            
            # Проверяем, пройдена ли текущая тема пользователем
            # ВНИМАНИЕ: Замени `Submission` на твою модель прогресса!
            is_passed = Submission.objects.filter(
                user=self.request.user, 
                node=sub, 
                is_passed=True # или ai_score__gte=5, смотря как ты определяешь успех
            ).exists()
            
            # Если текущая тема не пройдена, все СЛЕДУЮЩИЕ за ней будут заблокированы
            if not is_passed:
                previous_passed = False
        
        # Делим список пополам для левой и правой колонки
        half = len(subtopics) // 2 + len(subtopics) % 2
        context['left_subtopics'] = subtopics[:half]
        context['right_subtopics'] = subtopics[half:]
        
        return context
    

class GenerateSubtopicView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        return self.request.user.is_staff

    def post(self, request, pk):
        parent_node = get_object_or_404(Node, pk=pk)
        specialty = parent_node.roadmap.title
        subtopic_title = request.POST.get('title')
        if not subtopic_title:
            return redirect('roadmap_detail', pk=parent_node.roadmap.id)
    
        system_prompt = (
            f"You are an expert {specialty} Instructor. "
            "Generate a detailed, structured lesson and a practical task.\n"
            "Return ONLY valid JSON with two keys: 'theory' (string) and 'practice' (string).\n\n"
            "Formatting requirements for 'theory':\n"
            "- Use Markdown: headings (##, ###), code blocks with language specification (```python), bullet lists, etc.\n"
            "- Include at least 2–3 code examples with comments.\n"
            "- Add a real-world use case or best practices.\n"
            "- Length: 800–1500 characters, but be as informative as needed.\n"
            "- Write in Russian.\n\n"
            "Formatting for 'practice':\n"
            "- A single clear task that requires writing code.\n"
            "- Describe the expected input/output or behavior.\n"
            "- Optionally provide a template or hints.\n"
            "- Keep it concise (200–500 characters).\n\n"
            "IMPORTANT JSON ESCAPING RULES:\n"
            "- Escape double quotes inside strings: \\\"\n"
            "- Escape newlines as \\n\n"
            "- Use single quotes for code examples inside the JSON string, or escape double quotes properly.\n"
            "- Do NOT include any text outside the JSON object."
        )
    
        user_prompt = (
            f"Create a comprehensive lesson about '{subtopic_title}' "
            f"for the module '{parent_node.title}' in '{specialty}' roadmap.\n\n"
            "The lesson must include:\n"
            "- What is it and why it's important\n"
            "- Syntax and core concepts with code examples\n"
            "- A small real‑world example\n"
            "- Common pitfalls or tips\n\n"
            "The task should be a coding exercise that applies the learned material."
        )
    
        try:
            chat_completion = client.chat.completions.create(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                model="llama-3.1-8b-instant",
                response_format={"type": "json_object"}
            )
    
            ai_response = json.loads(chat_completion.choices[0].message.content)
    
            # Безопасное извлечение текста (если вдруг AI вернёт вложенный объект)
            theory = ai_response.get('theory', '')
            practice = ai_response.get('practice', '')
    
            # Если theory или practice – словари, конвертируем в строку
            if isinstance(theory, dict):
                theory = theory.get('text', theory.get('content', str(theory)))
            if isinstance(practice, dict):
                practice = practice.get('text', practice.get('content', str(practice)))
    
            # Дополнительно: распаковка экранированных символов (JSON уже распарсил, но на всякий случай)
            # Можно оставить как есть, строки уже корректные.
    
            new_node = Node.objects.create(
                title=subtopic_title,
                parent=parent_node,
                roadmap=parent_node.roadmap,
                node_type='subtopic',
                description=theory,   # лекция
                content=practice,     # задание
                order=parent_node.children.count() * 10
            )
    
            return redirect('subtopic_detail', pk=new_node.pk)
    
        except Exception as e:
            print(f"--- ОШИБКА ГЕНЕРАЦИИ ({specialty}) ---: {e}")
            return redirect('roadmap_detail', pk=parent_node.roadmap.id)
            
import markdown            

class SubtopicDetailView(LoginRequiredMixin, DetailView):
    model = Node
    template_name = 'subtopic_detail.html'
    context_object_name = 'node'

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        
        prev_subtopic = Node.objects.filter(
            parent=self.object.parent, 
            order__lt=self.object.order
        ).order_by('-order').first()

        if prev_subtopic:
            prev_passed = Submission.objects.filter(
                user=request.user, 
                node=prev_subtopic, 
                is_passed=True
            ).exists()
            
            if not prev_passed:
                messages.warning(request, "🔒 Эта тема пока закрыта. Сначала завершите предыдущее задание!")
                return redirect('node_detail', pk=self.object.parent.pk)

        # Если всё ок, продолжаем стандартную загрузку страницы
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        node = self.get_object()

        md = markdown.Markdown(extensions=[
            'extra',          
            'fenced_code',    
            'codehilite',    
            'nl2br',          
            'toc',            
        ])

        context['theory_html'] = md.convert(node.description or "")
        context['practice_html'] = md.convert(node.content or "")
        
        context['is_completed'] = Submission.objects.filter(
            user=self.request.user, 
            node=node, 
            is_passed=True
        ).exists()
        context['last_submission'] = Submission.objects.filter(user=self.request.user, node=node).order_by('-created_at').first()

        return context



from .ai import evaluate_node_answer

class CheckSubmissionView(LoginRequiredMixin, View):
    def post(self, request, node_id):
        node = get_object_or_404(Node, pk=node_id)
        
        answer_text = request.POST.get('answer_text', '').strip()
        if not answer_text:
            messages.error(request, "Ответ не может быть пустым.")
            return redirect('subtopic_detail', pk=node.id)
        
        question = node.content
        specialty = node.roadmap.title
        result = evaluate_node_answer(question, answer_text, specialty=specialty)
        score = result['score']
        feedback = result['feedback']
        is_passed = score >= 7
        
        submission = Submission.objects.create(
            user=request.user,
            node=node,
            answer_text=answer_text,
            ai_score=score,
            ai_feedback=feedback,
            is_passed=is_passed
        )
        
        if is_passed:
            UserProgress.objects.update_or_create(
                user=request.user,
                node=node,
                defaults={'is_completed': True, 'score': score}
            )
            messages.success(request, f"✅ Правильно! Оценка {score}/10. Этап пройден.")
        else:
            messages.warning(request, f"❌ Не зачтено. Оценка {score}/10.\n{feedback}\nПопробуйте ещё раз.")
        
        return redirect('subtopic_detail', pk=node.id)