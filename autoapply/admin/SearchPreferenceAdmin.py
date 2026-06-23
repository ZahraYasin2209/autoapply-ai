from sqladmin import ModelView

from autoapply.models import SearchPreference


class SearchPreferenceAdmin(ModelView, model=SearchPreference):
    column_list = [
        SearchPreference.id,
        SearchPreference.user_id,
        SearchPreference.target_role,
        SearchPreference.location,
        SearchPreference.seniority_level,
    ]

    column_details_list = [
        SearchPreference.id,
        SearchPreference.user_id,
        SearchPreference.target_role,
        SearchPreference.location,
        SearchPreference.seniority_level,
        SearchPreference.keywords,
        SearchPreference.excluded_companies,
        SearchPreference.created_at,
        SearchPreference.updated_at,
    ]

    name = "Search Preference"
    name_plural = "Search Preferences"
    icon = "fa-solid fa-sliders"
