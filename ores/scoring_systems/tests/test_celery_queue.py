import celery
import celerytest
import mock

from ..celery_queue import CeleryQueue
from .util import fakewiki, wait_time, test_scoring_system


def test_score():
    application = celery.Celery(__name__)
    scoring_system = CeleryQueue(
        {'fakewiki': fakewiki}, application=application, timeout=15)
    celerytest.start_celery_worker(application, concurrency=1)

    test_scoring_system(scoring_system)


def test_timeout():
    application = celery.Celery(__name__)
    scoring_system = CeleryQueue(
        {'fakewiki': fakewiki}, application=application, timeout=0.10)
    celerytest.start_celery_worker(application, concurrency=1)

    score_doc = scoring_system.score(
        "fakewiki", ["fake"], [1], injection_caches={1: {wait_time: 0.10}})
    assert 'error' in score_doc['scores'][1], str(score_doc['scores'])
    assert 'Timed out after' in score_doc['scores'][1]['error']['message'], \
           score_doc['scores'][1]['error']['message']


def test_lookup_cached():
    application = celery.Celery(__name__)

    # Set cached task result.
    stored_result = 123
    cache = mock.MagicMock()
    cache.lookup.return_value = stored_result

    scoring_system = CeleryQueue(
        {'fakewiki': fakewiki}, application=application, timeout=0.10, score_cache=cache)
    celerytest.start_celery_worker(application, concurrency=1)

    score_doc = scoring_system.score(
        "fakewiki", ["fake"], [1], injection_caches={1: {wait_time: 0.10}})
    expected_result = {
        'scores': {1: {'fake': {'score': stored_result}}},
        'models': {'fake': {'version': 'fake version'}},
    }
    assert expected_result == score_doc
