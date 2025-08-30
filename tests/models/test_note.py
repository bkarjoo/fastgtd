import pytest
import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.models.task_list import TaskList
from app.models.task import Task
from app.models.tag import Tag
from app.models.note import Note
from app.models.enums import TaskStatus, TaskPriority


@pytest.fixture
async def test_user(test_db_session: AsyncSession):
    user = User(
        email="test@example.com",
        password_hash="hashed_password",
        full_name="Test User"
    )
    test_db_session.add(user)
    await test_db_session.commit()
    await test_db_session.refresh(user)
    return user


@pytest.fixture
async def test_task_list(test_db_session: AsyncSession, test_user: User):
    task_list = TaskList(
        owner_id=test_user.id,
        name="Test List",
        description="A test task list"
    )
    test_db_session.add(task_list)
    await test_db_session.commit()
    await test_db_session.refresh(task_list)
    return task_list


@pytest.fixture
async def test_task(test_db_session: AsyncSession, test_task_list: TaskList):
    task = Task(
        list_id=test_task_list.id,
        title="Test Task",
        description="A test task",
        status=TaskStatus.todo,
        priority=TaskPriority.medium
    )
    test_db_session.add(task)
    await test_db_session.commit()
    await test_db_session.refresh(task)
    return task


@pytest.fixture
async def test_tag(test_db_session: AsyncSession, test_user: User):
    tag = Tag(
        owner_id=test_user.id,
        name="test-tag",
        description="A test tag",
        color="#FF0000"
    )
    test_db_session.add(tag)
    await test_db_session.commit()
    await test_db_session.refresh(tag)
    return tag


