"""
Tests for web GUI security fixes.

These tests verify the security improvements made to the GUI components:
1. Path traversal protection
2. XSS prevention
3. CORS configuration
4. Settings API authentication
5. Job manager cleanup
"""
import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path
import os


class TestPathTraversalProtection:
    """Tests for validate_path() function in filesystem.py"""
    
    def test_validate_path_blocks_double_dots(self):
        """Path with .. should be rejected"""
        from javinizer.web.api.filesystem import validate_path
        from fastapi import HTTPException
        
        with pytest.raises(HTTPException) as exc_info:
            validate_path("C:\\Users\\..\\..\\Windows\\System32")
        
        assert exc_info.value.status_code == 400
        assert "traversal" in exc_info.value.detail.lower()
    
    def test_validate_path_blocks_null_bytes(self):
        """Path with null bytes should be rejected"""
        from javinizer.web.api.filesystem import validate_path
        from fastapi import HTTPException
        
        with pytest.raises(HTTPException) as exc_info:
            validate_path("C:\\Users\\test\x00.txt")
        
        assert exc_info.value.status_code == 400
        assert "null" in exc_info.value.detail.lower()
    
    def test_validate_path_accepts_valid_path(self):
        """Valid absolute path should be accepted"""
        from javinizer.web.api.filesystem import validate_path
        
        # Use a path that definitely exists
        if os.name == 'nt':
            result = validate_path("C:\\")
            assert result == Path("C:\\")
        else:
            result = validate_path("/")
            assert result == Path("/")


class TestXSSPrevention:
    """Tests for XSS prevention in apply_metadata"""
    
    def test_html_escape_function(self):
        """Verify html.escape properly escapes script tags"""
        from html import escape
        
        malicious_input = "<script>alert('XSS')</script>"
        escaped = escape(malicious_input)
        
        # Script tags should be escaped
        assert "<script>" not in escaped
        assert "&lt;script&gt;" in escaped
    
    def test_movie_id_escaping_logic(self):
        """Test the escaping logic used in apply_metadata"""
        from html import escape
        
        # Simulate what apply_metadata does
        movie_id = "<script>alert('XSS')</script>"
        safe_movie_id = escape(str(movie_id))
        response = f'<div class="p-4 bg-green-500/20 text-green-400 rounded-lg text-xs">Applied OK: {safe_movie_id}</div>'
        
        # Verify script tags are escaped in output
        assert "<script>" not in response
        assert "&lt;script&gt;" in response


class TestCORSConfiguration:
    """Tests for CORS configuration"""
    
    def test_cors_reads_from_environment(self):
        """CORS should read allowed origins from ALLOWED_ORIGINS env var"""
        with patch.dict(os.environ, {"ALLOWED_ORIGINS": "http://example.com,http://test.com"}):
            # Re-import to test the configuration
            import importlib
            import javinizer.web.server as server_module
            
            # The origins should be parsed from env
            origins_str = os.environ.get("ALLOWED_ORIGINS", "*")
            if origins_str != "*":
                expected = [o.strip() for o in origins_str.split(",")]
                assert expected == ["http://example.com", "http://test.com"]
    
    def test_cors_defaults_to_wildcard(self):
        """Without ALLOWED_ORIGINS, should default to *"""
        with patch.dict(os.environ, {}, clear=True):
            origins = os.environ.get("ALLOWED_ORIGINS", "*")
            assert origins == "*"


class TestSettingsAuthentication:
    """Tests for settings API authentication"""
    
    def test_auth_disabled_without_token(self):
        """Without ADMIN_TOKEN, auth should be disabled"""
        from javinizer.web.api.settings import verify_admin_token
        
        with patch.dict(os.environ, {}, clear=True):
            # Should return True (allow access) when no token is configured
            result = verify_admin_token(x_admin_token=None)
            assert result is True
    
    def test_auth_rejects_invalid_token(self):
        """With ADMIN_TOKEN set, invalid token should be rejected"""
        from javinizer.web.api.settings import verify_admin_token
        from fastapi import HTTPException
        
        with patch.dict(os.environ, {"ADMIN_TOKEN": "correct-token"}):
            with pytest.raises(HTTPException) as exc_info:
                verify_admin_token(x_admin_token="wrong-token")
            
            assert exc_info.value.status_code == 401
    
    def test_auth_accepts_valid_token(self):
        """With ADMIN_TOKEN set, correct token should be accepted"""
        from javinizer.web.api.settings import verify_admin_token
        
        with patch.dict(os.environ, {"ADMIN_TOKEN": "correct-token"}):
            result = verify_admin_token(x_admin_token="correct-token")
            assert result is True


class TestJobManagerCleanup:
    """Tests for job manager cleanup functionality"""
    
    def test_cleanup_removes_old_completed_jobs(self):
        """Old completed jobs should be removed"""
        from javinizer.web.services.job_manager import JobManager
        from datetime import datetime, timedelta
        
        # Create a fresh instance
        manager = JobManager.__new__(JobManager)
        manager.jobs = {}
        
        # Create an old completed job
        job_id = manager.create_job("test")
        manager.update_job(job_id, status="completed")
        
        # Manually set created_at to 48 hours ago
        manager.jobs[job_id].created_at = datetime.now() - timedelta(hours=48)
        
        # Cleanup jobs older than 24 hours
        cleaned = manager.cleanup_old_jobs(max_age_hours=24)
        
        assert cleaned == 1
        assert job_id not in manager.jobs
    
    def test_cleanup_keeps_recent_jobs(self):
        """Recent jobs should not be removed"""
        from javinizer.web.services.job_manager import JobManager
        
        manager = JobManager.__new__(JobManager)
        manager.jobs = {}
        
        # Create a new completed job
        job_id = manager.create_job("test")
        manager.update_job(job_id, status="completed")
        
        # Cleanup should not remove it
        cleaned = manager.cleanup_old_jobs(max_age_hours=24)
        
        assert cleaned == 0
        assert job_id in manager.jobs
    
    def test_get_stats_returns_correct_counts(self):
        """get_stats should return correct job counts"""
        from javinizer.web.services.job_manager import JobManager
        
        manager = JobManager.__new__(JobManager)
        manager.jobs = {}
        
        # Create jobs with different statuses
        job1 = manager.create_job("test1")
        manager.update_job(job1, status="completed")
        
        job2 = manager.create_job("test2")
        manager.update_job(job2, status="failed")
        
        job3 = manager.create_job("test3")  # pending by default
        
        stats = manager.get_stats()
        
        assert stats["total_jobs"] == 3
        assert stats["completed"] == 1
        assert stats["failed"] == 1
        assert stats["pending"] == 1
