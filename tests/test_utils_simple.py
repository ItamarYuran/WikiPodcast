#!/usr/bin/env python3
"""
Simple Test Utilities
"""

import unittest
import tempfile
import shutil
import os
from pathlib import Path
from unittest.mock import patch

class SimpleBaseTestCase(unittest.TestCase):
    """Simplified base test case"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = Path(tempfile.mkdtemp())
        
        self.env_patcher = patch.dict(os.environ, {
            'OPENAI_API_KEY': 'sk-test-key-12345'
        })
        self.env_patcher.start()
    
    def tearDown(self):
        """Clean up test fixtures"""
        self.env_patcher.stop()
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir, ignore_errors=True)

if __name__ == '__main__':
    unittest.main()
