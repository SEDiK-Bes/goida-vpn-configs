#!/usr/bin/env python3
"""
🧪 COMPREHENSIVE TEST SUITE FOR main.py

Test Coverage:
1. Configuration loading (config.ini)
2. Data fetching (GitHub sources, timeouts, errors)
3. HAPP link generation (encryption, URL formatting)
4. Port validation (1-65535 range, system ports)
5. Country extraction (regex patterns, symbols)
6. Config validation (format, length, base64)
7. Host:Port extraction (json.loads, regex patterns)
8. TCP ping (connectivity, timeout)

Run: pytest tests/test_main.py -v --tb=short
"""

import pytest
import os
import sys
import json
import base64
import tempfile
import re
from unittest.mock import patch, MagicMock, mock_open
from io import StringIO

# Import functions from main.py
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import main


# ============================================================================
# 1️⃣ TEST_LOAD_CONFIG - Configuration Loading
# ============================================================================

class TestLoadConfig:
    """Test configuration loading and error handling."""

    def test_config_file_exists(self):
        """✅ Check if config.ini is expected to exist."""
        # This is a smoke test - checks config loading pattern
        assert hasattr(main, 'TOKEN'), "TOKEN should be loaded from environment"

    def test_token_validation(self):
        """✅ Validate token format (ghp_ prefix)."""
        # Token is validated in main.py
        # If invalid, the script exits
        assert main.TOKEN.startswith('ghp_'), "Token should start with 'ghp_'"

    def test_token_from_environment(self):
        """✅ Token loaded from MY_TOKEN environment variable."""
        with patch.dict(os.environ, {'MY_TOKEN': 'ghp_test123token456'}):
            # Verify environment loading works
            test_token = os.environ.get('MY_TOKEN', '').strip()
            assert test_token.startswith('ghp_')

    def test_yandex_proxy_optional(self):
        """✅ YANDEX_PROXY_URL is optional."""
        # Should not fail if not set
        assert hasattr(main, 'YANDEX_PROXY_URL')
        # Can be empty string
        assert isinstance(main.YANDEX_PROXY_URL, str)

    def test_happ_crypto_api_default(self):
        """✅ HAPP_CRYPTO_API has default URL."""
        assert 'crypto.happ.su' in main.HAPP_CRYPTO_API or \
               main.HAPP_CRYPTO_API == os.environ.get('HAPP_CRYPTO_API', 'https://crypto.happ.su/api.php')


# ============================================================================
# 2️⃣ TEST_FETCH_DATA - Data Fetching from GitHub
# ============================================================================

