# test_init_srv.py - Integration tests for INI loading

import os
import sys
import configparser
import pytest


class TestGetKeyAll:
    """Test INI configuration loading with real and sample files."""

    def test_load_sample_ini(self, sample_ini):
        """Load from a sample INI fixture and verify all keys."""
        # We can't easily instantiate CInitSrv without pywin32,
        # so test the configparser loading directly.
        config = configparser.ConfigParser()
        config.read(str(sample_ini), encoding='latin-1')

        assert config.get('Servico', 'ServiceName') == 'TestService'
        assert config.getint('Servico', 'MonitorPort') == 15000
        assert config.getint('Servico', 'SrvTimeout') == 60
        assert config.get('Servico', 'Trace') == 'D'

        assert config.get('DataBase', 'DBServer') == 'localhost'
        assert config.getint('DataBase', 'DBPort') == 5432
        assert config.get('DataBase', 'DBUserName') == 'testuser'

        assert config.get('MQSeries', 'QueueManager') == 'QM.TEST.01'
        assert config.getint('MQSeries', 'QueueTimeout') == 10

        assert config.get('Security', 'UnicodeEnable') == 'S'
        assert config.get('Security', 'SecurityEnable') == 'N'

    def test_load_real_ini(self):
        """Load the actual BCSrvSqlMq.ini if available."""
        ini_path = os.path.join('C:\\BCSrvSqlMq', 'BCSrvSqlMq.ini')
        if not os.path.exists(ini_path):
            pytest.skip('Real INI file not found')

        config = configparser.ConfigParser()
        config.read(ini_path, encoding='latin-1')

        # Verify critical sections exist
        assert config.has_section('Servico')
        assert config.has_section('DataBase')
        assert config.has_section('MQSeries')
        assert config.has_section('Security')

        # Verify critical keys
        assert config.has_option('Servico', 'ServiceName')
        assert config.has_option('Servico', 'MonitorPort')
        assert config.has_option('DataBase', 'DBServer')
        assert config.has_option('MQSeries', 'QueueManager')

    def test_missing_ini_uses_defaults(self, tmp_path):
        """When INI doesn't exist, configparser returns empty config."""
        config = configparser.ConfigParser()
        config.read(str(tmp_path / 'nonexistent.ini'), encoding='latin-1')
        assert len(config.sections()) == 0

    def test_all_16_queue_names_present(self, sample_ini):
        """Verify all 16 MQ queue names are loadable."""
        config = configparser.ConfigParser()
        config.read(str(sample_ini), encoding='latin-1')

        queue_keys = [
            'QLBacenCidadeReq', 'QLBacenCidadeRsp', 'QLBacenCidadeRep', 'QLBacenCidadeSup',
            'QRCidadeBacenReq', 'QRCidadeBacenRsp', 'QRCidadeBacenRep', 'QRCidadeBacenSup',
            'QLIFCidadeReq', 'QLIFCidadeRsp', 'QLIFCidadeRep', 'QLIFCidadeSup',
            'QRCidadeIFReq', 'QRCidadeIFRsp', 'QRCidadeIFRep', 'QRCidadeIFSup',
        ]
        for key in queue_keys:
            assert config.has_option('MQSeries', key), f'Missing queue key: {key}'
            val = config.get('MQSeries', key)
            assert len(val) > 0, f'Empty queue name for: {key}'

    def test_set_key_all_writes_ini(self, tmp_path):
        """Verify that writing config back to INI preserves values."""
        ini_path = tmp_path / 'output.ini'
        config = configparser.ConfigParser()
        config['Servico'] = {'ServiceName': 'WrittenService', 'MonitorPort': '9999'}
        config['DataBase'] = {'DBServer': 'dbhost', 'DBPort': '5433'}

        with open(ini_path, 'w', encoding='latin-1') as f:
            config.write(f)

        # Read back
        config2 = configparser.ConfigParser()
        config2.read(str(ini_path), encoding='latin-1')
        assert config2.get('Servico', 'ServiceName') == 'WrittenService'
        assert config2.getint('Servico', 'MonitorPort') == 9999
        assert config2.get('DataBase', 'DBServer') == 'dbhost'


class TestCInitSrvImport:
    """Test that CInitSrv can be imported."""

    def test_import(self):
        try:
            from bcsrvsqlmq.init_srv import CInitSrv
        except ImportError as e:
            if 'win32' in str(e).lower() or 'pywin32' in str(e).lower():
                pytest.skip('pywin32 not installed')
            raise
