from sqladmin import ModelView

from autoapply.models import User


class UserAdmin(ModelView, model=User):
    column_list = [
        User.id,
        User.name,
        User.email,
        User.created_at
    ]

    column_details_list = [
        User.id,
        User.name,
        User.email,
        User.created_at,
        User.updated_at
    ]

    column_searchable_list = [User.email, User.name]
    column_sortable_list = [User.created_at, User.email]
    name = "User"
    name_plural = "Users"
    icon = "fa-solid fa-user"