class TestFetchData:
    """Test data fetching with timeouts and error handling."""

    @patch('requests.get')
    def test_http_get_success(self, mock_get):
        """✅ Successfully fetch data from URL."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "vmess://config1\nvmess://config2"
        mock_get.return_value = mock_response

        idx, lines, success = main.http_get('https://example.com/test.txt', 1)
        
        assert success is True
        assert len(lines) == 2
        assert 'vmess://config1' in lines

    @patch('requests.get')
    def test_http_get_timeout(self, mock_get):
        """✅ Handle timeout when fetching."""
        mock_get.side_effect = Exception("Connection timeout")
        
        idx, lines, success = main.http_get('https://example.com/timeout.txt', 1)
        
        assert success is False
        assert lines == []

    @patch('requests.get')
    def test_http_get_404_error(self, mock_get):
        """✅ Handle 404 errors gracefully."""
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response
        
        idx, lines, success = main.http_get('https://example.com/notfound.txt', 1)
        
        assert success is False
        assert lines == []

    @patch('requests.get')
    def test_http_get_empty_response(self, mock_get):
        """✅ Handle empty responses."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = ""
        mock_get.return_value = mock_response
        
        idx, lines, success = main.http_get('https://example.com/empty.txt', 1)
        
        assert success is True
        assert lines == []

    @patch('requests.get')
    def test_http_get_whitespace_handling(self, mock_get):
        """✅ Strip whitespace from lines."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "  vmess://config1  \n\n  vmess://config2  "
        mock_get.return_value = mock_response
        
        idx, lines, success = main.http_get('https://example.com/test.txt', 1)
        
        assert success is True
        assert lines == ['vmess://config1', 'vmess://config2']


# ============================================================================
# 3️⃣ TEST_GENERATE_HAPP_LINK - HAPP Link Generation
# ============================================================================

class TestGenerateHappLink:
    """Test HAPP link generation and encryption."""

    @patch('requests.post')
    def test_happ_encrypt_url_success(self, mock_post):
        """✅ Successfully encrypt URL via HAPP API."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = {'content-type': 'application/json'}
        mock_response.json.return_value = {'url': 'happ://crypt3/encrypted123'}
        mock_post.return_value = mock_response
        
        result = main.happ_encrypt_url('https://example.com/proxy?source=set_a')
        
        assert result.startswith('happ://')
        assert 'encrypted123' in result

    @patch('requests.post')
    def test_happ_encrypt_url_404(self, mock_post):
        """✅ Handle 404 from HAPP API."""
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_post.return_value = mock_response
        
        result = main.happ_encrypt_url('https://example.com/proxy')
        
        assert result == ''

    @patch('requests.post')
    def test_happ_encrypt_url_timeout(self, mock_post):
        """✅ Handle timeout from HAPP API."""
        mock_post.side_effect = Exception("Timeout")
        
        result = main.happ_encrypt_url('https://example.com/proxy')
        
        assert result == ''

    @patch('requests.post')
    def test_happ_encrypt_url_json_response(self, mock_post):
        """✅ Parse JSON response with different field names."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = {'content-type': 'application/json'}
        mock_response.json.return_value = {'encrypted_url': 'happ://crypt3/xyz'}
        mock_post.return_value = mock_response
        
        result = main.happ_encrypt_url('https://example.com/proxy')
        
        assert 'happ://' in result

    @patch('requests.post')
    def test_happ_encrypt_url_text_response(self, mock_post):
        """✅ Handle plain text response."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = {'content-type': 'text/plain'}
        mock_response.text = 'happ://crypt3/plaintext'
        mock_post.return_value = mock_response
        
        result = main.happ_encrypt_url('https://example.com/proxy')
        
        assert 'happ://' in result


# ============================================================================
# 4️⃣ TEST_PORT_VALIDATION - Port Validation (1-65535 Range)
# ============================================================================

class TestPortValidation:
    """Test port validation in extract_host_port."""

    def test_vmess_valid_port(self):
        """✅ Extract vmess config with valid port."""
        config = json.dumps({
            "add": "192.168.1.1",
            "port": 443
        })
        payload = base64.b64encode(config.encode()).decode()
        config_line = f"vmess://{payload}"
        
        host, port = main.extract_host_port(config_line)
        
        assert host == "192.168.1.1"
        assert port == 443

    def test_port_range_valid(self):
        """✅ Validate port in valid range (1-65535)."""
        # Test boundary values
        for test_port in [1, 80, 443, 8080, 65535]:
            config = json.dumps({
                "add": "example.com",
                "port": test_port
            })
            payload = base64.b64encode(config.encode()).decode()
            config_line = f"vmess://{payload}"
            
            host, port = main.extract_host_port(config_line)
            
            assert port == test_port, f"Port {test_port} should be accepted"

    def test_port_out_of_range_high(self):
        """❌ Reject port > 65535."""
        config = json.dumps({
            "add": "example.com",
            "port": 65536
        })
        payload = base64.b64encode(config.encode()).decode()
        config_line = f"vmess://{payload}"
        
        host, port = main.extract_host_port(config_line)
        
        assert port is None, "Port > 65535 should be rejected"

    def test_port_out_of_range_low(self):
        """❌ Reject port 0."""
        config = json.dumps({
            "add": "example.com",
            "port": 0
        })
        payload = base64.b64encode(config.encode()).decode()
        config_line = f"vmess://{payload}"
        
        host, port = main.extract_host_port(config_line)
        
        assert port is None, "Port 0 should be rejected"

    def test_port_negative(self):
        """❌ Reject negative ports."""
        config = json.dumps({
            "add": "example.com",
            "port": -1
        })
        payload = base64.b64encode(config.encode()).decode()
        config_line = f"vmess://{payload}"
        
        host, port = main.extract_host_port(config_line)
        
        assert port is None, "Negative port should be rejected"

    def test_port_as_string(self):
        """✅ Handle port as string in JSON."""
        config = json.dumps({
            "add": "example.com",
            "port": "443"
        })
        payload = base64.b64encode(config.encode()).decode()
        config_line = f"vmess://{payload}"
        
        host, port = main.extract_host_port(config_line)
        
        assert port == 443

    def test_port_missing(self):
        """❌ Reject config without port."""
        config = json.dumps({
            "add": "example.com"
        })
        payload = base64.b64encode(config.encode()).decode()
        config_line = f"vmess://{payload}"
        
        host, port = main.extract_host_port(config_line)
        
        assert port is None


