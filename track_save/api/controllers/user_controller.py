import os

from django.contrib.auth.hashers import make_password
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.core.validators import validate_email

from api.entities.user import User
from api.entities.user import UserCategory


def get_categories():
    return [{"value": choice.value, "label": choice.label} for choice in UserCategory]


def create_user(name, email, password, categories):
    if not all([name, email, password, categories]):
        raise ValueError("Todos os campos são obrigatórios.")

    try:
        validate_email(email)
    except ValidationError:
        raise ValueError("Formato de email inválido.")

    if User.objects.filter(email=email).exists():
        raise ValueError("Este email já foi cadastrado.")

    if not isinstance(categories, list):
        raise ValueError("categories deve ser uma lista.")

    invalid = [c for c in categories if c not in UserCategory.values]
    if invalid:
        raise ValueError(f"Categorias inválidas: {invalid}")

    user = User.objects.create(
        name=name,
        email=email,
        password=make_password(password),
        is_verified=False,
        categories=categories,
    )

    send_mail(
        subject="Confirmação de email - Track&Save",
        message=f"Obrigado por se cadastrar no Track&Save! Para confirmar o email clique no link abaixo. Link: http://locahost:8001/api/confirm_email/{user.id}/",
        recipient_list=[email],
        from_email=os.getenv("DEFAULT_FROM_EMAIL"),
    )

    return user


def get_user_by_id(user_id):
    return User.objects.get(id=user_id)


def get_user_by_email(user_email):
    return User.objects.get(email=user_email)


def get_all_users():
    return User.objects.all()


def update_user(user_id, name=None, email=None, categories=None):
    user = User.objects.get(id=user_id)

    if name:
        user.name = name
    if email:
        user.email = email

    if categories is not None:
        if not isinstance(categories, list):
            raise ValueError("categories deve ser uma lista.")
        invalid = [c for c in categories if c not in UserCategory.values]
        if invalid:
            raise ValueError(f"Categorias inválidas: {invalid}")
        user.categories = categories

    user.save()
    return user


def update_password(user_id, nova_senha, confirmar_senha):
    if not nova_senha or not confirmar_senha:
        raise ValueError("Preencha todos os campos")

    if nova_senha != confirmar_senha:
        raise ValueError("As senhas precisam ser iguais")

    user = User.objects.get(id=user_id)
    user.password = make_password(nova_senha)
    user.save()
    return user


def delete_user(user_id):
    user = User.objects.get(id=user_id)
    user.delete()
    return


"""
Esboço de método. Pra funcionar precisam ser configuradas constantes em .envs/.local/.django,
tanto pra teste local quando com gmail, fora implementar fluxo com token.
"""


def recover_password(email):
    if not email:
        raise ValueError("Informe o email!")

    try:
        user = User.objects.get(email=email)
    except User.DoesNotExist:
        raise User.DoesNotExist("Este email não pertence a nenhuma conta!")

    link_redefinicao = f"http://localhost:8001/api/update_password/{user.id}"

    send_mail(
        subject="Redefinição de senha da conta Track&Save",
        message=f"Ao clicar no botão abaixo você será redirecionado(a) para o site e poderá redefinir sua senha. \
                  Caso não tenha feito esta solicitação, basta ignorar este email. LINK TESTE: {link_redefinicao}",
        from_email="tracksave@email.com",
        recipient_list=[email],
        fail_silently=False,
    )

    return {"message": "Email enviado com sucesso"}


def confirm_email(user_id):
    if not user_id:
        raise ValueError("Informe um id valido")
    try:
        user = User.objects.get(id=user_id)

        user.is_verified = True
        user.save()
        print("Email confirmado com sucesso")
    except User.DoesNotExist():
        raise User.DoesNotExist("Esse id não pertence a nenhuma conta")
