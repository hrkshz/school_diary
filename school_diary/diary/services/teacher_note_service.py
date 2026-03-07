"""Teacher note business logic."""

from school_diary.diary.constants import NoteSettings
from school_diary.diary.models import TeacherNote
from school_diary.diary.models import TeacherNoteReadStatus


class TeacherNoteService:
    """Operations for teacher notes and read states."""

    @staticmethod
    def validate_note(note: str) -> str:
        """Validate and normalize note text."""
        normalized_note = note.strip()
        if len(normalized_note) < NoteSettings.MIN_NOTE_LENGTH:
            msg = f"メモは{NoteSettings.MIN_NOTE_LENGTH}文字以上で入力してください。"
            raise ValueError(msg)
        return normalized_note

    @classmethod
    def create_note(cls, *, teacher, student, note: str, is_shared: bool):
        """Create a teacher note."""
        return TeacherNote.objects.create(
            teacher=teacher,
            student=student,
            note=cls.validate_note(note),
            is_shared=is_shared,
        )

    @classmethod
    def update_teacher_note(cls, note_obj, *, note: str, is_shared: bool):
        """Update an existing teacher note."""
        note_obj.note = cls.validate_note(note)
        note_obj.is_shared = is_shared
        note_obj.save(update_fields=["note", "is_shared", "updated_at"])
        return note_obj

    @staticmethod
    def delete_note(note_obj):
        """Delete a teacher note."""
        note_obj.delete()

    @staticmethod
    def mark_shared_note_read(*, teacher, note):
        """Create read state idempotently for a shared note."""
        return TeacherNoteReadStatus.objects.get_or_create(
            teacher=teacher,
            note=note,
        )