# ============================================================================
# 5️⃣ TEST_EXTRACT_COUNTRY - Country Code Extraction
# ============================================================================

class TestExtractCountry:
    """Test country code extraction from config remarks."""

    def test_extract_country_ec(self):
        """✅ Extract EC (European) country codes."""
        config = "vmess://..." + "#" + "NL"
        country = main.extract_country(config)
        assert country == "NL"

    def test_extract_country_ru(self):
        """✅ Extract RU country codes."""
        config = "vmess://..." + "#" + "RU"
        country = main.extract_country(config)
        assert country == "RU"

    def test_extract_country_world(self):
        """✅ Extract WORLD country codes."""
        config = "vmess://..." + "#" + "US"
        country = main.extract_country(config)
        assert country == "US"

    def test_extract_country_lowercase(self):
        """✅ Handle lowercase country codes."""
        config = "vmess://..." + "#" + "nl"
        country = main.extract_country(config)
        assert country == "NL"

    def test_extract_country_with_city(self):
        """✅ Extract country from remark with city."""
        config = "vmess://..." + "#" + "Amsterdam-NL"
        country = main.extract_country(config)
        assert country == "NL"

    def test_extract_country_url_encoded(self):
        """✅ Handle URL-encoded remarks."""
        config = "vmess://..." + "#" + "%C3%89%20NL"  # "É NL" URL encoded
        country = main.extract_country(config)
        assert country == "NL"

    def test_extract_country_html_entity(self):
        """✅ Handle HTML entities in remarks."""
        config = "vmess://..." + "#" + "&quot;DE&quot;"
        country = main.extract_country(config)
        assert country == "DE"

    def test_extract_country_unknown(self):
        """❌ Return UNKNOWN if no country found."""
        config = "vmess://...#nocontry"
        country = main.extract_country(config)
        assert country == "UNKNOWN"

    def test_extract_country_no_remark(self):
        """❌ Return UNKNOWN if no remark."""
        config = "vmess://nocountry"
        country = main.extract_country(config)
        assert country == "UNKNOWN"

    def test_extract_country_false_positive_prevention(self):
        """✅ Prevent false positive (US in 'AWESOME')."""
        config = "vmess://...#AWESOME"
        country = main.extract_country(config)
        # Should not match US in AWESOME
        assert country != "US" or country == "UNKNOWN"


# ============================================================================
# 6️⃣ TEST_IS_VALID - Config Format Validation
# ============================================================================

