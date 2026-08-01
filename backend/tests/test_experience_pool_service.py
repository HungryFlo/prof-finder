"""Experience pool statistics."""

from __future__ import annotations

from prof_finder.api.experience_pool_service import (
    count_pool_stats,
    count_pool_stats_bulk,
    story_completion,
)
from prof_finder.models.schema import (
    ExperienceCluster,
    ExperiencePool,
    ExperienceSeed,
    ExperienceStory,
    User,
)


def make_pool(session, title: str = "pool") -> ExperiencePool:
    user = session.query(User).filter(User.username == "pool-user").first()
    if user is None:
        user = User(username="pool-user", password_hash="x")
        session.add(user)
        session.flush()
    pool = ExperiencePool(user_id=user.id, title=title)
    session.add(pool)
    session.flush()
    return pool


def add_seed(session, pool, content="seed", *, status="active", clustered=False, standalone=False):
    cluster_id = None
    if clustered:
        cluster = ExperienceCluster(pool_id=pool.id, title="theme")
        session.add(cluster)
        session.flush()
        cluster_id = cluster.id
    seed = ExperienceSeed(
        pool_id=pool.id,
        content=content,
        status=status,
        cluster_id=cluster_id,
        standalone=standalone,
    )
    session.add(seed)
    session.flush()
    return seed


def add_story(session, seed, **fields) -> ExperienceStory:
    story = ExperienceStory(seed_id=seed.id, **fields)
    session.add(story)
    session.flush()
    return story


class TestStoryCompletion:
    def test_empty(self, db_session):
        pool = make_pool(db_session)
        story = add_story(db_session, add_seed(db_session, pool))
        assert story_completion(story) == "empty"

    def test_blank_strings_count_as_empty(self, db_session):
        pool = make_pool(db_session)
        story = add_story(db_session, add_seed(db_session, pool), origin="   ")
        assert story_completion(story) == "empty"

    def test_partial(self, db_session):
        pool = make_pool(db_session)
        story = add_story(db_session, add_seed(db_session, pool), origin="a", process="b")
        assert story_completion(story) == "partial"

    def test_complete(self, db_session):
        pool = make_pool(db_session)
        story = add_story(
            db_session,
            add_seed(db_session, pool),
            origin="a",
            process="b",
            outcome="c",
            insights="d",
        )
        assert story_completion(story) == "complete"


class TestPoolStats:
    def test_empty_pool(self, db_session):
        pool = make_pool(db_session)
        assert count_pool_stats(db_session, pool) == (0, 0)

    def test_seed_count_ignores_discarded_seeds(self, db_session):
        pool = make_pool(db_session)
        add_seed(db_session, pool, "kept")
        add_seed(db_session, pool, "dropped", status="discarded")
        assert count_pool_stats(db_session, pool)[0] == 1

    def test_story_count_requires_a_clustered_or_standalone_seed(self, db_session):
        pool = make_pool(db_session)
        loose = add_seed(db_session, pool, "loose")
        add_story(db_session, loose, origin="written")
        assert count_pool_stats(db_session, pool) == (1, 0)

        standalone = add_seed(db_session, pool, "standalone", standalone=True)
        add_story(db_session, standalone, origin="written")
        assert count_pool_stats(db_session, pool) == (2, 1)

    def test_story_count_skips_empty_stories(self, db_session):
        pool = make_pool(db_session)
        add_story(db_session, add_seed(db_session, pool, "a", clustered=True))
        add_story(db_session, add_seed(db_session, pool, "b", clustered=True), outcome="done")
        assert count_pool_stats(db_session, pool) == (2, 1)

    def test_bulk_matches_per_pool_counts(self, db_session):
        first = make_pool(db_session, "first")
        second = make_pool(db_session, "second")
        add_story(db_session, add_seed(db_session, first, "a", clustered=True), origin="x")
        add_seed(db_session, first, "b")
        add_story(db_session, add_seed(db_session, second, "c", standalone=True), insights="y")

        bulk = count_pool_stats_bulk(db_session, [first.id, second.id])
        assert bulk[first.id] == count_pool_stats(db_session, first)
        assert bulk[second.id] == count_pool_stats(db_session, second)
        assert bulk == {first.id: (2, 1), second.id: (1, 1)}

    def test_bulk_reports_pools_without_rows(self, db_session):
        pool = make_pool(db_session)
        assert count_pool_stats_bulk(db_session, [pool.id]) == {pool.id: (0, 0)}

    def test_bulk_with_no_ids(self, db_session):
        assert count_pool_stats_bulk(db_session, []) == {}
