"""
Temporary FiberWise instance manager for isolated testing.
Handles creation, configuration, and cleanup of temp instances.
"""
import os
import shutil
import json
import uuid
import subprocess
import signal
import time
import psutil
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional


class TempInstanceManager:
    """Manages temporary FiberWise instances for isolated testing."""
    
    def __init__(self, instance_id: str = None):
        if instance_id is None:
            # Generate instance ID with timestamp and UUID for uniqueness
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            uuid_part = str(uuid.uuid4())[:8]
            instance_id = f"test_{timestamp}_{uuid_part}"
        self.instance_id = instance_id
        self.base_dir = Path(__file__).parent.parent
        self.temp_instances_dir = self.base_dir / "temp-instances"
        self.instance_dir = self.temp_instances_dir / self.instance_id
        
        # Port allocation - use instance ID hash to get consistent ports
        # Avoid unsafe ports that browsers block (like 6667 IRC)
        unsafe_ports = {6667, 6668, 6669, 6670}  # IRC and other blocked ports
        port_base = 6000 + abs(hash(self.instance_id)) % 1000
        while port_base in unsafe_ports or (port_base + 1) in unsafe_ports:
            port_base = 6000 + (port_base - 6000 + 1) % 1000
        
        self.web_port = port_base
        self.api_port = port_base + 1
        
        self.base_url = f"http://localhost:{self.web_port}"
        self.api_url = f"http://localhost:{self.api_port}"
        
        # Process tracking
        self.web_process = None
        self.api_process = None
        self.frontend_process = None
        
        # Source paths
        self.fiberwise_core_web_path = self.base_dir.parent / "fiberwise-core-web"
        self.fiberwise_path = self.base_dir.parent / "fiberwise"
        
    def create_instance(self, use_bootstrap: bool = True) -> bool:
        """Create a temporary FiberWise instance using bootstrap system."""
        try:
            print(f"[INFO] Creating temp instance {self.instance_id}...")
            
            if use_bootstrap:
                # Use the new bootstrap system
                return self._create_with_bootstrap()
            else:
                # Fallback to old method
                return self._create_legacy()
                
        except Exception as e:
            print(f"[ERROR] Failed to create temp instance {self.instance_id}: {e}")
            return False
    
    def _create_with_bootstrap(self) -> bool:
        """Create instance using the bootstrap system."""
        try:
            # Import bootstrap system
            bootstrap_script = self.base_dir / "bootstrap.py"
            if not bootstrap_script.exists():
                print("[WARN] Bootstrap script not found, falling back to legacy method")
                return self._create_legacy()
            
            print("[INFO] Running bootstrap system (this may take a few minutes)...")
            print("[INFO] Bootstrap will copy files and install dependencies...")
            
            # Run bootstrap command
            import subprocess
            import sys
            
            cmd = [
                sys.executable, str(bootstrap_script), "bootstrap",
                "--dev", "--instance-id", self.instance_id,
                "--port-base", str(self.web_port)
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, cwd=self.base_dir)
            
            if result.returncode == 0:
                print(f"[OK] Bootstrap completed for {self.instance_id}")
                return True
            else:
                print(f"[ERROR] Bootstrap failed: {result.stderr}")
                return self._create_legacy()
                
        except Exception as e:
            print(f"[WARN] Bootstrap method failed: {e}, trying legacy")
            return self._create_legacy()
    
    def _create_legacy(self) -> bool:
        """Create instance using legacy method."""
        try:
            # Ensure temp instances directory exists
            self.temp_instances_dir.mkdir(exist_ok=True)
            
            # Remove existing instance if it exists
            if self.instance_dir.exists():
                self.cleanup_instance()
            
            # Check if source directories exist
            if not self.fiberwise_core_web_path.exists():
                print(f"[WARN] fiberwise-core-web not found at {self.fiberwise_core_web_path}")
                return False
            
            # Copy fiberwise-core-web to temp directory, ignoring large directories
            print(f"[INFO] Copying fiberwise-core-web to {self.instance_dir} (ignoring large directories)...")
            ignore_patterns = shutil.ignore_patterns(
                'node_modules', '.git', 'dist', 'build', '*.pyc', '__pycache__', '.DS_Store'
            )
            shutil.copytree(
                self.fiberwise_core_web_path,
                self.instance_dir,
                ignore=ignore_patterns
            )
            
            # Create instance-specific configuration
            self._create_instance_config()
            
            # Install dependencies if needed
            self._setup_dependencies()
            
            print(f"[OK] Created temp instance {self.instance_id} at {self.instance_dir}")
            return True
            
        except Exception as e:
            print(f"[ERROR] Legacy creation failed: {e}")
            return False
    
    def _create_instance_config(self):
        """Create instance-specific configuration files with proper settings management."""
        # Create config directory
        config_dir = self.instance_dir / "config"
        config_dir.mkdir(exist_ok=True)
        
        # Create local data directories for storage
        local_data_dir = self.instance_dir / "local_data"
        uploads_dir = local_data_dir / "uploads"
        app_bundles_dir = local_data_dir / "app_bundles"
        entity_bundles_dir = local_data_dir / "entity_bundles"
        
        local_data_dir.mkdir(exist_ok=True)
        uploads_dir.mkdir(exist_ok=True)
        app_bundles_dir.mkdir(exist_ok=True)
        entity_bundles_dir.mkdir(exist_ok=True)
        
        # Instance-specific test configuration
        test_config = {
            "web_port": self.web_port,
            "api_port": self.api_port,
            "database_url": f"sqlite:///{self.instance_dir}/local_data/fiberwise.db",
            "instance_id": self.instance_id,
            "temp_instance": True,
            "environment": "test",
            "debug": True,
            "log_level": "INFO",
            "storage": {
                "uploads_path": str(uploads_dir),
                "app_bundles_path": str(app_bundles_dir),
                "entity_bundles_path": str(entity_bundles_dir)
            }
        }
        
        config_file = config_dir / "test.json"
        with open(config_file, 'w') as f:
            json.dump(test_config, f, indent=2)
        
        # Create environment file with proper settings
        env_file = self.instance_dir / ".env.test"
        env_content = f"""# Temp instance environment
NODE_ENV=test
FIBERWISE_MODE=development
PORT={self.web_port}
API_PORT={self.api_port}
DATABASE_URL=sqlite:///{self.instance_dir}/local_data/fiberwise.db
INSTANCE_ID={self.instance_id}
TEMP_INSTANCE=true

# Storage paths
UPLOADS_PATH={uploads_dir}
APP_BUNDLES_PATH={app_bundles_dir}
APP_BUNDLES_DIR={app_bundles_dir}/apps
ENTITY_BUNDLES_PATH={entity_bundles_dir}

# Development settings
DEBUG=true
LOG_LEVEL=INFO
"""
        with open(env_file, 'w') as f:
            f.write(env_content.strip())
        
        # Create settings.py override for Python backend
        settings_file = self.instance_dir / "temp_settings.py"
        settings_content = f'''"""
Temporary instance settings override
"""
import os
from pathlib import Path

# Instance paths
INSTANCE_DIR = Path(__file__).parent
LOCAL_DATA_DIR = INSTANCE_DIR / "local_data"

# Database settings
DATABASE_URL = "sqlite:///{self.instance_dir / 'local_data' / 'fiberwise.db'}"

# Storage settings
UPLOADS_PATH = str(LOCAL_DATA_DIR / "uploads")
APP_BUNDLES_PATH = str(LOCAL_DATA_DIR / "app_bundles")
ENTITY_BUNDLES_PATH = str(LOCAL_DATA_DIR / "entity_bundles")

# Server settings
DEBUG = True
PORT = {self.web_port}
HOST = "127.0.0.1"

# Instance identification
INSTANCE_ID = "{self.instance_id}"
TEMP_INSTANCE = True
ENVIRONMENT = "test"
'''
        with open(settings_file, 'w') as f:
            f.write(settings_content)
        
        print(f"[OK] Created configuration and storage structure for instance {self.instance_id}")
        print(f"     Database: {self.instance_dir / 'local_data' / 'fiberwise.db'}")
        print(f"     Storage: {local_data_dir}")
    
    def _setup_dependencies(self):
        """Set up dependencies for the temp instance."""
        try:
            # Check if node_modules exists
            node_modules = self.instance_dir / "node_modules"
            package_json = self.instance_dir / "package.json"
            
            if package_json.exists() and not node_modules.exists():
                print(f"[INFO] Installing npm dependencies for {self.instance_id}...")
                subprocess.run(
                    ["npm", "install"],
                    cwd=self.instance_dir,
                    check=True,
                    capture_output=True,
                    text=True
                )
                print(f"[OK] Dependencies installed for {self.instance_id}")
            
        except subprocess.CalledProcessError as e:
            print(f"[WARN] Failed to install dependencies: {e}")
        except Exception as e:
            print(f"[WARN] Error setting up dependencies: {e}")
    
    def start_instance(self) -> bool:
        """Start the temporary FiberWise instance."""
        try:
            if not self.instance_dir.exists():
                print(f"[ERROR] Instance directory {self.instance_dir} does not exist")
                return False
            
            print(f"[INFO] Starting temp instance {self.instance_id}...")
            print("[INFO] This includes starting frontend (Vite) and backend (uvicorn) servers...")
            print("[INFO] Please wait while services initialize...")
            
            # Start web server
            web_success = self._start_web_server()
            if not web_success:
                return False
            
            # Start API server if fiberwise backend is available
            api_success = self._start_api_server()
            
            # Wait for services to be ready
            if self._wait_for_services():
                print(f"[OK] Temp instance {self.instance_id} started successfully")
                print(f"     Web: {self.base_url}")
                print(f"     API: {self.api_url}")
                return True
            else:
                self.stop_instance()
                return False
            
        except Exception as e:
            print(f"[ERROR] Failed to start temp instance {self.instance_id}: {e}")
            self.stop_instance()
            return False
    
    def _start_web_server(self) -> bool:
        """Start the web server using correct fiberwise-core-web structure."""
        try:
            # Check if this looks like a FiberWise instance (has main.py)
            main_py = self.instance_dir / "main.py"
            fiberwise_core_dir = self.instance_dir / "fiberwise_core"
            
            if main_py.exists() and fiberwise_core_dir.exists():
                print(f"[INFO] Found FiberWise structure - starting frontend and backend")
                
                # Step 1: Install npm dependencies in fiberwise_core
                package_json = fiberwise_core_dir / "package.json"
                node_modules = fiberwise_core_dir / "node_modules"
                
                if package_json.exists() and not node_modules.exists():
                    print(f"[INFO] Installing npm dependencies in fiberwise_core...")
                    print(f"[DEBUG] Running: npm install in {fiberwise_core_dir}")
                    try:
                        npm_install = subprocess.run(
                            ["npm", "install"],
                            cwd=fiberwise_core_dir,
                            capture_output=True,
                            text=True,
                            timeout=120,
                            shell=True
                        )
                        print(f"[DEBUG] npm install return code: {npm_install.returncode}")
                        if npm_install.returncode == 0:
                            print(f"[OK] npm dependencies installed")
                            if npm_install.stdout:
                                print(f"[DEBUG] npm stdout: {npm_install.stdout[:300]}")
                        else:
                            print(f"[WARN] npm install had issues: {npm_install.stderr[:200]}")
                            if npm_install.stdout:
                                print(f"[DEBUG] npm stdout: {npm_install.stdout[:300]}")
                    except subprocess.TimeoutExpired:
                        print(f"[ERROR] npm install timed out after 120 seconds")
                    except Exception as e:
                        print(f"[WARN] npm install error: {e}")
                else:
                    if not package_json.exists():
                        print(f"[DEBUG] No package.json found at {package_json}")
                    if node_modules.exists():
                        print(f"[DEBUG] node_modules already exists at {node_modules}")
                
                # Step 2: Start Vite dev server in background
                print(f"[INFO] Starting Vite dev server in fiberwise_core...")
                print(f"[DEBUG] Vite will start on port {self.web_port + 1000}")
                try:
                    vite_port = self.web_port + 1000  # Use different port for Vite
                    
                    env = os.environ.copy()
                    env["PORT"] = str(vite_port)
                    env["VITE_PORT"] = str(vite_port)
                    env["VITE_DEV_PORT"] = str(vite_port)  # This is what vite.config.js looks for
                    
                    print(f"[DEBUG] Running: npm run dev in {fiberwise_core_dir}")
                    print(f"[DEBUG] VITE_DEV_PORT environment variable set to: {vite_port}")
                    
                    # Start Vite dev server - let vite.config.js handle the port from VITE_DEV_PORT
                    self.frontend_process = subprocess.Popen(
                        ["npm", "run", "dev"],
                        cwd=fiberwise_core_dir,
                        env=env,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True,
                        shell=True
                    )
                    
                    print(f"[INFO] Vite dev server process started (PID: {self.frontend_process.pid})")
                    print(f"[INFO] Vite should be available on port {vite_port}")
                    
                    # Give Vite time to start
                    import time
                    print(f"[DEBUG] Waiting 3 seconds for Vite to initialize...")
                    time.sleep(3)
                    
                    # Check if process is still running
                    if self.frontend_process.poll() is None:
                        print(f"[OK] Vite dev server process is running")
                    else:
                        print(f"[WARN] Vite dev server process exited with code: {self.frontend_process.poll()}")
                    
                except Exception as e:
                    print(f"[WARN] Vite dev server error: {e}")
                    self.frontend_process = None
                
                # Step 3: Start Python backend with proper settings
                print(f"[INFO] Starting Python backend server on port {self.web_port}...")
                print(f"[DEBUG] Backend will run from {self.instance_dir}")
                
                env = os.environ.copy()
                # Force UTF-8 encoding for subprocess stdout/stderr on Windows
                env["PYTHONIOENCODING"] = "utf-8"
                env["FIBERWISE_MODE"] = "development"
                env["ENVIRONMENT"] = "development"  # Ensure main.py detects development mode
                env["TEMP_INSTANCE"] = "true"
                env["DATABASE_URL"] = f"sqlite:///{self.instance_dir}/local_data/fiberwise.db"
                env["PORT"] = str(self.web_port)
                env["INSTANCE_ID"] = self.instance_id
                env["WORKER_ENABLED"] = "false"  # Enable background worker for processing activations
                
                # IMPORTANT: Disable environment file loading to prevent port conflicts
                env["FIBERWISE_USE_HOME_DIR"] = "false"  # Don't load .env.fiber
                # Override any potential .env.local settings
                env["BASE_URL"] = f"http://localhost:{self.web_port}"
                
                # Add Vite port for backend template context
                vite_port = self.web_port + 1000
                env["VITE_DEV_PORT"] = str(vite_port)
                
                # Add storage paths
                local_data_dir = self.instance_dir / "local_data"
                env["UPLOADS_PATH"] = str(local_data_dir / "uploads")
                env["APP_BUNDLES_PATH"] = str(local_data_dir / "app_bundles")
                env["APP_BUNDLES_DIR"] = str(local_data_dir / "app_bundles" / "apps")
                env["ENTITY_BUNDLES_PATH"] = str(local_data_dir / "entity_bundles")
                
                # Handle conflicting .env files - override them with correct settings
                print(f"[DEBUG] Creating .env.local for temp instance with correct port settings...")
                
                # Create a custom .env.local for this temp instance (main.py expects this file)
                env_local_content = f"""# Temporary test instance environment - auto-generated for {self.instance_id}
# This file is expected by main.py for local development configuration

# Environment settings
ENVIRONMENT=development
DEBUG=true
TEMP_INSTANCE=true

# Port settings for this test instance  
PORT={self.web_port}
BASE_URL=http://localhost:{self.web_port}
HOST=0.0.0.0

# Database (isolated for this test instance)
DB_PROVIDER=sqlite
DATABASE_URL=sqlite:///{local_data_dir}/fiberwise.db

# Storage (isolated for this test instance)
STORAGE_PROVIDER=local
UPLOADS_DIR={local_data_dir}/uploads
APP_BUNDLES_DIR={local_data_dir}/app_bundles/apps
ENTITY_BUNDLES_DIR={local_data_dir}/entity_bundles

# Vite frontend port
VITE_DEV_PORT={vite_port}

# Instance identification
INSTANCE_ID={self.instance_id}

# Worker settings
WORKER_ENABLED=false

# Security (temp key for testing)
SECRET_KEY=temp-test-secret-{self.instance_id}

# API settings  
API_PREFIX=/api/v1

# CORS settings
CORS_ORIGINS=["http://localhost:{self.web_port}", "http://localhost:{vite_port}", "http://localhost:3000", "http://localhost:5556"]

# Project settings
PROJECT_NAME=FiberWise Core Web (Test Instance)
VERSION=0.0.1

# Fiber API settings (for testing)
FIBER_API_BASE_URL=http://localhost:{self.web_port}/api/v1
FIBER_API_KEY=temp-test-api-key-{self.instance_id}

# OAuth settings (empty for testing)
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=
GITHUB_CLIENT_ID=
GITHUB_CLIENT_SECRET=
MICROSOFT_CLIENT_ID=
MICROSOFT_CLIENT_SECRET=

# Platform settings
PLATFORM_BASE_URL=http://localhost:{self.web_port}

# Disable home directory mode (don't load .env.fiber)
FIBERWISE_USE_HOME_DIR=false
"""
                
                # Write/overwrite the .env.local file that main.py expects
                env_local_file = self.instance_dir / ".env.local"
                with open(env_local_file, 'w') as f:
                    f.write(env_local_content)
                print(f"[DEBUG] Created .env.local with PORT={self.web_port} for temp instance")
                
                # Remove .env.production if it exists  
                env_production_file = self.instance_dir / ".env.production"
                if env_production_file.exists():
                    print(f"[DEBUG] Removing .env.production file")
                    env_production_file.unlink()
                
                # Remove .env.fiber if it exists (to prevent conflicts)
                env_fiber_file = self.instance_dir / ".env.fiber"
                if env_fiber_file.exists():
                    print(f"[DEBUG] Removing .env.fiber file to prevent port conflicts")
                    env_fiber_file.unlink()
                
                # Point to temp settings and add required Python paths
                env["FIBERWISE_SETTINGS_MODULE"] = "temp_settings"
                
                # Add current instance to Python path
                instance_python_path = str(self.instance_dir)
                
                # Add fiberwise-common to Python path (essential for api.core imports)
                fiberwise_common_path = self.base_dir.parent / "fiberwise-common"
                
                # Add fiberwise root to Python path (for other dependencies)
                fiberwise_root_path = self.base_dir.parent / "fiberwise"
                # Build PYTHONPATH with all required paths
                python_paths = [
                    instance_python_path,
                    str(fiberwise_common_path),
                    str(fiberwise_root_path)
                ]
                
                # Add existing PYTHONPATH if it exists
                existing_pythonpath = env.get("PYTHONPATH", "")
                if existing_pythonpath:
                    python_paths.append(existing_pythonpath)
                
                env["PYTHONPATH"] = os.pathsep.join(python_paths)
                
                print(f"[DEBUG] Set PYTHONPATH to: {env['PYTHONPATH']}")
                print(f"[DEBUG] This includes fiberwise-common: {fiberwise_common_path}")
                print(f"[DEBUG] This includes fiberwise root: {fiberwise_root_path}")
                
                print(f"[DEBUG] Running uvicorn directly: uvicorn main:app --port {self.web_port} --host 127.0.0.1")
                print(f"[DEBUG] Environment: PORT={self.web_port}, DATABASE_URL={env['DATABASE_URL']}")
                
                # Start uvicorn directly for better control
                import sys  # Make sure sys is available in this scope
                
                # Create log files for persistent logging
                log_dir = self.instance_dir / "logs"
                log_dir.mkdir(exist_ok=True)
                self.server_log_file = log_dir / "server.log"
                self.server_error_file = log_dir / "server_error.log"
                
                print(f"[INFO] Server logs will be saved to: {self.server_log_file}")
                print(f"[INFO] Server errors will be saved to: {self.server_error_file}")
                
                # Open log files
                stdout_file = open(self.server_log_file, 'w', encoding='utf-8')
                stderr_file = open(self.server_error_file, 'w', encoding='utf-8')
                
                self.web_process = subprocess.Popen(
                    [sys.executable, "-m", "uvicorn", "main:app", 
                     "--host", "127.0.0.1", "--port", str(self.web_port), 
                     "--reload", "--log-level", "debug"],  # Changed to debug for more info
                    cwd=self.instance_dir,
                    env=env,
                    stdout=stdout_file,
                    stderr=stderr_file,
                    text=True
                )
                
                print(f"[INFO] Python backend process started (PID: {self.web_process.pid})")
                print(f"[INFO] Monitoring server logs in real-time...")
                
                # Give backend a moment to start
                import time
                print(f"[DEBUG] Waiting 5 seconds for backend to initialize...")
                time.sleep(5)
                
                # Monitor initial startup logs
                self._show_recent_logs(initial_startup=True)
                
                # Check if process is still running
                if self.web_process.poll() is None:
                    print(f"[OK] Python backend process is running")
                else:
                    print(f"[ERROR] Python backend process exited with code: {self.web_process.poll()}")
                    self._show_recent_logs(show_errors=True)
                    return False
                
                # Give it a bit more time and check for startup logs
                time.sleep(5)  # Give more time for uvicorn to start
                if self.web_process.poll() is not None:
                    print(f"[ERROR] Backend process died after additional wait")
                    try:
                        stdout, stderr = self.web_process.communicate(timeout=1)
                        if stderr:
                            print(f"[ERROR] Backend stderr: {stderr[:500]}")
                        if stdout:
                            print(f"[DEBUG] Backend stdout: {stdout[:500]}")
                    except:
                        pass
                    return False
                else:
                    # Process still running, try to get some output
                    print(f"[DEBUG] Backend process still running, checking output...")
                    try:
                        # Give it a moment to produce output
                        import select
                        import sys
                        if hasattr(select, 'select'):
                            # Unix-like systems
                            ready, _, _ = select.select([self.web_process.stdout], [], [], 1)
                            if ready:
                                output = self.web_process.stdout.read(500)
                                if output:
                                    print(f"[DEBUG] Recent backend output: {output}")
                        else:
                            # Windows - just try to peek at the output
                            pass
                    except Exception as e:
                        print(f"[DEBUG] Could not read backend output: {e}")
                
                print(f"[OK] Backend startup sequence completed")
                return True
                
            else:
                # Fallback for non-FiberWise projects
                print(f"[INFO] Not a FiberWise instance, using fallback startup")
                return self._start_fallback_server()
            
        except Exception as e:
            print(f"[ERROR] Failed to start FiberWise server: {e}")
            return False
    
    def _start_fallback_server(self) -> bool:
        """Fallback server startup for non-FiberWise projects."""
        try:
            # Try to find package.json for npm-based projects
            package_json_path = self.instance_dir / "package.json"
            
            if package_json_path.exists():
                with open(package_json_path) as f:
                    package_data = json.load(f)
                    scripts = package_data.get("scripts", {})
                    
                    # Try different script names
                    start_script = None
                    for script_name in ["dev", "start", "serve"]:
                        if script_name in scripts:
                            start_script = script_name
                            break
                    
                    if start_script:
                        cmd = ["npm", "run", start_script]
                    else:
                        # Fallback to direct commands
                        if (self.instance_dir / "vite.config.js").exists():
                            cmd = ["npx", "vite", "--port", str(self.web_port)]
                        else:
                            cmd = ["python", "-m", "http.server", str(self.web_port)]
            else:
                # No package.json, use simple HTTP server
                cmd = ["python", "-m", "http.server", str(self.web_port)]
            
            # Set environment for fallback servers
            env = os.environ.copy()
            env["PORT"] = str(self.web_port)
            env["NODE_ENV"] = "development"
            env["TEMP_INSTANCE"] = "true"
            
            print(f"[INFO] Starting fallback server: {' '.join(cmd)}")
            
            # Start process
            self.web_process = subprocess.Popen(
                cmd,
                cwd=self.instance_dir,
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                shell=True
            )
            
            print(f"[INFO] Fallback server started on port {self.web_port}")
            return True
            
        except Exception as e:
            print(f"[ERROR] Failed to start fallback server: {e}")
            return False
    
    def _start_api_server(self) -> bool:
        """Skip separate API server - fiber start handles both frontend and API."""
        try:
            # Check if this looks like a FiberWise instance
            main_py = self.instance_dir / "main.py"
            
            if main_py.exists():
                print(f"[INFO] FiberWise instance detected - API integrated with web server")
                return True  # fiber start command handles both web and API
            else:
                print(f"[INFO] No FiberWise main.py found - skipping API server")
                return True  # Not critical for non-FiberWise instances
            
        except Exception as e:
            print(f"[WARN] Error checking for API server: {e}")
            return True  # Not critical for web-only tests
    
    def _wait_for_services(self, timeout: int = 30) -> bool:
        """Wait for services to be ready."""
        import requests
        
        print(f"[INFO] Waiting for services to be ready at {self.base_url}...")
        print(f"[DEBUG] Will wait up to {timeout} seconds")
        
        start_time = time.time()
        attempts = 0
        
        while time.time() - start_time < timeout:
            attempts += 1
            elapsed = int(time.time() - start_time)
            
            try:
                # Check web server
                print(f"[DEBUG] Attempt {attempts} (after {elapsed}s): Checking {self.base_url}")
                response = requests.get(f"{self.base_url}", timeout=2)
                print(f"[DEBUG] Got response: status={response.status_code}")
                
                if response.status_code < 500:
                    print(f"[OK] Web server ready at {self.base_url} (status: {response.status_code})")
                    return True
                else:
                    print(f"[DEBUG] Server responded but with status {response.status_code}")
                    
            except requests.exceptions.ConnectionError as e:
                print(f"[DEBUG] Connection refused (server not ready yet)")
            except requests.exceptions.Timeout as e:
                print(f"[DEBUG] Request timed out")
            except Exception as e:
                print(f"[DEBUG] Request error: {e}")
            
            if attempts % 10 == 0:  # Every 10 seconds, show progress
                print(f"[INFO] Still waiting... ({elapsed}/{timeout}s)")
            
            time.sleep(1)
        
        print(f"[ERROR] Services not ready after {timeout} seconds")
        print(f"[DEBUG] Made {attempts} attempts")
        
        # Final check of processes
        if self.web_process:
            if self.web_process.poll() is None:
                print(f"[DEBUG] Backend process is still running (PID: {self.web_process.pid})")
            else:
                print(f"[ERROR] Backend process died (exit code: {self.web_process.poll()})")
        
        if self.frontend_process:
            if self.frontend_process.poll() is None:
                print(f"[DEBUG] Frontend process is still running (PID: {self.frontend_process.pid})")
            else:
                print(f"[ERROR] Frontend process died (exit code: {self.frontend_process.poll()})")
        
        return False
    
    def _stop_process_tree(self, process, name="process"):
        """Gracefully stop a process and its entire process tree."""
        if not process:
            return
        
        try:
            parent = psutil.Process(process.pid)
            children = parent.children(recursive=True)
            
            # Terminate all children first
            for child in children:
                try:
                    child.terminate()
                except psutil.NoSuchProcess:
                    pass
            
            # Terminate the parent
            try:
                parent.terminate()
            except psutil.NoSuchProcess:
                pass
            
            # Wait for processes to terminate
            gone, alive = psutil.wait_procs(children + [parent], timeout=3)
            
            # Force kill any stubborn processes
            for p in alive:
                try:
                    p.kill()
                except psutil.NoSuchProcess:
                    pass
            
            print(f"[OK] {name.capitalize()} process stopped")
        
        except psutil.NoSuchProcess:
            print(f"[INFO] {name.capitalize()} process already stopped.")
        except Exception as e:
            print(f"[WARN] Error stopping {name} process tree: {e}")

    def stop_instance(self):
        """Stop the temporary instance processes."""
        try:
            print(f"[INFO] Stopping temp instance {self.instance_id}...")
            
            # Stop process trees
            self._stop_process_tree(self.frontend_process, "Frontend")
            self.frontend_process = None
            
            self._stop_process_tree(self.web_process, "Backend")
            self.web_process = None
            
            self._stop_process_tree(self.api_process, "API")
            self.api_process = None
            
            # Kill any remaining processes on our ports as a fallback
            self._kill_processes_on_ports()
            
            print(f"[OK] Stopped temp instance {self.instance_id}")
            
        except Exception as e:
            print(f"[WARN] Error stopping temp instance: {e}")
    
    def _kill_processes_on_ports(self):
        """Fallback to kill any processes running on our allocated ports."""
        try:
            for port in [self.web_port, self.api_port]:
                for proc in psutil.process_iter(attrs=['pid']):
                    try:
                        for conn in proc.connections():
                            if conn.laddr.port == port:
                                proc.kill()
                                print(f"[INFO] Killed process on port {port}")
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        continue
        except Exception as e:
            print(f"[WARN] Error killing processes on ports: {e}")
    
    def cleanup_instance(self, dump_logs=True):
        """Clean up the temporary instance."""
        try:
            # Dump complete logs before cleanup if requested
            if dump_logs:
                print(f"\n[INFO] Dumping server logs before cleanup...")
                self.dump_full_logs()
            
            # Stop processes first
            self.stop_instance()

            # Add a small delay to allow file handles to be released on Windows
            if sys.platform == "win32":
                time.sleep(1)
            
            # Remove instance directory
            if self.instance_dir.exists():
                shutil.rmtree(self.instance_dir)
                print(f"[OK] Cleaned up temp instance {self.instance_id}")
            
        except Exception as e:
            print(f"[WARN] Error cleaning up temp instance: {e}")
    
    def cleanup(self, *args, **kwargs):
        """Alias for cleanup_instance for backward compatibility or typos."""
        print("[WARN] .cleanup() is deprecated, please use .cleanup_instance()")
        self.cleanup_instance(*args, **kwargs)

    def get_instance_info(self) -> Dict[str, Any]:
        """Get information about the instance."""
        return {
            "instance_id": self.instance_id,
            "instance_dir": str(self.instance_dir),
            "web_port": self.web_port,
            "api_port": self.api_port,
            "base_url": self.base_url,
            "api_url": self.api_url,
            "running": self.is_running()
        }
    
    def is_running(self) -> bool:
        """Check if the instance is currently running."""
        web_running = self.web_process and self.web_process.poll() is None
        return web_running
    
    def _show_recent_logs(self, initial_startup=False, show_errors=False, lines=20):
        """Show recent server logs to console."""
        try:
            if hasattr(self, 'server_log_file') and self.server_log_file.exists():
                print(f"\n[LOG] === Recent Server Output (last {lines} lines) ===")
                with open(self.server_log_file, 'r', encoding='utf-8') as f:
                    log_lines = f.readlines()
                    for line in log_lines[-lines:]:
                        print(f"[LOG] {line.rstrip()}")
                print(f"[LOG] === End Server Output ===\n")
            
            if show_errors and hasattr(self, 'server_error_file') and self.server_error_file.exists():
                print(f"\n[ERROR] === Recent Server Errors (last {lines} lines) ===")
                with open(self.server_error_file, 'r', encoding='utf-8') as f:
                    error_lines = f.readlines()
                    for line in error_lines[-lines:]:
                        print(f"[ERROR] {line.rstrip()}")
                print(f"[ERROR] === End Server Errors ===\n")
                
        except Exception as e:
            print(f"[WARN] Could not read log files: {e}")
    
    def dump_full_logs(self):
        """Dump complete server logs to console."""
        print("\n" + "="*80)
        print(f"COMPLETE SERVER LOGS FOR INSTANCE: {self.instance_id}")
        print("="*80)
        
        if hasattr(self, 'server_log_file') and self.server_log_file.exists():
            print(f"\n--- STANDARD OUTPUT LOG: {self.server_log_file} ---")
            try:
                with open(self.server_log_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if content.strip():
                        print(content)
                    else:
                        print("(Log file is empty)")
            except Exception as e:
                print(f"Error reading stdout log: {e}")
        else:
            print("\n--- NO STANDARD OUTPUT LOG FOUND ---")
        
        if hasattr(self, 'server_error_file') and self.server_error_file.exists():
            print(f"\n--- ERROR OUTPUT LOG: {self.server_error_file} ---")
            try:
                with open(self.server_error_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if content.strip():
                        print(content)
                    else:
                        print("(Error log file is empty)")
            except Exception as e:
                print(f"Error reading stderr log: {e}")
        else:
            print("\n--- NO ERROR OUTPUT LOG FOUND ---")
            
        print("\n" + "="*80)
        print("END OF SERVER LOGS")
        print("="*80 + "\n")
    
    def __enter__(self):
        """Context manager entry."""
        if self.create_instance() and self.start_instance():
            return self
        else:
            raise RuntimeError(f"Failed to create and start temp instance {self.instance_id}")
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.cleanup_instance()


# Utility functions
def create_temp_instance(instance_id: str = None) -> TempInstanceManager:
    """Create a temporary FiberWise instance."""
    return TempInstanceManager(instance_id)


def cleanup_all_temp_instances():
    """Clean up all temporary instances."""
    temp_instances_dir = Path(__file__).parent.parent / "temp-instances"
    
    if temp_instances_dir.exists():
        for instance_dir in temp_instances_dir.iterdir():
            if instance_dir.is_dir():
                try:
                    # Try to stop any running processes
                    manager = TempInstanceManager(instance_dir.name)
                    manager.cleanup_instance()
                except:
                    # If that fails, just remove the directory
                    shutil.rmtree(instance_dir)
        
        print("[OK] Cleaned up all temporary instances")


if __name__ == "__main__":
    # Test the temp instance manager
    print("[INFO] Starting FiberWise temp instance test...")
    print("[INFO] This may take a moment for initial setup (npm install, etc.)")
    print("[INFO] Please wait while the instance is created and started...")
    print()
    
    with create_temp_instance("test_instance") as instance:
        print()
        print(f"[SUCCESS] Temp instance ready!")
        print(f"Test instance info: {instance.get_instance_info()}")
        print()
        print("Press Enter to cleanup and exit...")
        input()