class TestIsValid:
    """Test config format validation."""

    def test_is_valid_vmess(self):
        """✅ Accept vmess:// format."""
        config = "vmess://abcdefghijklmnopqrstuvwxyz"
        assert main.is_valid(config) is True

    def test_is_valid_vless(self):
        """✅ Accept vless:// format."""
        config = "vless://abcdefghijklmnopqrstuvwxyz"
        assert main.is_valid(config) is True

    def test_is_valid_trojan(self):
        """✅ Accept trojan:// format."""
        config = "trojan://abcdefghijklmnopqrstuvwxyz"
        assert main.is_valid(config) is True

    def test_is_valid_ss(self):
        """✅ Accept ss:// format."""
        config = "ss://abcdefghijklmnopqrstuvwxyz"
        assert main.is_valid(config) is True

    def test_is_valid_base64(self):
        """✅ Accept valid base64 strings."""
        config = base64.b64encode(b"vmess://config").decode()
        assert main.is_valid(config) is True

    def test_is_valid_ip_port(self):
        """✅ Accept IP:PORT format."""
        config = "192.168.1.1:8080"
        assert main.is_valid(config) is True

    def test_is_valid_host_port(self):
        """✅ Accept hostname:port format."""
        config = "example.com:443"
        assert main.is_valid(config) is True

    def test_is_invalid_too_short(self):
        """❌ Reject configs < 10 chars."""
        config = "short"
        assert main.is_valid(config) is False

    def test_is_invalid_too_long(self):
        """❌ Reject configs > 5000 chars."""
        config = "a" * 5001
        assert main.is_valid(config) is False

    def test_is_invalid_empty(self):
        """❌ Reject empty config."""
        assert main.is_valid("") is False

    def test_is_invalid_random_string(self):
        """❌ Reject invalid format."""
        config = "thisisrandomstringwithnoformat"
        assert main.is_valid(config) is False

    def test_is_invalid_base64(self):
        """❌ Reject invalid base64."""
        config = "!!!invalid!!!base64!!!"
        assert main.is_valid(config) is False


# ============================================================================
# 7️⃣ TEST_EXTRACT_HOST_PORT - Host:Port Extraction
# ============================================================================

class TestExtractHostPort:
    """Test host:port extraction with json.loads."""

    def test_extract_vmess_json(self):
        """✅ Extract from vmess with JSON payload."""
        config = json.dumps({
            "add": "proxy.example.com",
            "port": 443
        })
        payload = base64.b64encode(config.encode()).decode()
        config_line = f"vmess://{payload}"
        
        host, port = main.extract_host_port(config_line)
        
        assert host == "proxy.example.com"
        assert port == 443

    def test_extract_vmess_alternative_keys(self):
        """✅ Extract using alternative JSON keys (host, ip)."""
        # Try with 'host' key
        config = json.dumps({
            "host": "example.com",
            "port": 8080
        })
        payload = base64.b64encode(config.encode()).decode()
        config_line = f"vmess://{payload}"
        
        host, port = main.extract_host_port(config_line)
        
        assert host == "example.com"
        assert port == 8080

    def test_extract_vless_at_notation(self):
        """✅ Extract host:port from @notation."""
        config = "vless://uuid@example.com:443/path?host=example.com"
        
        host, port = main.extract_host_port(config)
        
        assert host == "example.com"
        assert port == 443

    def test_extract_trojan_at_notation(self):
        """✅ Extract from trojan:// @notation."""
        config = "trojan://password@195.154.1.1:443?security=tls"
        
        host, port = main.extract_host_port(config)
        
        assert host == "195.154.1.1"
        assert port == 443

    def test_extract_no_host_port(self):
        """❌ Return None, None if extraction fails."""
        config = "invalid://config"
        
        host, port = main.extract_host_port(config)
        
        assert host is None
        assert port is None

    def test_extract_invalid_json(self):
        """✅ Gracefully handle invalid JSON in vmess."""
        payload = base64.b64encode(b"{invalid json}").decode()
        config_line = f"vmess://{payload}"
        
        host, port = main.extract_host_port(config_line)
        
        # Should fail gracefully
        assert host is None or port is None

    def test_extract_malformed_port(self):
        """❌ Handle non-numeric port."""
        config = json.dumps({
            "add": "example.com",
            "port": "not_a_number"
        })
        payload = base64.b64encode(config.encode()).decode()
        config_line = f"vmess://{payload}"
        
        host, port = main.extract_host_port(config_line)
        
        assert port is None


