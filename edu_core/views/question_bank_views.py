# Portfolio\Education_Villa\edu_core\views\question_bank_views.py

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.forms import inlineformset_factory, formset_factory
from django.contrib import messages
from django.http import HttpResponseForbidden
from ..models import Question, Course, Option
from ..forms import QuestionBankForm, MCQForm, OptionForm, ContentBlockForm

@login_required
def question_bank(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    query = request.GET.get('q', '')
    questions = Question.objects.filter(course=course, in_bank=True)
    
    if query:
        questions = questions.filter(
            Q(key_name__icontains=query) | Q(text__icontains=query)
        )

    return render(request, 'edu_core/question_bank/question_bank.html', {'course': course, 'questions': questions})


@login_required
def add_question_to_bank(request, course_id):
    """
    Redirect to the question type selection template for adding a new question.
    """
    course = get_object_or_404(Course, id=course_id)
    return render(request, 'edu_core/activity/views/question_type_selection.html', {'course': course})


@login_required
def add_mcq_to_bank(request, course_id):
    """
    Add a new multiple-choice question to the question bank.
    """
    course = get_object_or_404(Course, id=course_id)
    OptionFormSet = formset_factory(OptionForm, extra=0, min_num=2, validate_min=True)

    if request.method == 'POST':
        form = MCQForm(request.POST)
        option_formset = OptionFormSet(request.POST, prefix='form')  # Use the same prefix as the working view

        # Print statements for debugging
        print("===== DEBUG INFO =====")
        print("POST Data:", request.POST)
        
        # Validate the forms before saving
        form_valid = form.is_valid()
        formset_valid = option_formset.is_valid()
        print("MCQ Form is valid:", form_valid)
        print("Option Formset is valid:", formset_valid)

        if not form_valid:
            print("MCQ Form errors:", form.errors)
        if not formset_valid:
            print("Option Formset errors:", option_formset.errors)
            print("Non-form errors:", option_formset.non_form_errors())

        if form_valid and formset_valid:
            # Validate that a correct option is selected
            correct_option = request.POST.get('correct_option')
            min_options_filled = sum(1 for form in option_formset if form.cleaned_data.get('text')) >= 2

            # Validate that the correct option is valid and corresponds to a non-empty option
            valid_options = False
            if correct_option is not None and correct_option.isdigit():
                idx = int(correct_option)
                if 0 <= idx < len(option_formset.forms):
                    selected_form = option_formset.forms[idx]
                    if selected_form.cleaned_data.get('text'):
                        valid_options = True

            # Save the question and related options if valid
            if valid_options and min_options_filled:
                question = form.save(commit=False)
                question.course = course
                question.question_type = Question.MULTIPLE_CHOICE
                question.in_bank = True
                question.save()

                # Save each option for the question
                for idx, option_form in enumerate(option_formset):
                    if option_form.cleaned_data.get('text'):
                        option = option_form.save(commit=False)
                        option.question = question
                        option.is_correct = (str(idx) == correct_option)  # Mark the correct option
                        option.save()

                messages.success(request, 'Question successfully added to the bank.')
                print("===== SUCCESS: Question Added =====")
                return redirect('question_bank', course_id=course.id)
            else:
                messages.error(request, 'You must select at least one correct answer.')
                print("===== ERROR: No correct answer selected =====")
        else:
            messages.error(request, 'There was an error in the form. Please correct the highlighted errors.')
            print("===== ERROR: Form or Formset Invalid =====")
    
    else:
        form = MCQForm()
        option_formset = OptionFormSet(prefix='form')

    return render(request, 'edu_core/activity/forms/mcq_creator.html', {
        'mcq_form': form,
        'option_formset': option_formset,
        'course': course,
        'editing': False,  # Set editing to False since we're creating a new question
    })


@login_required
def edit_question(request, question_id):
    """
    Redirects to the appropriate edit view based on the question type.
    """
    question = get_object_or_404(Question, id=question_id)
    
    # Debugging statements
    print(f"=== DEBUG INFO ===")
    print(f"Question ID: {question.id}")
    print(f"Question Type: {question.question_type}")
    print(f"===================")

    if question.question_type == Question.MULTIPLE_CHOICE:
        print("Redirecting to edit_mcq_from_bank view")
        return edit_mcq_from_bank(request, question_id)
    elif question.question_type == Question.CONTENT_BLOCK:
        print("Redirecting to edit_content_block view")
        return edit_content_block(request, question_id)
    else:
        print("Unsupported question type. Permission forbidden.")
        return HttpResponseForbidden("Editing this type of question is not supported.")


@login_required
def edit_mcq_from_bank(request, question_id):
    """
    Edit an existing multiple-choice question in the course question bank.
    """
    question = get_object_or_404(Question, id=question_id)

    # Ensure the user is allowed to edit the question (author or superuser)
    if request.user != question.course.author and not request.user.is_superuser:
        return HttpResponseForbidden("You do not have permission to edit this question.")

    # Create an inline formset for options related to the question
    OptionFormSet = inlineformset_factory(
        Question,
        Option,
        form=OptionForm,
        extra=0,  # No extra empty forms
        can_delete=True  # Allow options to be marked for deletion
    )

    if request.method == 'POST':
        form = MCQForm(request.POST, instance=question)
        option_formset = OptionFormSet(request.POST, instance=question, prefix='form')

        if form.is_valid() and option_formset.is_valid():
            # Save the question form first
            question = form.save()

            # Get the 'correct_option' value from POST data
            correct_option_index = request.POST.get('correct_option')
            if correct_option_index is not None and correct_option_index.isdigit():
                correct_option_index = int(correct_option_index)
            else:
                correct_option_index = None

            # Iterate over the forms in the formset and set 'is_correct'
            for i, option_form in enumerate(option_formset.forms):
                if i == correct_option_index:
                    option_form.instance.is_correct = True
                else:
                    option_form.instance.is_correct = False

            # Save the options formset, including deletions
            option_formset.save()

            messages.success(request, 'Question successfully updated.')
            return redirect('question_bank', course_id=question.course.id)
        else:
            # Add messages for debugging purposes if validation fails
            messages.error(request, "There was an error updating the question. Please review the form.")
            print(form.errors)
            print(option_formset.errors)
    else:
        form = MCQForm(instance=question)
        option_formset = OptionFormSet(instance=question, prefix='form')

    return render(request, 'edu_core/question_bank/edit_question_in_bank.html', {
        'form': form,
        'option_formset': option_formset,
        'question': question,
        'course': question.course,
        'editing': True,
    })


@login_required
def add_content_block_to_bank(request, course_id):
    """
    Add a new content block question to the question bank.
    """
    course = get_object_or_404(Course, id=course_id)

    if request.method == 'POST':
        form = ContentBlockForm(request.POST, request.FILES)
        if form.is_valid():
            content_block = form.save(commit=False)
            content_block.course = course
            content_block.question_type = Question.CONTENT_BLOCK
            content_block.in_bank = True
            content_block.save()
            messages.success(request, 'Content Block successfully added to the bank.')
            return redirect('question_bank', course_id=course.id)
    else:
        form = ContentBlockForm()

    return render(request, 'edu_core/activity/forms/cb_creator.html', {
        'form': form,
        'course': course,
        'editing': False,
        'question': None
    })


@login_required
def edit_content_block(request, question_id):
    """
    Edit an existing content block question in the bank.
    """
    question = get_object_or_404(Question, id=question_id)

    # Ensure the user is allowed to edit the question (author or superuser)
    if request.user != question.course.author and not request.user.is_superuser:
        return HttpResponseForbidden("You do not have permission to edit this question.")

    if request.method == 'POST':
        form = ContentBlockForm(request.POST, request.FILES, instance=question)
        if form.is_valid():
            content_block = form.save(commit=False)
            content_block.in_bank = True
            content_block.save()
            messages.success(request, 'Content Block successfully updated.')
            return redirect('question_bank', course_id=question.course.id)
    else:
        form = ContentBlockForm(instance=question)

    return render(request, 'edu_core/activity/forms/cb_creator.html', {
        'form': form,
        'course': question.course,
        'editing': True,
        'question': question
    })


@login_required
def question_type_selection_for_bank(request, course_id):
    """
    Show the question type selection page to add a new question to the bank.
    """
    course = get_object_or_404(Course, id=course_id)
    return render(request, 'edu_core/activity/views/question_type_selection.html', {'course': course})


@login_required
def delete_question(request, question_id):
    """
    Delete a question from the course bank.
    Only the course author or a superuser can delete a question.
    """
    question = get_object_or_404(Question, id=question_id)
    
    # Ensure only the course author or superuser can delete the question
    if request.user != question.course.author and not request.user.is_superuser:
        return HttpResponseForbidden("You do not have permission to delete this question.")

    if request.method == 'POST':
        question.delete()
        messages.success(request, 'Question successfully deleted.')
        return redirect('question_bank', course_id=question.course.id)
    else:
        return HttpResponseForbidden("Invalid request method.")
