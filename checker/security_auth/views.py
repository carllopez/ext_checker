from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from .forms import UserRegistrationForm, SecurityQuestionForm
from .models import SecurityQuestion
from django.contrib.auth.hashers import make_password, check_password

# The main view to handle both login and security question challenge.
def login_and_challenge_view(request):
    if request.method == 'POST':
        # Stage 1: Standard login form submission
        if 'login_form' in request.POST:
            form = AuthenticationForm(request, data=request.POST)
            if form.is_valid():
                username = form.cleaned_data.get('username')
                password = form.cleaned_data.get('password')
                user = authenticate(username=username, password=password)
                if user is not None:
                    # Check if the user has a security question set up
                    try:
                        security_question = SecurityQuestion.objects.get(user=user)
                        # If a security question exists, store user info in session
                        # and redirect to the challenge page.
                        request.session['temp_user_id'] = user.id
                        return redirect('security_challenge')
                    except SecurityQuestion.DoesNotExist:
                        # No security question, so log the user in directly.
                        login(request, user)
                        return redirect('home')
                else:
                    return render(request, 'login.html', {'login_form': form, 'error': 'Invalid username or password.'})
            else:
                return render(request, 'login.html', {'login_form': form})

        # Stage 2: Security question form submission
        if 'challenge_form' in request.POST:
            challenge_form = SecurityQuestionForm(request.POST)
            user_id = request.session.get('temp_user_id')
            if user_id and challenge_form.is_valid():
                try:
                    user = User.objects.get(id=user_id)
                    security_question = SecurityQuestion.objects.get(user=user)
                    provided_answer = challenge_form.cleaned_data['answer']
                    # Use Django's check_password for secure comparison
                    if check_password(provided_answer, security_question.answer_hash):
                        # Answer is correct, authenticate the user and clear the session variable.
                        login(request, user)
                        del request.session['temp_user_id']
                        return redirect('home')
                    else:
                        return render(request, 'security_challenge.html', {'challenge_form': challenge_form, 'question': security_question.question, 'error': 'Incorrect answer.'})
                except (User.DoesNotExist, SecurityQuestion.DoesNotExist):
                    return redirect('login_and_challenge') # Handle edge case where user/question is not found

    else:
        # Initial GET request for the login page
        form = AuthenticationForm()
        # Check if we are coming from the login view and need to display the challenge.
        user_id = request.session.get('temp_user_id')
        if user_id:
            try:
                user = User.objects.get(id=user_id)
                security_question = SecurityQuestion.objects.get(user=user)
                challenge_form = SecurityQuestionForm()
                return render(request, 'security_challenge.html', {'challenge_form': challenge_form, 'question': security_question.question})
            except (User.DoesNotExist, SecurityQuestion.DoesNotExist):
                # Something went wrong, just show the login form
                if 'temp_user_id' in request.session:
                    del request.session['temp_user_id']
                form = AuthenticationForm()
        
    return render(request, 'login.html', {'login_form': form})


def register_view(request):
    if request.method == 'POST':
        user_form = UserRegistrationForm(request.POST)
        security_form = SecurityQuestionForm(request.POST)
        if user_form.is_valid() and security_form.is_valid():
            # Create the user and set a hashed password
            new_user = user_form.save(commit=False)
            new_user.set_password(user_form.cleaned_data['password'])
            new_user.save()

            # Hash the security question answer
            hashed_answer = make_password(security_form.cleaned_data['answer'])

            # Create and save the SecurityQuestion object
            SecurityQuestion.objects.create(
                user=new_user,
                question=security_form.cleaned_data['question'],
                answer_hash=hashed_answer
            )

            return redirect('login_and_challenge')
    else:
        user_form = UserRegistrationForm()
        security_form = SecurityQuestionForm()
    
    return render(request, 'register.html', {
        'user_form': user_form,
        'security_form': security_form
    })


@login_required
def home_view(request):
    return render(request, 'home.html', {})

def logout_view(request):
    from django.contrib.auth import logout
    logout(request)
    return redirect('login_and_challenge')