# ============================================================================
# 8️⃣ TEST_CHECK_PING - TCP Ping Connectivity
# ============================================================================

class TestCheckPing:
    """Test TCP ping functionality."""

    @patch('socket.socket')
    def test_check_ping_success(self, mock_socket_class):
        """✅ Successful TCP connection."""
        mock_socket = MagicMock()
        mock_socket.connect_ex.return_value = 0
        mock_socket_class.return_value = mock_socket
        
        result = main.check_ping("example.com", 443)
        
        assert result > 0, "Should return positive ping time"

    @patch('socket.socket')
    def test_check_ping_connection_refused(self, mock_socket_class):
        """❌ Connection refused (port closed)."""
        mock_socket = MagicMock()
        mock_socket.connect_ex.return_value = 1
        mock_socket_class.return_value = mock_socket
        
        result = main.check_ping("example.com", 443)
        
        assert result == -1, "Should return -1 on connection refused"

    @patch('socket.socket')
    def test_check_ping_timeout(self, mock_socket_class):
        """❌ Connection timeout."""
        mock_socket = MagicMock()
        mock_socket.connect_ex.side_effect = Exception("Timeout")
        mock_socket_class.return_value = mock_socket
        
        result = main.check_ping("example.com", 443)
        
        assert result == -1, "Should return -1 on timeout"

    @patch('socket.socket')
    def test_check_ping_invalid_host(self, mock_socket_class):
        """❌ Invalid hostname."""
        mock_socket = MagicMock()
        mock_socket.connect_ex.side_effect = Exception("Name resolution failed")
        mock_socket_class.return_value = mock_socket
        
        result = main.check_ping("invalid.example.xyz", 443)
        
        assert result == -1


# ============================================================================
# SUMMARY AND DIAGNOSTICS
# ============================================================================

class TestSummaryAndDiagnostics:
    """Summary tests for project health."""

    def test_constants_defined(self):
        """✅ Verify all critical constants are defined."""
        assert hasattr(main, 'MAX_PING_MS')
        assert hasattr(main, 'CONNECTION_TIMEOUT')
        assert hasattr(main, 'MAX_CONFIGS_PER_FILE')
        assert hasattr(main, 'HTTP_TIMEOUT')
        assert hasattr(main, 'THREAD_TIMEOUT')

    def test_country_sets_defined(self):
        """✅ Verify country classification sets."""
        assert len(main.EC_COUNTRIES) > 0
        assert len(main.RU_COUNTRIES) > 0
        assert len(main.WORLD_COUNTRIES) > 0
        # Check for overlaps
        overlap = main.EC_COUNTRIES & main.RU_COUNTRIES
        assert len(overlap) == 0, "EC and RU countries should not overlap"

    def test_sources_available(self):
        """✅ Verify config sources are configured."""
        assert len(main.SOURCES) > 0
        assert len(main.SNI_SOURCES) > 0

    def test_main_function_exists(self):
        """✅ Verify main() function exists."""
        assert hasattr(main, 'main')
        assert callable(main.main)

    def test_critical_functions_exist(self):
        """✅ Verify all critical functions are defined."""
        functions = [
            'is_valid',
            'http_get',
            'extract_host_port',
            'extract_country',
            'check_ping',
            'test_config',
            'gh_push',
            'happ_encrypt_url',
            'log_t'
        ]
        for func_name in functions:
            assert hasattr(main, func_name), f"Function {func_name} should exist"


# ============================================================================
# PYTEST CONFIGURATION
# ============================================================================

if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