class TestNoteModel:
    """Test suite for the Note model"""

    async def test_create_note(self, test_db_session: AsyncSession, test_task: Task):
        """Test creating a basic note"""
        note = Note(
            task_id=test_task.id,
            title="Test Note",
            body="This is a test note"
        )
        test_db_session.add(note)
        await test_db_session.commit()
        await test_db_session.refresh(note)

        assert note.id is not None
        assert note.task_id == test_task.id
        assert note.title == "Test Note"
        assert note.body == "This is a test note"
        assert note.created_at is not None
        assert note.updated_at is not None
        assert note.parent_id is None

    async def test_note_requires_task_id(self, test_db_session: AsyncSession):
        """Test that note creation fails without task_id"""
        note = Note(
            title="Test Note",
            body="This is a test note"
        )
        test_db_session.add(note)
        
        with pytest.raises(Exception):  # Should fail due to CheckConstraint
            await test_db_session.commit()

    async def test_note_task_relationship(self, test_db_session: AsyncSession, test_task: Task):
        """Test the relationship between note and task"""
        note = Note(
            task_id=test_task.id,
            title="Test Note",
            body="This is a test note"
        )
        test_db_session.add(note)
        await test_db_session.commit()
        await test_db_session.refresh(note)

        # Test that note has correct task_id
        assert note.task_id == test_task.id

        # Test accessing notes from task via query
        result = await test_db_session.execute(
            select(Note).where(Note.task_id == test_task.id)
        )
        task_notes = result.scalars().all()
        assert len(task_notes) == 1
        assert task_notes[0].id == note.id

    async def test_note_hierarchy_parent_child(self, test_db_session: AsyncSession, test_task: Task):
        """Test note hierarchy with parent and children relationships"""
        # Create parent note
        parent_note = Note(
            task_id=test_task.id,
            title="Parent Note",
            body="This is the parent note"
        )
        test_db_session.add(parent_note)
        await test_db_session.commit()
        await test_db_session.refresh(parent_note)

        # Create child note
        child_note = Note(
            task_id=test_task.id,
            parent_id=parent_note.id,
            title="Child Note",
            body="This is a child note"
        )
        test_db_session.add(child_note)
        await test_db_session.commit()
        await test_db_session.refresh(child_note)

        # Test parent-child relationships
        assert child_note.parent_id == parent_note.id

        # Test querying children
        result = await test_db_session.execute(
            select(Note).where(Note.parent_id == parent_note.id)
        )
        children = result.scalars().all()
        assert len(children) == 1
        assert children[0].id == child_note.id

    async def test_note_hierarchy_cascade_delete(self, test_db_session: AsyncSession, test_task: Task):
        """Test that deleting a parent note cascades to children"""
        # Create parent note
        parent_note = Note(
            task_id=test_task.id,
            title="Parent Note",
            body="This is the parent note"
        )
        test_db_session.add(parent_note)
        await test_db_session.commit()
        await test_db_session.refresh(parent_note)

        # Create child notes
        child1 = Note(
            task_id=test_task.id,
            parent_id=parent_note.id,
            title="Child Note 1",
            body="This is child note 1"
        )
        child2 = Note(
            task_id=test_task.id,
            parent_id=parent_note.id,
            title="Child Note 2",
            body="This is child note 2"
        )
        test_db_session.add_all([child1, child2])
        await test_db_session.commit()

        child1_id = child1.id
        child2_id = child2.id

        # Delete parent note
        await test_db_session.delete(parent_note)
        await test_db_session.commit()

        # Verify children are also deleted
        result = await test_db_session.execute(
            select(Note).where(Note.id.in_([child1_id, child2_id]))
        )
        remaining_notes = result.scalars().all()
        assert len(remaining_notes) == 0

    async def test_note_tag_relationship(self, test_db_session: AsyncSession, test_task: Task, test_tag: Tag):
        """Test many-to-many relationship between notes and tags"""
        note = Note(
            task_id=test_task.id,
            title="Test Note",
            body="This is a test note"
        )
        test_db_session.add(note)
        await test_db_session.commit()
        await test_db_session.refresh(note)

        # Add tag to note by inserting into junction table
        from app.models.associations import note_tags
        await test_db_session.execute(
            note_tags.insert().values(note_id=note.id, tag_id=test_tag.id)
        )
        await test_db_session.commit()

        # Test that the relationship was created by querying the junction table
        result = await test_db_session.execute(
            select(note_tags).where(
                (note_tags.c.note_id == note.id) & 
                (note_tags.c.tag_id == test_tag.id)
            )
        )
        association = result.first()
        assert association is not None

    async def test_note_linking_relationships(self, test_db_session: AsyncSession, test_task: Task):
        """Test note-to-note linking relationships"""
        # Create source note
        source_note = Note(
            task_id=test_task.id,
            title="Source Note",
            body="This note links to other notes"
        )
        test_db_session.add(source_note)
        await test_db_session.commit()
        await test_db_session.refresh(source_note)

        # Create target notes
        target_note1 = Note(
            task_id=test_task.id,
            title="Target Note 1",
            body="This is the first target note"
        )
        target_note2 = Note(
            task_id=test_task.id,
            title="Target Note 2",
            body="This is the second target note"
        )
        test_db_session.add_all([target_note1, target_note2])
        await test_db_session.commit()
        await test_db_session.refresh(target_note1)
        await test_db_session.refresh(target_note2)

        # Create links by inserting into junction table
        from app.models.associations import note_links
        await test_db_session.execute(
            note_links.insert().values([
                {"source_note_id": source_note.id, "target_note_id": target_note1.id},
                {"source_note_id": source_note.id, "target_note_id": target_note2.id}
            ])
        )
        await test_db_session.commit()

        # Test that links were created by querying the junction table
        result = await test_db_session.execute(
            select(note_links).where(note_links.c.source_note_id == source_note.id)
        )
        links = result.fetchall()
        assert len(links) == 2
        
        target_ids = {link.target_note_id for link in links}
        assert target_note1.id in target_ids
        assert target_note2.id in target_ids

    async def test_note_multiple_tags(self, test_db_session: AsyncSession, test_task: Task, test_user: User):
        """Test a note with multiple tags"""
        # Create additional tags
        tag1 = Tag(owner_id=test_user.id, name="tag1", color="#FF0000")
        tag2 = Tag(owner_id=test_user.id, name="tag2", color="#00FF00")
        tag3 = Tag(owner_id=test_user.id, name="tag3", color="#0000FF")
        test_db_session.add_all([tag1, tag2, tag3])
        await test_db_session.commit()

        # Create note with multiple tags
        note = Note(
            task_id=test_task.id,
            title="Multi-tag Note",
            body="This note has multiple tags"
        )
        test_db_session.add(note)
        await test_db_session.commit()
        await test_db_session.refresh(note)

        # Add tags by inserting into junction table
        from app.models.associations import note_tags
        await test_db_session.execute(
            note_tags.insert().values([
                {"note_id": note.id, "tag_id": tag1.id},
                {"note_id": note.id, "tag_id": tag2.id},
                {"note_id": note.id, "tag_id": tag3.id}
            ])
        )
        await test_db_session.commit()

        # Verify all tags are associated by querying the junction table
        from app.models.associations import note_tags
        result = await test_db_session.execute(
            select(note_tags).where(note_tags.c.note_id == note.id)
        )
        associations = result.fetchall()
        assert len(associations) == 3

    async def test_complex_note_hierarchy(self, test_db_session: AsyncSession, test_task: Task):
        """Test complex note hierarchy with multiple levels"""
        # Create root note
        root_note = Note(
            task_id=test_task.id,
            title="Root Note",
            body="This is the root note"
        )
        test_db_session.add(root_note)
        await test_db_session.commit()
        await test_db_session.refresh(root_note)

        # Create level 1 children
        child1 = Note(
            task_id=test_task.id,
            parent_id=root_note.id,
            title="Child 1",
            body="First child"
        )
        child2 = Note(
            task_id=test_task.id,
            parent_id=root_note.id,
            title="Child 2",
            body="Second child"
        )
        test_db_session.add_all([child1, child2])
        await test_db_session.commit()
        await test_db_session.refresh(child1)
        await test_db_session.refresh(child2)

        # Create level 2 children (grandchildren)
        grandchild1 = Note(
            task_id=test_task.id,
            parent_id=child1.id,
            title="Grandchild 1",
            body="First grandchild"
        )
        grandchild2 = Note(
            task_id=test_task.id,
            parent_id=child1.id,
            title="Grandchild 2",
            body="Second grandchild"
        )
        test_db_session.add_all([grandchild1, grandchild2])
        await test_db_session.commit()

        # Verify hierarchy structure through queries
        # Check level 1 children
        result = await test_db_session.execute(
            select(Note).where(Note.parent_id == root_note.id)
        )
        level1_children = result.scalars().all()
        assert len(level1_children) == 2

        # Check level 2 children (grandchildren under child1)
        result = await test_db_session.execute(
            select(Note).where(Note.parent_id == child1.id)
        )
        level2_children = result.scalars().all()
        assert len(level2_children) == 2

        # Check that child2 has no children
        result = await test_db_session.execute(
            select(Note).where(Note.parent_id == child2.id)
        )
        child2_children = result.scalars().all()
        assert len(child2_children) == 0

    async def test_note_delete_preserves_links(self, test_db_session: AsyncSession, test_task: Task):
        """Test that deleting a note removes its links but preserves other notes"""
        # Create three notes
        note1 = Note(task_id=test_task.id, title="Note 1", body="First note")
        note2 = Note(task_id=test_task.id, title="Note 2", body="Second note")
        note3 = Note(task_id=test_task.id, title="Note 3", body="Third note")
        test_db_session.add_all([note1, note2, note3])
        await test_db_session.commit()

        # Create links: note1 -> note2, note1 -> note3, note2 -> note3
        from app.models.associations import note_links
        await test_db_session.execute(
            note_links.insert().values([
                {"source_note_id": note1.id, "target_note_id": note2.id},
                {"source_note_id": note1.id, "target_note_id": note3.id},
                {"source_note_id": note2.id, "target_note_id": note3.id}
            ])
        )
        await test_db_session.commit()

        note2_id = note2.id
        note3_id = note3.id

        # Delete note1
        await test_db_session.delete(note1)
        await test_db_session.commit()

        # Verify note2 and note3 still exist
        result = await test_db_session.execute(
            select(Note).where(Note.id.in_([note2_id, note3_id]))
        )
        remaining_notes = result.scalars().all()
        assert len(remaining_notes) == 2

        # Verify note2 -> note3 link still exists by querying junction table
        result = await test_db_session.execute(
            select(note_links).where(
                (note_links.c.source_note_id == note2_id) &
                (note_links.c.target_note_id == note3_id)
            )
        )
        link = result.first()
        assert link is not None