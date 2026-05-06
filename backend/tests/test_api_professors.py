"""Tests for professor management API endpoints."""

import pytest
from fastapi.testclient import TestClient

from prof_finder.models.schema import Professor, SourceInput


class TestProfessorList:
    """Tests for listing professors."""

    def test_list_professors_success(self, test_client: TestClient, auth_headers: dict, test_db):
        """Test listing professors with pagination."""
        # Create professors
        with test_db.session() as session:
            from prof_finder.models.schema import User
            user = session.query(User).filter(User.username == "testuser").first()
            professors = [
                Professor(
                    user_id=user.id,
                    name=f"Prof {i}",
                    affiliation=f"University {i}",
                    research_interests=["NLP", "ML"],
                )
                for i in range(5)
            ]
            session.add_all(professors)
            session.commit()
        
        response = test_client.get("/api/professors?page=1&page_size=10", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert "page" in data
        assert data["total"] == 5
        assert len(data["items"]) == 5

    def test_list_professors_pagination(self, test_client: TestClient, auth_headers: dict, test_db):
        """Test pagination."""
        # Create 10 professors
        with test_db.session() as session:
            from prof_finder.models.schema import User
            user = session.query(User).filter(User.username == "testuser").first()
            professors = [
                Professor(
                    user_id=user.id,
                    name=f"Prof {i}",
                    affiliation=f"University {i}",
                )
                for i in range(10)
            ]
            session.add_all(professors)
            session.commit()
        
        # First page
        response = test_client.get("/api/professors?page=1&page_size=3", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 3
        assert data["page"] == 1
        assert data["pages"] == 4  # 10 / 3 = 4 pages
        
        # Second page
        response = test_client.get("/api/professors?page=2&page_size=3", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 3
        assert data["page"] == 2

    def test_list_professors_filter_affiliation(
        self, test_client: TestClient, auth_headers: dict, test_db
    ):
        """Test filtering by affiliation."""
        with test_db.session() as session:
            from prof_finder.models.schema import User
            user = session.query(User).filter(User.username == "testuser").first()
            professors = [
                Professor(user_id=user.id, name="Prof A", affiliation="MIT"),
                Professor(user_id=user.id, name="Prof B", affiliation="Stanford"),
            ]
            session.add_all(professors)
            session.commit()
        
        response = test_client.get(
            "/api/professors?affiliation=MIT", headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 1
        assert data["items"][0]["affiliation"] == "MIT"


class TestProfessorCreate:
    """Tests for creating professors."""

    def test_create_professor_success(self, test_client: TestClient, auth_headers: dict):
        """Test successful professor creation."""
        response = test_client.post(
            "/api/professors",
            headers=auth_headers,
            json={
                "name": "Dr. Smith",
                "affiliation": "Stanford CS",
                "email": "smith@stanford.edu",
                "research_interests": ["NLP", "ML"],
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Dr. Smith"
        assert data["affiliation"] == "Stanford CS"
        assert "NLP" in data["research_interests"]
        assert data.get("enrichment_task_id")
        assert data.get("enrichment_task_total") == 2

    def test_create_professor_skips_enrichment_when_all_auto_steps_off(
        self, test_client: TestClient, auth_headers: dict
    ):
        """No background task when all auto-enrichment toggles are disabled."""
        r0 = test_client.put(
            "/api/settings",
            headers=auth_headers,
            json={
                "auto_enrich_on_save_fetch_publication_details": False,
                "auto_enrich_on_save_paper_summaries": False,
                "auto_enrich_on_save_research_profile": False,
            },
        )
        assert r0.status_code == 200

        response = test_client.post(
            "/api/professors",
            headers=auth_headers,
            json={
                "name": "Dr. No Enrich",
                "affiliation": "Test Univ",
                "research_interests": ["AI"],
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data.get("enrichment_task_id") in (None, "")
        assert data.get("enrichment_task_total") in (None, 0)


class TestProfessorGet:
    """Tests for getting a specific professor."""

    def test_get_professor_success(self, test_client: TestClient, auth_headers: dict, test_db):
        """Test getting a professor."""
        with test_db.session() as session:
            from prof_finder.models.schema import User
            user = session.query(User).filter(User.username == "testuser").first()
            professor = Professor(
                user_id=user.id,
                name="Dr. Test",
                affiliation="Test University",
            )
            session.add(professor)
            session.commit()
            professor_id = professor.id
        
        response = test_client.get(f"/api/professors/{professor_id}", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == professor_id
        assert data["name"] == "Dr. Test"

    def test_get_professor_not_found(self, test_client: TestClient, auth_headers: dict):
        """Test getting non-existent professor."""
        response = test_client.get("/api/professors/99999", headers=auth_headers)
        assert response.status_code == 404


class TestProfessorUpdate:
    """Tests for updating professors."""

    def test_update_professor_success(self, test_client: TestClient, auth_headers: dict, test_db):
        """Test successful professor update."""
        with test_db.session() as session:
            from prof_finder.models.schema import User
            user = session.query(User).filter(User.username == "testuser").first()
            professor = Professor(
                user_id=user.id,
                name="Old Name",
                affiliation="Old University",
            )
            session.add(professor)
            session.commit()
            professor_id = professor.id
        
        response = test_client.put(
            f"/api/professors/{professor_id}",
            headers=auth_headers,
            json={"name": "New Name", "affiliation": "New University"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "New Name"
        assert data["affiliation"] == "New University"


class TestProfessorEditFlow:
    """Tests for professor preview/apply edit endpoints."""

    def test_edit_preview_with_manual_and_sources(
        self, test_client: TestClient, auth_headers: dict, test_db
    ):
        """Preview should return manual patch result and source suggestions."""
        with test_db.session() as session:
            from prof_finder.models.schema import User

            user = session.query(User).filter(User.username == "testuser").first()
            professor = Professor(user_id=user.id, name="Old Name", affiliation="Old Aff")
            session.add(professor)
            session.flush()

            source = SourceInput(
                user_id=user.id,
                source_type="arxiv",
                title="Paper A",
                abstract="Interesting abstract",
                status="succeeded",
            )
            session.add(source)
            session.flush()
            professor_id = professor.id
            source_id = source.id

        response = test_client.post(
            f"/api/professors/{professor_id}/edit-preview",
            headers=auth_headers,
            json={
                "manual_patch": {"name": "New Name", "manual_notes": "manual"},
                "source_input_ids": [source_id],
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["manual_patch_applied"]["name"] == "New Name"
        assert data["source_suggestions"]["publications"][0]["title"] == "Paper A"
        assert data["source_suggestions"]["manual_notes_append"] is None
        assert len(data["source_suggestions"]["paper_summaries"]) == 1
        assert "Interesting abstract" in (data["source_suggestions"]["paper_summaries"][0]["summary"] or "")

    def test_apply_edits_updates_professor_and_links_source(
        self, test_client: TestClient, auth_headers: dict, test_db
    ):
        """Apply endpoint should update professor and attach source inputs."""
        with test_db.session() as session:
            from prof_finder.models.schema import User

            user = session.query(User).filter(User.username == "testuser").first()
            professor = Professor(
                user_id=user.id,
                name="Old Name",
                affiliation="Old Aff",
                publications=[],
                manual_notes="base notes",
            )
            session.add(professor)
            session.flush()

            source = SourceInput(
                user_id=user.id,
                source_type="arxiv",
                title="Paper B",
                abstract="Abstract B",
                status="succeeded",
            )
            session.add(source)
            session.flush()
            professor_id = professor.id
            source_id = source.id

        response = test_client.post(
            f"/api/professors/{professor_id}/apply-edits",
            headers=auth_headers,
            json={
                "manual_patch": {"affiliation": "New Aff"},
                "source_input_ids": [source_id],
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["affiliation"] == "New Aff"
        assert any(item["title"] == "Paper B" for item in data["publications"])
        assert data.get("manual_notes") == "base notes"
        assert len(data.get("paper_summaries") or []) == 1
        assert (data["paper_summaries"][0]["title"]) == "Paper B"
        assert "Abstract B" in (data["paper_summaries"][0]["summary"] or "")

        with test_db.session() as session:
            linked = session.query(SourceInput).filter(SourceInput.id == source_id).first()
            assert linked is not None
            assert linked.professor_id == professor_id

    def test_apply_edits_ignores_manual_patch_for_paper_summaries(
        self, test_client: TestClient, auth_headers: dict, test_db
    ):
        """Apply edits should not mutate paper summaries via manual patch."""
        with test_db.session() as session:
            from prof_finder.models.schema import User

            user = session.query(User).filter(User.username == "testuser").first()
            professor = Professor(
                user_id=user.id,
                name="Prof Summary",
                affiliation="Aff",
                paper_summaries=[
                    {
                        "source_input_id": 1,
                        "source_type": "pdf",
                        "title": "Keep Me",
                        "summary": "old keep summary",
                        "keywords": ["old"],
                    },
                    {
                        "source_input_id": 2,
                        "source_type": "pdf",
                        "title": "Delete Me",
                        "summary": "old delete summary",
                        "keywords": ["drop"],
                    },
                ],
            )
            session.add(professor)
            session.flush()
            professor_id = professor.id

        response = test_client.post(
            f"/api/professors/{professor_id}/apply-edits",
            headers=auth_headers,
            json={
                "manual_patch": {
                    "paper_summaries": [
                        {
                            "source_input_id": 1,
                            "source_type": "pdf",
                            "title": "Keep Me Edited",
                            "summary": "new keep summary",
                            "keywords": ["new", "keep"],
                        }
                    ]
                },
                "source_input_ids": [],
            },
        )
        assert response.status_code == 200
        data = response.json()
        summaries = data.get("paper_summaries") or []
        assert len(summaries) == 2
        assert summaries[0]["title"] == "Keep Me"
        assert summaries[1]["title"] == "Delete Me"

    def test_start_background_paper_summary_task(
        self, test_client: TestClient, auth_headers: dict, test_db
    ):
        """Should start async paper summary task for selected sources."""
        with test_db.session() as session:
            from prof_finder.models.schema import User

            user = session.query(User).filter(User.username == "testuser").first()
            professor = Professor(user_id=user.id, name="Prof Async", affiliation="Aff")
            session.add(professor)
            session.flush()

            source = SourceInput(
                user_id=user.id,
                source_type="arxiv",
                title="Async Paper",
                abstract="async abstract",
                status="succeeded",
            )
            session.add(source)
            session.flush()
            professor_id = professor.id
            source_id = source.id

        response = test_client.post(
            f"/api/professors/{professor_id}/summarize-sources",
            headers=auth_headers,
            json={"source_input_ids": [source_id]},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["task_id"]
        assert "已启动" in data["message"]

    def test_start_background_paper_summary_skips_already_summarized(
        self, test_client: TestClient, auth_headers: dict, test_db
    ):
        """Should reject task start when all selected sources are already summarized."""
        with test_db.session() as session:
            from prof_finder.models.schema import User

            user = session.query(User).filter(User.username == "testuser").first()
            source = SourceInput(
                user_id=user.id,
                source_type="arxiv",
                title="Done Paper",
                abstract="done abstract",
                status="succeeded",
            )
            session.add(source)
            session.flush()
            professor = Professor(
                user_id=user.id,
                name="Prof Done",
                affiliation="Aff",
                paper_summaries=[
                    {
                        "source_input_id": source.id,
                        "source_type": "arxiv",
                        "title": "Done Paper",
                        "summary": "already done",
                        "keywords": ["done"],
                    }
                ],
            )
            session.add(professor)
            session.flush()
            professor_id = professor.id
            source_id = source.id

        response = test_client.post(
            f"/api/professors/{professor_id}/summarize-sources",
            headers=auth_headers,
            json={"source_input_ids": [source_id]},
        )
        assert response.status_code == 400
        assert "均已总结" in response.json()["detail"]


class TestProfessorDelete:
    """Tests for deleting professors."""

    def test_delete_professor_success(self, test_client: TestClient, auth_headers: dict, test_db):
        """Test successful professor deletion."""
        with test_db.session() as session:
            from prof_finder.models.schema import User
            user = session.query(User).filter(User.username == "testuser").first()
            professor = Professor(
                user_id=user.id,
                name="To Delete",
            )
            session.add(professor)
            session.commit()
            professor_id = professor.id
        
        response = test_client.delete(f"/api/professors/{professor_id}", headers=auth_headers)
        assert response.status_code == 200
        assert "已删除" in response.json()["message"]
        
        # Verify deleted
        response = test_client.get(f"/api/professors/{professor_id}", headers=auth_headers)
        assert response.status_code == 404


class TestProfessorBatchDelete:
    """Tests for batch deleting professors."""

    def test_batch_delete_success(self, test_client: TestClient, auth_headers: dict, test_db):
        """Test successful batch deletion."""
        with test_db.session() as session:
            from prof_finder.models.schema import User
            user = session.query(User).filter(User.username == "testuser").first()
            professors = [
                Professor(user_id=user.id, name=f"Prof {i}")
                for i in range(3)
            ]
            session.add_all(professors)
            session.commit()
            professor_ids = [p.id for p in professors]
        
        response = test_client.post(
            "/api/professors/batch-delete",
            headers=auth_headers,
            json={"ids": professor_ids[:2]},
        )
        assert response.status_code == 200
        assert "已删除 2 位教授" in response.json()["message"]
