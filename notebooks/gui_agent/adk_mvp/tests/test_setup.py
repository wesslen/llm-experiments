"""
Setup and environment validation tests.

These tests verify that the environment is properly configured before
running agent tests. They check for required dependencies, environment
variables, and system tools.

Run these first: pytest tests/test_setup.py -v
"""

import os
import sys
import subprocess
import pytest


def test_python_version():
    """Verify Python version is 3.12 or higher."""
    version_info = sys.version_info
    assert version_info >= (3, 12), (
        f"Python 3.12+ required, found {version_info.major}.{version_info.minor}"
    )


def test_required_imports():
    """Test that all required libraries can be imported."""
    # Test google-adk
    try:
        import google.adk
        import google.adk.agents
        import google.adk.runners
        import google.adk.sessions
        import google.adk.tools.mcp_tool
    except ImportError as e:
        pytest.fail(f"Failed to import google-adk: {e}")

    # Test mcp
    try:
        import mcp
    except ImportError as e:
        pytest.fail(f"Failed to import mcp: {e}")

    # Test python-dotenv
    try:
        import dotenv
    except ImportError as e:
        pytest.fail(f"Failed to import python-dotenv: {e}")


def test_dev_imports():
    """Test that development dependencies can be imported."""
    # Test pytest
    try:
        import pytest
    except ImportError as e:
        pytest.fail(f"Failed to import pytest: {e}")

    # Test pytest-asyncio
    try:
        import pytest_asyncio
    except ImportError as e:
        pytest.fail(f"Failed to import pytest-asyncio: {e}")


def test_nodejs_available():
    """Check that Node.js is installed and accessible."""
    try:
        result = subprocess.run(
            ["node", "--version"],
            capture_output=True,
            text=True,
            timeout=5
        )
        assert result.returncode == 0, f"node command failed: {result.stderr}"

        version = result.stdout.strip()
        assert version.startswith("v"), f"Unexpected node version format: {version}"

        # Extract major version (e.g., "v20.11.0" -> 20)
        major_version = int(version[1:].split(".")[0])
        assert major_version >= 18, f"Node.js 18+ recommended, found v{major_version}"

    except FileNotFoundError:
        pytest.fail("node command not found. Please install Node.js")
    except subprocess.TimeoutExpired:
        pytest.fail("node --version command timed out")


def test_npx_available():
    """Check that npx is installed and accessible."""
    try:
        result = subprocess.run(
            ["npx", "--version"],
            capture_output=True,
            text=True,
            timeout=5
        )
        assert result.returncode == 0, f"npx command failed: {result.stderr}"

        version = result.stdout.strip()
        assert version, "npx version returned empty string"

    except FileNotFoundError:
        pytest.fail("npx command not found. Please install npm/npx")
    except subprocess.TimeoutExpired:
        pytest.fail("npx --version command timed out")


def test_playwright_mcp_package():
    """Verify that Playwright MCP package can be resolved by npx."""
    try:
        # Try to get help from the package (doesn't launch browser)
        result = subprocess.run(
            ["npx", "-y", "playwright-mcp@latest", "--help"],
            capture_output=True,
            text=True,
            timeout=30  # First run may need to download package
        )

        # Package should either show help or indicate it's an MCP server
        # (some MCP servers don't support --help)
        # Just verify npx can resolve and load the package
        assert result.returncode in [0, 1], (
            f"Failed to resolve playwright-mcp package: {result.stderr}"
        )

    except FileNotFoundError:
        pytest.fail("npx command not found")
    except subprocess.TimeoutExpired:
        pytest.fail("Playwright MCP package resolution timed out")


def test_gemini_api_key_set():
    """Check that GEMINI_API_KEY environment variable exists."""
    api_key = os.getenv("GEMINI_API_KEY")
    assert api_key is not None, (
        "GEMINI_API_KEY environment variable is not set. "
        "Please set it in .env file or environment. "
        "Get your key from: https://makersuite.google.com/app/apikey"
    )


def test_gemini_api_key_format():
    """Basic format validation for GEMINI_API_KEY."""
    api_key = os.getenv("GEMINI_API_KEY")

    # Skip if not set (will fail in previous test)
    if not api_key:
        pytest.skip("GEMINI_API_KEY not set")

    # Basic validation
    api_key = api_key.strip()
    assert len(api_key) >= 10, (
        f"GEMINI_API_KEY appears invalid (only {len(api_key)} characters). "
        "Please check your API key."
    )

    assert not api_key.startswith(" "), "GEMINI_API_KEY has leading whitespace"
    assert not api_key.endswith(" "), "GEMINI_API_KEY has trailing whitespace"


def test_adk_basic_init():
    """Verify LlmAgent can be imported and instantiated."""
    try:
        from google.adk.agents import LlmAgent

        # Create a minimal agent (doesn't call API, just validates imports)
        agent = LlmAgent(
            model="gemini-2.5-flash",
            name="test_agent",
            instruction="Test instruction",
            tools=[]
        )

        assert agent is not None
        assert agent.name == "test_agent"

    except Exception as e:
        pytest.fail(f"Failed to create basic LlmAgent: {e}")


def test_model_env_var():
    """Check that MODEL environment variable has sensible default or override."""
    model = os.getenv("MODEL", "gemini-2.5-flash")

    assert model, "MODEL should not be empty"
    assert model.startswith("gemini"), (
        f"MODEL should be a Gemini model name, got: {model}"
    )


if __name__ == "__main__":
    # Allow running this test file directly
    pytest.main([__file__, "-v"])
