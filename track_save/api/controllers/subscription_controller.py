from api.entities.subscription import Subscription
from api.entities.subscription import SubscriptionType
from api.entities.subscription import SubscriptionUser
from api.entities.user import User

def get_subscriptions():
    return Subscription.objects.all()


def get_all_subscription_user():
    return SubscriptionUser.objects.all()


def update_subscription(subscription_id, data):
    try:
        subscription = Subscription.objects.get(id=subscription_id)

        # Atualiza os campos, se existirem no dict
        for field in ["favorite_quantity", "alert_quantity", "interactions_quantity", "price_htr_quantity", "value"]:
            if field in data:
                setattr(subscription, field, data[field])

        subscription.save()
        return subscription
    except Subscription.DoesNotExist:
        raise ValueError("Plano não encontrado.")


# deleta da tabela de tipos de assinatura, NÃO de assinaturas de users
def delete_subscription(subscription_id):
    try:
        subscription = Subscription.objects.get(id=subscription_id)
        subscription.delete()
    except Subscription.DoesNotExist:
        raise ValueError("Plano não encontrado.")


# usado na criação do usuario para criar um plano
def create_subscription_user(user_id, subscription_type):
    # pra evitar erro de import circular
    from api.controllers.user_controller import get_user_by_id  

    try:
        subscription = Subscription.objects.get(type=subscription_type)
    except Subscription.DoesNotExist:
        raise ValueError(f"Plano '{subscription_type}' não encontrado.")

    user = get_user_by_id(user_id)
    # garantir que só tem uma ativa por usuário
    SubscriptionUser.objects.filter(user=user, is_active=True).update(is_active=False)
    sub_user = SubscriptionUser.objects.create(
               user=user,
               subscription=subscription,
               is_active=True  
            )

    return sub_user

# retorna apenas as assinaturas ativas
def get_subscription_user(user_id):
    try:
        return SubscriptionUser.objects.get(user__id=user_id, is_active=True)
    except SubscriptionUser.DoesNotExist:
        raise ValueError("Usuário não encontrado.")


def update_subscription_user(user_id, new_type):
    if new_type not in SubscriptionType.values:
        raise ValueError("Tipo de plano inválido. Os tipos válidos são: basic, standard, premium.")

    try:
        subscription = Subscription.objects.get(type=new_type)
        sub_user = SubscriptionUser.objects.get(user__id=user_id, is_active=True)
        sub_user.subscription = subscription
        sub_user.save()
        return sub_user
    except (Subscription.DoesNotExist, SubscriptionUser.DoesNotExist):
        raise ValueError("Plano ou usuário não encontrados.")


# o cancelamento de uma assinatura não exclui o registro dela, apenas seta
# is_active como False e cria um novo registro de assinatura Basic ativa.
# caso já exista
def cancel_subscription_user(user_id):
    sub_user = SubscriptionUser.objects.filter(user__id=user_id, is_active=True).first()

    if not sub_user:
        raise ValueError("Assinatura ativa não encontrada.")

    if sub_user.subscription.type == SubscriptionType.BASIC:
        raise ValueError("Assinatura básica não pode ser cancelada.")
    else:
        # assinatura paga — desativa e troca pela básica
        sub_user.is_active = False
        sub_user.save()

        basic_plan = Subscription.objects.get(type=SubscriptionType.BASIC)
        basic = SubscriptionUser.objects.create(
            user=sub_user.user,
            subscription=basic_plan,
            is_active=True
        )
        return basic

# recebe o id correspondente a linha da tabela SubscriptionUser e não user_id
def delete_subscription_user(subscription_id):
    try:
        subscription = SubscriptionUser.objects.get(id=subscription_id)
        subscription.delete()
    except Subscription.DoesNotExist:
        raise ValueError("Assinatura não encontrada.")
