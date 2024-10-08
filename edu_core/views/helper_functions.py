# Portfolio\Education_Villa\edu_core\views\helper_functions.py

from django.db import transaction
from django.db.models import F, Max
from ..models import ActivityQuestion, Question

def update_page_numbers(activity):
    """
    Update page numbers for all activity questions based on their order.
    """
    activity_questions = ActivityQuestion.objects.filter(activity=activity).order_by('order')
    current_page_number = 1
    for aq in activity_questions:
        if aq.is_separator:
            current_page_number += 1
        aq.page_number = current_page_number
        aq.save(update_fields=['page_number'])


def correct_question_order(activity):
    """
    Ensure that the order of questions is sequential and correct.
    """
    activity_questions = ActivityQuestion.objects.filter(activity=activity).order_by('order')
    expected_order = 1
    with transaction.atomic():
        for aq in activity_questions:
            if aq.order != expected_order:
                aq.order = expected_order
                aq.save(update_fields=['order'])
            expected_order += 1


def adjust_orders_for_insertion(activity, insert_after_order, increment_by=1):
    """
    Adjust the order of all activity questions after the given order to make room for a new question.

    Args:
        activity: The activity for which questions' orders need adjustment.
        insert_after_order: The order after which new question is to be inserted.
        increment_by: The value to increment the order by (default is 1).
    """
    ActivityQuestion.objects.filter(activity=activity, order__gt=insert_after_order).update(order=F('order') + increment_by)


def get_page_number_for_insertion(activity, insert_after_order):
    """
    Get the page number for inserting a new question.

    Args:
        activity: The activity where the new question is being inserted.
        insert_after_order: The order after which the new question is to be inserted.

    Returns:
        The page number where the new question should be inserted.
    """
    previous_question = ActivityQuestion.objects.filter(activity=activity, order=insert_after_order).first()
    return previous_question.page_number if previous_question else 1
