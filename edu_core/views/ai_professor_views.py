# Path: Portfolio\Education_Villa\edu_core\views\ai_professor_views.py

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.core.files.storage import default_storage
from django.http import HttpResponseForbidden
from django.contrib import messages
from ..models import Course, CourseCorpus
import os
import nltk
import math
from collections import Counter
from difflib import SequenceMatcher

# Download necessary resources if not already downloaded

from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize


@login_required
def ai_course_professor(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    response = None
    user_is_author_or_superuser = request.user == course.author or request.user.is_superuser
    registered = course.students.filter(id=request.user.id).exists()

    if request.method == "POST":
        # Handle File Upload - Only the author or superuser can upload files
        if 'file_input' in request.FILES and user_is_author_or_superuser:
            file = request.FILES['file_input']
            CourseCorpus.objects.create(course=course, file=file)
            return redirect('ai_course_professor', course_id=course.id)

        # Handle Question Input - Registered users and the author can submit questions
        elif 'query_input' in request.POST and (registered or user_is_author_or_superuser):
            query = request.POST['query_input']
            response = handle_query(course, query)
        else:
            messages.error(request, "You do not have permission to perform this action.")

    # Get all corpus files related to the course
    corpus_files = CourseCorpus.objects.filter(course=course)

    return render(request, 'edu_core/ai_professor.html', {
        'course': course,
        'response': response,
        'corpus_files': corpus_files,
        'user_is_author_or_superuser': user_is_author_or_superuser,
        'registered': registered
    })


@login_required
def delete_corpus_file(request, corpus_id):
    corpus = get_object_or_404(CourseCorpus, id=corpus_id)

    # Ensure only the course author or superuser can delete files
    if request.user != corpus.course.author and not request.user.is_superuser:
        return HttpResponseForbidden("You do not have permission to delete files for this course.")

    # Delete the file and remove the record
    default_storage.delete(corpus.file.name)
    corpus.delete()

    return redirect('ai_course_professor', course_id=corpus.course.id)


def handle_query(course, query):
    # Load all corpus files related to the course
    corpus_files = course.corpus.all()
    if not corpus_files:
        return "No corpus available for this course."

    # Read all files and form a corpus dictionary
    files = {corpus.file.name: corpus.file.read().decode('utf-8') for corpus in corpus_files}
    file_words = {filename: tokenize(content) for filename, content in files.items()}
    file_idfs = compute_idfs(file_words)

    # Tokenize query and find matching files using TF-IDF
    query_tokens = set(tokenize(query))
    top_file = top_files(query_tokens, file_words, file_idfs, n=1)

    if not top_file:
        return "No relevant information found."

    # Extract the best-matching content from the top file
    filename = top_file[0]
    best_sentences = extract_relevant_sentences(files[filename], query_tokens, file_idfs)

    response = f"You asked about: **{query}**. Here's what I found: {best_sentences} If you need more details, feel free to ask!"
    return response


def tokenize(document):
    lower_doc = document.lower()
    words = word_tokenize(lower_doc)
    words = [word for word in words if word.isalpha()]
    words = [word for word in words if word not in stopwords.words('english')]
    return words


def compute_idfs(documents):
    N = len(documents)
    doc_count = Counter()

    for doc in documents.values():
        doc_count.update(set(doc))

    return {word: math.log(N / count) for word, count in doc_count.items()}


def top_files(query, files, idfs, n):
    tf_idfs = {}
    for filename, words in files.items():
        tf_idf = sum(words.count(word) * idfs.get(word, 0) for word in query)
        tf_idfs[filename] = tf_idf

    ranked_files = sorted(tf_idfs.items(), key=lambda x: x[1], reverse=True)
    return [file[0] for file in ranked_files[:n]]


def extract_relevant_sentences(file_content, query_tokens, file_idfs, n=3):
    sentences = nltk.sent_tokenize(file_content)
    sentence_scores = []

    for sentence in sentences:
        tokens = tokenize(sentence)
        idf_score = sum(file_idfs.get(token, 0) for token in tokens if token in query_tokens)
        similarity_score = max((SequenceMatcher(None, token.lower(), qt.lower()).ratio() for qt in query_tokens for token in tokens), default=0)
        combined_score = idf_score + similarity_score
        sentence_scores.append((sentence, combined_score))

    # Sort sentences by combined score in descending order
    ranked_sentences = sorted(sentence_scores, key=lambda x: x[1], reverse=True)
    best_sentences = " ".join([sentence for sentence, score in ranked_sentences[:n]])

    return best_sentences