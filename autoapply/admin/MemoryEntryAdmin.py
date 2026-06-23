from sqladmin import ModelView

from autoapply.models import MemoryEntry


class MemoryEntryAdmin(ModelView, model=MemoryEntry):
    column_list = [
        MemoryEntry.id,
        MemoryEntry.user_id,
        MemoryEntry.entry_type,
        MemoryEntry.source_outcome,
        MemoryEntry.stored_at,
    ]

    column_details_list = [
        MemoryEntry.id,
        MemoryEntry.user_id,
        MemoryEntry.entry_type,
        MemoryEntry.content,
        MemoryEntry.source_outcome,
        MemoryEntry.stored_at,
    ]

    column_searchable_list = [MemoryEntry.content]
    name = "Memory Entry"
    name_plural = "Memory Entries"
    icon = "fa-solid fa-brain"
