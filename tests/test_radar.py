import json
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import Mock, patch

from agent.radar import (Budget, Extractor, Fetcher, atomic_json, canonical_url,
                         jsonld_events, merge_events, normalize_event, public_url,
                         read_json, retain_prior, run, verify)

NOW = datetime(2026,10,3,10,tzinfo=timezone.utc)
URL = 'https://example.org/ai-workshop'


def raw(**overrides):
    value = dict(title='AI workshop',start='2026-10-10T10:00:00+05:00',end=None,venue='Innovation Hub, Karachi',format='in-person',organizer='Builders Karachi',description='A machine learning workshop',is_free=True,cost='Free',student_only=False,source_url=URL,extraction='jsonld')
    value.update(overrides)
    return value


def event_html(**overrides):
    obj = {'@context':'https://schema.org','@type':'Event','name':'AI workshop','startDate':'2026-10-10T10:00:00+05:00','url':URL,'location':{'@type':'Place','name':'Innovation Hub','address':{'addressLocality':'Karachi'}},'organizer':{'name':'Builders Karachi'},'offers':{'price':'0','priceCurrency':'PKR'},'description':'A machine learning workshop'}
    obj.update(overrides)
    return '<html><script type="application/ld+json">'+json.dumps({'@graph':[obj]})+'</script></html>'


def config():
    return dict(horizon_days=120,monthly_search_credits=10,max_searches_per_run=1,max_pages_per_run=10,max_llm_calls_per_run=3,request_timeout_seconds=2,event_urls=[URL],listing_urls=[],queries=[])


class NormalizationTests(unittest.TestCase):
    def test_timezone_conversion(self):
        event = normalize_event(raw(start='2026-10-10T10:00:00Z'),NOW)
        self.assertEqual(event['start'],'2026-10-10T15:00:00+05:00')

    def test_drop_past_cancelled_unrelated_and_wrong_city(self):
        for changes in [dict(start='2026-01-01'),dict(event_status='https://schema.org/EventCancelled'),dict(venue='Lahore'),dict(title='Lunch',description='Lunch',organizer='Restaurant')]:
            with self.subTest(changes=changes):
                self.assertIsNone(normalize_event(raw(**changes),NOW))

    def test_online_ambiguous_time_rejected(self):
        self.assertIsNone(normalize_event(raw(format='online',start='2026-10-10T10:00:00'),NOW))

    def test_restricted_online_rejected(self):
        self.assertIsNone(normalize_event(raw(format='online',online_access='restricted'),NOW))

    def test_date_only_visible_all_day(self):
        event = normalize_event(raw(start='2026-10-03'),NOW)
        self.assertFalse(event['time_known'])
        self.assertTrue(event['end'].endswith('23:59:59+05:00'))

    def test_invalid_dates_and_urls(self):
        self.assertIsNone(normalize_event(raw(start='2026-02-30'),NOW))
        self.assertIsNone(normalize_event(raw(source_url='javascript:alert(1)'),NOW))

    def test_free_not_inferred_from_missing_price(self):
        result = jsonld_events(event_html(offers={}),URL)[0]
        self.assertIsNone(result['is_free'])
        self.assertEqual(result['cost'],'Cost not listed')

    def test_nested_jsonld_and_karachi_location(self):
        values = jsonld_events(event_html(),URL)
        self.assertEqual(len(values),1)
        self.assertIn('Karachi',values[0]['venue'])
        self.assertTrue(values[0]['is_free'])

    def test_canonical_url_removes_tracking_not_event_ids(self):
        self.assertEqual(canonical_url('https://EXAMPLE.org/e/?id=2&utm_source=test#top'),'https://example.org/e?id=2')

    def test_private_address_blocked(self):
        with patch('agent.radar.socket.getaddrinfo',return_value=[(2,1,6,'',('127.0.0.1',80))]):
            with self.assertRaises(ValueError):
                public_url('https://example.org')


class MergeTests(unittest.TestCase):
    def test_cross_platform_duplicates_keep_sources_and_oldest_seen(self):
        a = normalize_event(raw(),NOW)
        b = normalize_event(raw(source_url='https://another.org/workshop'),NOW-timedelta(days=2))
        b['confidence'] = 90
        result = merge_events([a,b])
        self.assertEqual(len(result),1)
        self.assertEqual(len(result[0]['sources']),2)
        self.assertEqual(result[0]['first_seen'],b['first_seen'])
        self.assertEqual(result[0]['confidence'],90)

    def test_same_title_different_day_not_merged(self):
        a = normalize_event(raw(),NOW)
        b = normalize_event(raw(start='2026-10-11T10:00:00+05:00'),NOW)
        self.assertEqual(len(merge_events([a,b])),2)

    def test_different_organizers_not_merged(self):
        a = normalize_event(raw(),NOW)
        b = normalize_event(raw(organizer='Other Society',source_url='https://another.org/workshop'),NOW)
        self.assertEqual(len(merge_events([a,b])),2)

    def test_unseen_previous_events_lose_verified_badge(self):
        a = normalize_event(raw(),NOW)
        a['verification'],a['confidence'] = 'verified',90
        self.assertEqual(retain_prior([a],NOW)[0]['verification'],'unverified')


