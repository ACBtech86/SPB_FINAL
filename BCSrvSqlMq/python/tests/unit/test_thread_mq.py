# test_thread_mq.py - Unit tests for CThreadMQ static/utility methods

import pytest
from lxml import etree

from bcsrvsqlmq.thread_mq import CThreadMQ


class TestCharacterEncoding:
    """Tests for ANSI/Unicode conversion methods."""

    def test_ansi_to_unicode(self):
        ansi = b'Hello'
        unicode_data = CThreadMQ.ansi_to_unicode(ansi)
        assert unicode_data == 'Hello'.encode('utf-16-le')

    def test_unicode_to_ansi(self):
        unicode_data = 'Hello'.encode('utf-16-le')
        ansi = CThreadMQ.unicode_to_ansi(unicode_data)
        assert ansi == b'Hello'

    def test_roundtrip_ansi_unicode(self):
        original = b'Teste \xe7\xe3o'  # Latin-1 chars (ção)
        unicode_data = CThreadMQ.ansi_to_unicode(original)
        back = CThreadMQ.unicode_to_ansi(unicode_data)
        assert back == original

    def test_empty_data(self):
        assert CThreadMQ.ansi_to_unicode(b'') == b''
        assert CThreadMQ.unicode_to_ansi(b'') == b''


class TestXMLProcessing:
    """Tests for XML document operations using lxml."""

    def test_load_document_sync(self):
        xml = b'<root><item>value</item></root>'
        doc = CThreadMQ.load_document_sync(xml)
        assert doc is not None
        assert doc.tag == 'root'

    def test_load_document_sync_string(self):
        xml = '<root><item>value</item></root>'
        doc = CThreadMQ.load_document_sync(xml)
        assert doc is not None

    def test_load_document_sync_invalid(self):
        doc = CThreadMQ.load_document_sync(b'not xml')
        assert doc is None

    def test_check_load(self):
        doc = CThreadMQ.load_document_sync(b'<root/>')
        assert CThreadMQ.check_load(doc) is True
        assert CThreadMQ.check_load(None) is False

    def test_find_tag_with_parent(self):
        xml = b'<root><parent><child>found</child></parent></root>'
        doc = CThreadMQ.load_document_sync(xml)
        result = CThreadMQ.find_tag(doc, 'parent', 'child')
        assert result == 'found'

    def test_find_tag_without_parent(self):
        xml = b'<root><child>direct</child></root>'
        doc = CThreadMQ.load_document_sync(xml)
        result = CThreadMQ.find_tag(doc, '', 'child')
        assert result == 'direct'

    def test_find_tag_missing(self):
        xml = b'<root><other>val</other></root>'
        doc = CThreadMQ.load_document_sync(xml)
        result = CThreadMQ.find_tag(doc, '', 'nothere')
        assert result is None

    def test_find_tag_none_doc(self):
        result = CThreadMQ.find_tag(None, '', 'tag')
        assert result is None

    def test_set_tag(self):
        xml = b'<root><field>old</field></root>'
        doc = CThreadMQ.load_document_sync(xml)
        assert CThreadMQ.set_tag(doc, 'field', 'new') is True
        assert CThreadMQ.find_tag(doc, '', 'field') == 'new'

    def test_set_tag_none_doc(self):
        assert CThreadMQ.set_tag(None, 'field', 'value') is False

    def test_save_document(self, tmp_path):
        xml = b'<root><item>value</item></root>'
        doc = CThreadMQ.load_document_sync(xml)
        filepath = str(tmp_path / 'test.xml')
        assert CThreadMQ.save_document(doc, filepath) is True
        assert (tmp_path / 'test.xml').exists()

        # Read back
        with open(filepath, 'rb') as f:
            content = f.read()
        assert b'<item>value</item>' in content

    def test_walk_tree(self, capsys):
        xml = b'<root><child>text</child></root>'
        doc = CThreadMQ.load_document_sync(xml)
        result = CThreadMQ.walk_tree(doc)
        assert result is True

    def test_walk_tree_none(self):
        assert CThreadMQ.walk_tree(None) is False

    def test_report_error(self):
        assert CThreadMQ.report_error(None) is False


class TestThreadMQInit:
    """Tests for CThreadMQ initialization."""

    def test_default_values(self):
        t = CThreadMQ()
        assert t.m_ServiceName == ''
        assert t.m_AutomaticThread is True
        assert t.m_ThreadIsRunning is False
        assert t.m_ServicoIsRunning is False

    def test_custom_init(self):
        t = CThreadMQ(name='TestTask', automatic_thread=False, handle_mq=3)
        assert t.m_szTaskName == 'TestTask'
        assert t.m_AutomaticThread is False
        assert t.m_HandleMQ == 3

    def test_name_truncation(self):
        long_name = 'A' * 100
        t = CThreadMQ(name=long_name)
        assert len(t.m_szTaskName) == 40

    def test_lock_unlock(self):
        t = CThreadMQ()
        assert t.lock() is True
        assert t.unlock() is True

    def test_events_exist(self):
        t = CThreadMQ()
        assert t.m_event_stop is not None
        assert t.m_event_post is not None
        assert t.m_event_timer is not None
        assert not t.m_event_stop.is_set()
