from django.views.generic import ListView, DetailView, CreateView, FormView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import redirect, get_object_or_404
from django.urls import reverse_lazy, reverse
from django.contrib import messages
from .models import Challenge, ChallengeSubmission
from .forms import ChallengeSubmitForm, ChallengeGenerationForm
from .ai import generate_challenge, evaluate_challenge_solution
import markdown

class ChallengeListView(LoginRequiredMixin, ListView):
    model = Challenge
    template_name = 'challenges/challenge_list.html'
    context_object_name = 'challenges'
    paginate_by = 12

    def get_queryset(self):
        qs = super().get_queryset()
        language = self.request.GET.get('language')
        difficulty = self.request.GET.get('difficulty')
        if language:
            qs = qs.filter(language=language)
        if difficulty:
            qs = qs.filter(difficulty=difficulty)
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Добавляем фильтры в контекст для формы
        context['current_language'] = self.request.GET.get('language', '')
        context['current_difficulty'] = self.request.GET.get('difficulty', '')
        context['languages'] = Challenge.LANGUAGE_CHOICES
        context['difficulties'] = Challenge.DIFFICULTY_CHOICES
        return context

class ChallengeDetailView(LoginRequiredMixin, DetailView):
    model = Challenge
    template_name = 'challenges/challenge_detail.html'
    context_object_name = 'challenge'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        challenge = self.get_object()
        user = self.request.user

        context['description_html'] = markdown.markdown(
            challenge.description,
            extensions=[
                'markdown.extensions.fenced_code',
                'markdown.extensions.tables',     
                'markdown.extensions.nl2br', 
            ]
        )

        last_submission = ChallengeSubmission.objects.filter(
            user=user,
            challenge=challenge
        ).order_by('-created_at').first() # Берем самую свежую
        
        context['last_submission'] = last_submission

        initial_code = ""
        if last_submission:
            initial_code = last_submission.code
        elif challenge.starter_code:
            initial_code = challenge.starter_code

        context['form'] = ChallengeSubmitForm(initial={'code': initial_code})
        
        return context
    

class ChallengeSubmitView(LoginRequiredMixin, CreateView):
    model = ChallengeSubmission
    form_class = ChallengeSubmitForm
    http_method_names = ['post']

    def dispatch(self, request, *args, **kwargs):
        self.challenge = get_object_or_404(Challenge, pk=kwargs['pk'])
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        # Сохраняем сабмишн без оценки
        submission = form.save(commit=False)
        submission.user = self.request.user
        submission.challenge = self.challenge
        submission.save()

        # Вызываем AI оценку
        result = evaluate_challenge_solution(
            problem_description=self.challenge.description,
            user_code=submission.code,
            language=self.challenge.language
        )
        submission.ai_score = result['score']
        submission.ai_feedback = result['feedback']
        submission.is_passed = result['score'] >= 7
        submission.save()

        messages.success(self.request, f"Решение проверено! Оценка: {submission.ai_score}/10")
        if not submission.is_passed:
            messages.warning(self.request, "Попробуйте улучшить решение и отправить снова.")
        else:
            messages.success(self.request, "Поздравляем! Задача решена верно.")

        return redirect('challenge_detail', pk=self.challenge.pk)

    def form_invalid(self, form):
        messages.error(self.request, "Ошибка в форме. Проверьте код.")
        return redirect('challenge_detail', pk=self.challenge.pk)

class GenerateChallengeView(LoginRequiredMixin, UserPassesTestMixin, FormView):
    template_name = 'challenges/generate_challenge.html'
    form_class = ChallengeGenerationForm
    success_url = reverse_lazy('challenge_list')

    def test_func(self):
        return self.request.user.is_staff

    def form_valid(self, form):
        language = form.cleaned_data['language']
        difficulty = form.cleaned_data['difficulty']

        data = generate_challenge(language, difficulty)

        challenge = Challenge.objects.create(
            title=data['title'],
            description=data['description'],
            starter_code=data['starter_code'],
            solution_hint=data['solution_hint'],
            language=language,
            difficulty=difficulty,
            created_by=self.request.user
        )
        messages.success(self.request, f"Задача '{challenge.title}' успешно создана!")
        return redirect('challenge_detail', pk=challenge.pk)