import pytest
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from httpx import AsyncClient

from app.models.user import User
from app.models.task_list import TaskList
from app.models.task import Task
from app.models.tag import Tag
from app.models.note import Note
from app.models.enums import TaskStatus, TaskPriority


@pytest.fixture
async def test_user(client: AsyncClient, override_get_db):
    """Create a test user and return user data with auth token"""
    # Signup user
    signup_response = await client.post(
        "/auth/signup",
        json={
            "email": "test@example.com",
            "password": "testpassword",
            "full_name": "Test User",
        },
    )
    assert signup_response.status_code == 201
    user_data = signup_response.json()
    
    # Login to get token
    login_response = await client.post(
        "/auth/login",
        json={
            "email": "test@example.com",
            "password": "testpassword",
        },
    )
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]
    
    return {
        "id": user_data["id"],
        "email": user_data["email"],
        "full_name": user_data["full_name"],
        "token": token
    }


@pytest.fixture
async def auth_headers(test_user):
    """Provide authentication headers for requests"""
    return {"Authorization": f"Bearer {test_user['token']}"}


@pytest.fixture
async def test_user_model(test_db_session: AsyncSession, test_user):
    """Get the actual User model from the database"""
    from sqlalchemy import select
    import uuid
    user_id = uuid.UUID(test_user["id"])
    result = await test_db_session.execute(
        select(User).where(User.id == user_id)
    )
    return result.scalar_one()


