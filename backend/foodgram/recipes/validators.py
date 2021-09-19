from rest_framework.serializers import ValidationError


def validator_amount(value):
    if value < 0:
        raise ValidationError(
            'Жадина. Нужно не меньше 0',
            code='invalid',
            params={'value': value}
        )


def validator_time(value):
    if value < 1:
        raise ValidationError(
            'Слишком быстро. Нужно больше 1',
            code='invalid',
            params={'value': value}
        )


def validate_subscribe(user, author):
    user_id = user.id
    author_id = author.id
    if user_id == author_id:
        raise ValidationError(
               'вы не можете подписаться на себя'
        )