class VerificationTests(unittest.TestCase):
    def test_matching_own_page_is_verified(self):
        fetcher = Mock()
        fetcher.get.return_value = (URL,event_html())
        result = verify(normalize_event(raw(),NOW),raw(),fetcher,NOW)
        self.assertEqual(result['verification'],'verified')
        fetcher.get.assert_called_once_with(URL,fresh=True)

    def test_reachable_page_alone_not_verified(self):
        fetcher = Mock()
        fetcher.get.return_value = (URL,'<html>Welcome</html>')
        result = verify(normalize_event(raw(),NOW),raw(),fetcher,NOW)
        self.assertEqual(result['verification'],'unverified')

    def test_changed_date_not_verified(self):
        fetcher = Mock()
        fetcher.get.return_value = (URL,event_html(startDate='2026-10-12T10:00:00+05:00'))
        self.assertEqual(verify(normalize_event(raw(),NOW),raw(),fetcher,NOW)['verification'],'unverified')

    def test_blocked_page_keeps_unverified_result(self):
        fetcher = Mock()
        fetcher.get.side_effect = ValueError('blocked')
        result = verify(normalize_event(raw(),NOW),raw(),fetcher,NOW)
        self.assertEqual(result['confidence'],25)
        self.assertEqual(result['registration_url'],'')

    def test_cancellation_on_fresh_check_removes_event(self):
        fetcher = Mock()
        fetcher.get.return_value = (URL,event_html(eventStatus='https://schema.org/EventCancelled'))
        self.assertIsNone(verify(normalize_event(raw(),NOW),raw(),fetcher,NOW))


class BudgetAndPipelineTests(unittest.TestCase):
    @patch.dict('os.environ',{},clear=True)
    @patch('agent.radar.utcnow',return_value=NOW)
    @patch.object(Fetcher,'get',return_value=(URL,event_html(eventStatus='https://schema.org/EventCancelled')))
    def test_cancelled_last_event_can_clear_live_dataset(self,*_):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            atomic_json(root/'docs/events.json',dict(mode='live',generated_at=NOW.isoformat(),events=[normalize_event(raw(),NOW)]))
            self.assertEqual(run(config(),root/'docs',root/'state',root/'cache'),0)
            self.assertEqual(read_json(root/'docs/events.json')['events'],[])

    def test_credit_budget_persists_and_resets_monthly(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/'usage.json'
            budget = Budget(path,1,NOW)
            self.assertTrue(budget.reserve())
            self.assertFalse(Budget(path,1,NOW).reserve())
            self.assertTrue(Budget(path,1,NOW+timedelta(days=31)).reserve())

    @patch.dict('os.environ',{},clear=True)
    @patch('agent.radar.utcnow',return_value=NOW)
    @patch.object(Fetcher,'get',return_value=(URL,event_html()))
    def test_pipeline_publishes_live_data_and_keeps_first_seen(self,*_):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            first = normalize_event(raw(),NOW-timedelta(days=2))
            atomic_json(root/'docs/events.json',dict(mode='live',generated_at=NOW.isoformat(),events=[first]))
            self.assertEqual(run(config(),root/'docs',root/'state',root/'cache'),0)
            output = read_json(root/'docs/events.json')
            self.assertEqual(output['mode'],'live')
            self.assertEqual(output['events'][0]['verification'],'verified')
            self.assertEqual(output['events'][0]['first_seen'],first['first_seen'])

    @patch.dict('os.environ',{},clear=True)
    @patch('agent.radar.utcnow',return_value=NOW)
    @patch.object(Fetcher,'get',side_effect=ValueError('blocked'))
    def test_failed_run_preserves_last_good_file_byte_for_byte(self,*_):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            atomic_json(root/'docs/events.json',dict(mode='live',generated_at=NOW.isoformat(),events=[normalize_event(raw(),NOW)]))
            original = (root/'docs/events.json').read_bytes()
            self.assertEqual(run(config(),root/'docs',root/'state',root/'cache'),1)
            self.assertEqual((root/'docs/events.json').read_bytes(),original)
            self.assertEqual(read_json(root/'docs/status.json')['state'],'failed')

    @patch.dict('os.environ',{'GEMINI_API_KEY':'test-key','GROQ_API_KEY':'test-backup'},clear=True)
    @patch('agent.radar.time.sleep')
    @patch('agent.radar.requests.post')
    def test_groq_fallback_and_extraction_cache(self,post,_sleep):
        import requests
        response = Mock()
        response.json.return_value = {'choices':[{'message':{'content':json.dumps({'events':[raw(date_evidence='10 October 2026')]})}}]}
        post.side_effect = [requests.RequestException('quota'),response]
        with tempfile.TemporaryDirectory() as directory:
            extractor = Extractor(config(),Path(directory))
            results = extractor.extract('AI workshop on 10 October 2026',URL,NOW)
            self.assertEqual(len(results),1)
            self.assertEqual(results[0]['extraction'],'llm')
            extractor.extract('AI workshop on 10 October 2026',URL,NOW)
            self.assertEqual(post.call_count,2)

    @patch.dict('os.environ',{'GEMINI_API_KEY':'test-key'},clear=True)
    @patch('agent.radar.requests.post')
    def test_fabricated_date_evidence_rejected(self,post):
        post.return_value.json.return_value = {'candidates':[{'content':{'parts':[{'text':json.dumps({'events':[raw(date_evidence='10 October 2026')]})}]}}]}
        with tempfile.TemporaryDirectory() as directory:
            self.assertEqual(Extractor(config(),Path(directory)).extract('No date here',URL,NOW),[])


if __name__ == '__main__':
    unittest.main()