@pytest.fixture
async def test_task_list(test_db_session: AsyncSession, test_user_model: User):
    task_list = TaskList(
        owner_id=test_user_model.id,
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
async def test_tag(test_db_session: AsyncSession, test_user_model: User):
    tag = Tag(
        owner_id=test_user_model.id,
        name="test-tag",
        description="A test tag",
        color="#FF0000"
    )
    test_db_session.add(tag)
    await test_db_session.commit()
    await test_db_session.refresh(tag)
    return tag


@pytest.fixture
async def test_note(test_db_session: AsyncSession, test_task: Task):
    note = Note(
        task_id=test_task.id,
        title="Test Note",
        body="This is a test note"
    )
    test_db_session.add(note)
    await test_db_session.commit()
    await test_db_session.refresh(note)
    return note


class TestNotesAPI:
    """Test suite for the Notes API endpoints"""

    async def test_create_note_success(self, client: AsyncClient, override_get_db, test_task: Task, auth_headers):
        """Test successful note creation"""
        note_data = {
            "task_id": str(test_task.id),
            "title": "New Note",
            "body": "This is a new note"
        }
        
        response = await client.post("/notes", json=note_data, headers=auth_headers)
        
        assert response.status_code == 201
        data = response.json()
        assert data["task_id"] == str(test_task.id)
        assert data["title"] == "New Note"
        assert data["body"] == "This is a new note"
        assert data["parent_id"] is None
        assert "id" in data
        assert "created_at" in data
        assert "updated_at" in data

    async def test_create_note_with_parent(self, client: AsyncClient, override_get_db, test_note: Note, test_task: Task, auth_headers):
        """Test creating a note with a parent"""
        note_data = {
            "task_id": str(test_task.id),
            "title": "Child Note",
            "body": "This is a child note",
            "parent_id": str(test_note.id)
        }
        
        response = await client.post("/notes", json=note_data, headers=auth_headers)
        
        assert response.status_code == 201
        data = response.json()
        assert data["parent_id"] == str(test_note.id)
        assert data["title"] == "Child Note"

    async def test_create_note_missing_task_id(self, client: AsyncClient, override_get_db, auth_headers):
        """Test note creation fails without task_id"""
        note_data = {
            "title": "New Note",
            "body": "This is a new note"
        }
        
        response = await client.post("/notes", json=note_data, headers=auth_headers)
        
        assert response.status_code == 422  # Validation error

    async def test_create_note_invalid_task_id(self, client: AsyncClient, override_get_db, auth_headers):
        """Test note creation fails with invalid task_id"""
        note_data = {
            "task_id": str(uuid.uuid4()),  # Non-existent task
            "title": "New Note",
            "body": "This is a new note"
        }
        
        response = await client.post("/notes", json=note_data, headers=auth_headers)
        
        assert response.status_code == 404

    async def test_create_note_invalid_parent(self, client: AsyncClient, override_get_db, test_task: Task, auth_headers):
        """Test note creation fails with invalid parent_id"""
        note_data = {
            "task_id": str(test_task.id),
            "title": "New Note",
            "body": "This is a new note",
            "parent_id": str(uuid.uuid4())  # Non-existent parent
        }
        
        response = await client.post("/notes", json=note_data, headers=auth_headers)
        
        assert response.status_code == 404

    async def test_list_notes_by_task(self, client: AsyncClient, override_get_db, test_task: Task, test_note: Note, auth_headers):
        """Test listing notes by task_id"""
        response = await client.get(f"/notes?task_id={test_task.id}", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        assert any(note["id"] == str(test_note.id) for note in data)

    async def test_list_notes_missing_task_id(self, client: AsyncClient, override_get_db, auth_headers):
        """Test listing notes fails without task_id"""
        response = await client.get("/notes", headers=auth_headers)
        
        assert response.status_code == 422  # Validation error

    async def test_get_note_success(self, client: AsyncClient, override_get_db, test_note: Note, auth_headers):
        """Test getting a specific note"""
        response = await client.get(f"/notes/{test_note.id}", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(test_note.id)
        assert data["title"] == test_note.title
        assert data["body"] == test_note.body

    async def test_get_note_not_found(self, client: AsyncClient, override_get_db, auth_headers):
        """Test getting non-existent note"""
        response = await client.get(f"/notes/{uuid.uuid4()}", headers=auth_headers)
        
        assert response.status_code == 404

    async def test_update_note_success(self, client: AsyncClient, override_get_db, test_note: Note, auth_headers):
        """Test updating a note"""
        update_data = {
            "title": "Updated Title",
            "body": "Updated body content"
        }
        
        response = await client.patch(f"/notes/{test_note.id}", json=update_data, headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Updated Title"
        assert data["body"] == "Updated body content"

    async def test_update_note_parent(self, client: AsyncClient, override_get_db, test_db_session: AsyncSession, test_task: Task, auth_headers):
        """Test updating note parent"""
        # Create parent note
        parent_note = Note(
            task_id=test_task.id,
            title="Parent Note",
            body="Parent note body"
        )
        test_db_session.add(parent_note)
        await test_db_session.commit()
        await test_db_session.refresh(parent_note)

        # Create child note
        child_note = Note(
            task_id=test_task.id,
            title="Child Note",
            body="Child note body"
        )
        test_db_session.add(child_note)
        await test_db_session.commit()
        await test_db_session.refresh(child_note)

        update_data = {
            "parent_id": str(parent_note.id)
        }
        
        response = await client.patch(f"/notes/{child_note.id}", json=update_data, headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["parent_id"] == str(parent_note.id)

    async def test_delete_note_success(self, client: AsyncClient, override_get_db, test_note: Note, auth_headers):
        """Test deleting a note"""
        response = await client.delete(f"/notes/{test_note.id}", headers=auth_headers)
        
        assert response.status_code == 204
        
        # Verify note is deleted
        get_response = await client.get(f"/notes/{test_note.id}", headers=auth_headers)
        assert get_response.status_code == 404

    async def test_get_note_children(self, client: AsyncClient, override_get_db, test_db_session: AsyncSession, test_task: Task, auth_headers):
        """Test getting child notes"""
        # Create parent note
        parent_note = Note(
            task_id=test_task.id,
            title="Parent Note",
            body="Parent note body"
        )
        test_db_session.add(parent_note)
        await test_db_session.commit()
        await test_db_session.refresh(parent_note)

        # Create child notes
        child1 = Note(
            task_id=test_task.id,
            parent_id=parent_note.id,
            title="Child 1",
            body="First child"
        )
        child2 = Note(
            task_id=test_task.id,
            parent_id=parent_note.id,
            title="Child 2",
            body="Second child"
        )
        test_db_session.add_all([child1, child2])
        await test_db_session.commit()

        response = await client.get(f"/notes/{parent_note.id}/children", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert any(note["title"] == "Child 1" for note in data)
        assert any(note["title"] == "Child 2" for note in data)

    async def test_create_child_note(self, client: AsyncClient, override_get_db, test_note: Note, test_task: Task, auth_headers):
        """Test creating a child note via parent endpoint"""
        child_data = {
            "task_id": str(test_task.id),
            "title": "Child Note",
            "body": "This is a child note"
        }
        
        response = await client.post(f"/notes/{test_note.id}/children", json=child_data, headers=auth_headers)
        
        assert response.status_code == 201
        data = response.json()
        assert data["parent_id"] == str(test_note.id)
        assert data["title"] == "Child Note"

    async def test_create_child_note_wrong_task(self, client: AsyncClient, override_get_db, test_note: Note, test_db_session: AsyncSession, test_task_list: TaskList, auth_headers):
        """Test creating child note fails with different task_id"""
        # Create another task
        other_task = Task(
            list_id=test_task_list.id,
            title="Other Task",
            description="Another task",
            status=TaskStatus.todo,
            priority=TaskPriority.low
        )
        test_db_session.add(other_task)
        await test_db_session.commit()
        await test_db_session.refresh(other_task)

        child_data = {
            "task_id": str(other_task.id),  # Different task than parent
            "title": "Child Note",
            "body": "This is a child note"
        }
        
        response = await client.post(f"/notes/{test_note.id}/children", json=child_data, headers=auth_headers)
        
        assert response.status_code == 400

    async def test_get_note_tags(self, client: AsyncClient, override_get_db, test_note: Note, auth_headers):
        """Test getting note tags"""
        response = await client.get(f"/notes/{test_note.id}/tags", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    async def test_attach_tag_to_note(self, client: AsyncClient, override_get_db, test_note: Note, test_tag: Tag, auth_headers):
        """Test attaching a tag to a note"""
        response = await client.post(f"/notes/{test_note.id}/tags/{test_tag.id}", headers=auth_headers)
        
        assert response.status_code == 201
        data = response.json()
        assert data["message"] == "tag_attached"

    async def test_attach_tag_to_note_twice(self, client: AsyncClient, override_get_db, test_note: Note, test_tag: Tag, auth_headers):
        """Test attaching same tag twice doesn't cause error"""
        # First attachment
        response1 = await client.post(f"/notes/{test_note.id}/tags/{test_tag.id}", headers=auth_headers)
        assert response1.status_code == 201

        # Second attachment
        response2 = await client.post(f"/notes/{test_note.id}/tags/{test_tag.id}", headers=auth_headers)
        assert response2.status_code == 201

    async def test_detach_tag_from_note(self, client: AsyncClient, override_get_db, test_note: Note, test_tag: Tag, auth_headers):
        """Test detaching a tag from a note"""
        # First attach
        await client.post(f"/notes/{test_note.id}/tags/{test_tag.id}", headers=auth_headers)
        
        # Then detach
        response = await client.delete(f"/notes/{test_note.id}/tags/{test_tag.id}", headers=auth_headers)
        
        assert response.status_code == 204

    async def test_get_note_links(self, client: AsyncClient, override_get_db, test_note: Note, auth_headers):
        """Test getting note links"""
        response = await client.get(f"/notes/{test_note.id}/links", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "linked_to" in data
        assert "linked_from" in data
        assert isinstance(data["linked_to"], list)
        assert isinstance(data["linked_from"], list)

    async def test_link_notes(self, client: AsyncClient, override_get_db, test_db_session: AsyncSession, test_task: Task, auth_headers):
        """Test linking two notes"""
        # Create two notes
        note1 = Note(task_id=test_task.id, title="Note 1", body="First note")
        note2 = Note(task_id=test_task.id, title="Note 2", body="Second note")
        test_db_session.add_all([note1, note2])
        await test_db_session.commit()
        await test_db_session.refresh(note1)
        await test_db_session.refresh(note2)

        response = await client.post(f"/notes/{note1.id}/links/{note2.id}", headers=auth_headers)
        
        assert response.status_code == 201
        data = response.json()
        assert data["message"] == "notes_linked"

    async def test_link_notes_twice(self, client: AsyncClient, override_get_db, test_db_session: AsyncSession, test_task: Task, auth_headers):
        """Test linking same notes twice doesn't cause error"""
        # Create two notes
        note1 = Note(task_id=test_task.id, title="Note 1", body="First note")
        note2 = Note(task_id=test_task.id, title="Note 2", body="Second note")
        test_db_session.add_all([note1, note2])
        await test_db_session.commit()
        await test_db_session.refresh(note1)
        await test_db_session.refresh(note2)

        # First link
        response1 = await client.post(f"/notes/{note1.id}/links/{note2.id}", headers=auth_headers)
        assert response1.status_code == 201

        # Second link
        response2 = await client.post(f"/notes/{note1.id}/links/{note2.id}", headers=auth_headers)
        assert response2.status_code == 201

    async def test_unlink_notes(self, client: AsyncClient, override_get_db, test_db_session: AsyncSession, test_task: Task, auth_headers):
        """Test unlinking two notes"""
        # Create two notes
        note1 = Note(task_id=test_task.id, title="Note 1", body="First note")
        note2 = Note(task_id=test_task.id, title="Note 2", body="Second note")
        test_db_session.add_all([note1, note2])
        await test_db_session.commit()
        await test_db_session.refresh(note1)
        await test_db_session.refresh(note2)

        # First link
        await client.post(f"/notes/{note1.id}/links/{note2.id}", headers=auth_headers)
        
        # Then unlink
        response = await client.delete(f"/notes/{note1.id}/links/{note2.id}", headers=auth_headers)
        
        assert response.status_code == 204

    async def test_circular_reference_prevention(self, client: AsyncClient, override_get_db, test_db_session: AsyncSession, test_task: Task, auth_headers):
        """Test that circular references are prevented"""
        # Create chain of notes: A -> B -> C
        note_a = Note(task_id=test_task.id, title="Note A", body="First note")
        test_db_session.add(note_a)
        await test_db_session.commit()
        await test_db_session.refresh(note_a)

        note_b = Note(task_id=test_task.id, parent_id=note_a.id, title="Note B", body="Second note")
        test_db_session.add(note_b)
        await test_db_session.commit()
        await test_db_session.refresh(note_b)

        note_c = Note(task_id=test_task.id, parent_id=note_b.id, title="Note C", body="Third note")
        test_db_session.add(note_c)
        await test_db_session.commit()
        await test_db_session.refresh(note_c)

        # Try to create circular reference: A -> C (making C parent of A would create cycle)
        update_data = {
            "parent_id": str(note_c.id)
        }
        
        response = await client.patch(f"/notes/{note_a.id}", json=update_data, headers=auth_headers)
        
        assert response.status_code == 400
        assert "circular_reference_detected" in response.json()["detail"]