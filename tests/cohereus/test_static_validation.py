"""
CO-HERE-US Static Validation Tests

Tests that don't require PyTorch runtime:
- Code structure validation
- Import validation
- API surface validation
- Documentation validation
"""

import sys
import ast
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent.parent.parent / "src"
sys.path.insert(0, str(src_path))


class TestCodeStructure:
    """Validate code structure and syntax"""

    def test_all_files_parse_correctly(self):
        """Ensure all Python files have valid syntax"""
        cohereus_path = src_path / "cohereus"
        python_files = list(cohereus_path.rglob("*.py"))

        print(f"\n✓ Found {len(python_files)} Python files")

        errors = []
        for py_file in python_files:
            try:
                with open(py_file, 'r') as f:
                    code = f.read()
                    ast.parse(code)
                print(f"  ✓ {py_file.relative_to(src_path)}")
            except SyntaxError as e:
                errors.append(f"{py_file}: {e}")
                print(f"  ✗ {py_file.relative_to(src_path)}: {e}")

        assert len(errors) == 0, f"Syntax errors found:\n" + "\n".join(errors)
        print(f"\n✓ All files have valid syntax")

    def test_imports_structure(self):
        """Validate import structure"""
        # Check __init__.py files exist
        init_files = [
            src_path / "cohereus" / "__init__.py",
            src_path / "cohereus" / "core" / "__init__.py",
            src_path / "cohereus" / "orchestration" / "__init__.py",
            src_path / "cohereus" / "optimizer" / "__init__.py",
            src_path / "cohereus" / "observability" / "__init__.py",
        ]

        print("\n✓ Checking package structure:")
        for init_file in init_files:
            assert init_file.exists(), f"Missing {init_file}"
            print(f"  ✓ {init_file.relative_to(src_path)}")

        print(f"\n✓ Package structure is correct")

    def test_class_definitions(self):
        """Validate expected classes exist"""
        print("\n✓ Validating class definitions:")

        # RHL
        rhl_file = src_path / "cohereus" / "core" / "risk_harmonization.py"
        with open(rhl_file) as f:
            tree = ast.parse(f.read())
        classes = [node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]
        assert "RiskHarmonizationLayer" in classes
        print(f"  ✓ RiskHarmonizationLayer found")

        # SIL
        sil_file = src_path / "cohereus" / "core" / "strategy_identity.py"
        with open(sil_file) as f:
            tree = ast.parse(f.read())
        classes = [node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]
        assert "StrategyIdentityLayer" in classes
        print(f"  ✓ StrategyIdentityLayer found")

        # PSE
        pse_file = src_path / "cohereus" / "core" / "position_smoothing.py"
        with open(pse_file) as f:
            tree = ast.parse(f.read())
        classes = [node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]
        assert "PositionSmoothingEngine" in classes
        print(f"  ✓ PositionSmoothingEngine found")

        # Orchestrator
        orch_file = src_path / "cohereus" / "orchestration" / "account_orchestrator.py"
        with open(orch_file) as f:
            tree = ast.parse(f.read())
        classes = [node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]
        assert "AccountOrchestrator" in classes
        assert "CohortState" in classes
        print(f"  ✓ AccountOrchestrator found")
        print(f"  ✓ CohortState found")

        # IDS
        ids_file = src_path / "cohereus" / "orchestration" / "diversity_system.py"
        with open(ids_file) as f:
            tree = ast.parse(f.read())
        classes = [node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]
        assert "InterBotDiversitySystem" in classes
        print(f"  ✓ InterBotDiversitySystem found")

        # HOE
        hoe_file = src_path / "cohereus" / "optimizer" / "harmonic_optimizer.py"
        with open(hoe_file) as f:
            tree = ast.parse(f.read())
        classes = [node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]
        assert "HarmonicOptimizer" in classes
        print(f"  ✓ HarmonicOptimizer found")

        print(f"\n✓ All expected classes exist")

    def test_method_signatures(self):
        """Validate critical method signatures"""
        print("\n✓ Validating method signatures:")

        # RHL forward method
        rhl_file = src_path / "cohereus" / "core" / "risk_harmonization.py"
        with open(rhl_file) as f:
            tree = ast.parse(f.read())

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef) and node.name == "RiskHarmonizationLayer":
                methods = {n.name: n for n in node.body if isinstance(n, ast.FunctionDef)}
                assert "forward" in methods
                assert "clamp_range" in methods
                assert "smooth" in methods
                assert "predictive_drift" in methods
                assert "get_drift_metrics" in methods
                print(f"  ✓ RHL has required methods")

        # SIL forward method
        sil_file = src_path / "cohereus" / "core" / "strategy_identity.py"
        with open(sil_file) as f:
            tree = ast.parse(f.read())

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef) and node.name == "StrategyIdentityLayer":
                methods = {n.name: n for n in node.body if isinstance(n, ast.FunctionDef)}
                assert "forward" in methods
                assert "update_strategy" in methods
                assert "compute_deviation" in methods
                assert "enforce_boundaries" in methods
                print(f"  ✓ SIL has required methods")

        # AccountOrchestrator
        orch_file = src_path / "cohereus" / "orchestration" / "account_orchestrator.py"
        with open(orch_file) as f:
            tree = ast.parse(f.read())

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef) and node.name == "AccountOrchestrator":
                methods = {n.name: n for n in node.body if isinstance(n, ast.FunctionDef)}
                assert "register_account" in methods
                assert "batch_rebalance" in methods
                assert "get_total_aum" in methods
                print(f"  ✓ AccountOrchestrator has required methods")

        # IDS
        ids_file = src_path / "cohereus" / "orchestration" / "diversity_system.py"
        with open(ids_file) as f:
            tree = ast.parse(f.read())

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef) and node.name == "InterBotDiversitySystem":
                methods = {n.name: n for n in node.body if isinstance(n, ast.FunctionDef)}
                assert "should_rebalance" in methods
                assert "check_synchronization_risk" in methods
                assert "detect_liquidity_pressure" in methods
                assert "compute_diversity_score" in methods
                print(f"  ✓ IDS has required methods")

        print(f"\n✓ All critical methods exist")


class TestDocumentation:
    """Validate documentation exists"""

    def test_readme_exists(self):
        """Check README exists"""
        readme = src_path / "cohereus" / "README.md"
        assert readme.exists(), "README.md missing"

        with open(readme) as f:
            content = f.read()
            assert "CO-HERE-US" in content
            assert "EchoZero" in content
            assert "DNA" in content
            print(f"\n✓ README.md exists and contains required sections")

    def test_docstrings(self):
        """Check critical classes have docstrings"""
        print("\n✓ Validating docstrings:")

        files_to_check = [
            ("RiskHarmonizationLayer", src_path / "cohereus" / "core" / "risk_harmonization.py"),
            ("StrategyIdentityLayer", src_path / "cohereus" / "core" / "strategy_identity.py"),
            ("PositionSmoothingEngine", src_path / "cohereus" / "core" / "position_smoothing.py"),
            ("AccountOrchestrator", src_path / "cohereus" / "orchestration" / "account_orchestrator.py"),
            ("InterBotDiversitySystem", src_path / "cohereus" / "orchestration" / "diversity_system.py"),
            ("HarmonicOptimizer", src_path / "cohereus" / "optimizer" / "harmonic_optimizer.py"),
        ]

        for class_name, file_path in files_to_check:
            with open(file_path) as f:
                tree = ast.parse(f.read())

            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef) and node.name == class_name:
                    docstring = ast.get_docstring(node)
                    assert docstring is not None, f"{class_name} missing docstring"
                    assert len(docstring) > 50, f"{class_name} docstring too short"
                    print(f"  ✓ {class_name} has docstring")

        print(f"\n✓ All classes have docstrings")


class TestEchoZeroDNA:
    """Validate DNA traceability to EchoZero"""

    def test_dna_attribution(self):
        """Check DNA source attribution in files"""
        print("\n✓ Validating EchoZero DNA attribution:")

        # Check RHL references WIL 2.0
        with open(src_path / "cohereus" / "core" / "risk_harmonization.py") as f:
            content = f.read()
            assert "WIL 2.0" in content or "WantIntegrityLayerV2" in content
            assert "EchoZero" in content
            print(f"  ✓ RHL → WIL 2.0 attribution found")

        # Check SIL references IBL
        with open(src_path / "cohereus" / "core" / "strategy_identity.py") as f:
            content = f.read()
            assert "IBL" in content or "IdentityBoundaryLayer" in content
            assert "EchoZero" in content
            print(f"  ✓ SIL → IBL attribution found")

        # Check PSE references DCE
        with open(src_path / "cohereus" / "core" / "position_smoothing.py") as f:
            content = f.read()
            assert "DCE" in content or "DesireContinuityEngine" in content
            assert "EchoZero" in content
            print(f"  ✓ PSE → DCE attribution found")

        # Check HOE references dynamics
        with open(src_path / "cohereus" / "optimizer" / "harmonic_optimizer.py") as f:
            content = f.read()
            assert "dynamics" in content or "ψ-dynamics" in content
            assert "EchoZero" in content
            print(f"  ✓ HOE → ψ-dynamics attribution found")

        print(f"\n✓ All DNA attributions correct")


class TestFileMetrics:
    """Validate code metrics"""

    def test_total_lines_of_code(self):
        """Count total lines of code"""
        cohereus_path = src_path / "cohereus"
        python_files = list(cohereus_path.rglob("*.py"))

        total_lines = 0
        code_lines = 0
        comment_lines = 0
        blank_lines = 0

        for py_file in python_files:
            with open(py_file) as f:
                for line in f:
                    total_lines += 1
                    stripped = line.strip()
                    if not stripped:
                        blank_lines += 1
                    elif stripped.startswith('#') or stripped.startswith('"""') or stripped.startswith("'''"):
                        comment_lines += 1
                    else:
                        code_lines += 1

        print(f"\n✓ Code metrics:")
        print(f"  Total files: {len(python_files)}")
        print(f"  Total lines: {total_lines}")
        print(f"  Code lines: {code_lines}")
        print(f"  Comment/doc lines: {comment_lines}")
        print(f"  Blank lines: {blank_lines}")

        assert total_lines > 1500, "Insufficient code"
        assert code_lines > 1000, "Insufficient implementation"
        print(f"\n✓ Codebase size is substantial ({code_lines} lines of implementation)")


def run_all_tests():
    """Run all validation tests"""
    print("=" * 70)
    print("CO-HERE-US STATIC VALIDATION SUITE")
    print("=" * 70)

    test_classes = [
        TestCodeStructure(),
        TestDocumentation(),
        TestEchoZeroDNA(),
        TestFileMetrics(),
    ]

    total_tests = 0
    passed_tests = 0
    failed_tests = []

    for test_class in test_classes:
        class_name = test_class.__class__.__name__
        print(f"\n{'=' * 70}")
        print(f"{class_name}")
        print(f"{'=' * 70}")

        test_methods = [m for m in dir(test_class) if m.startswith("test_")]

        for method_name in test_methods:
            total_tests += 1
            try:
                method = getattr(test_class, method_name)
                method()
                passed_tests += 1
            except AssertionError as e:
                failed_tests.append((class_name, method_name, str(e)))
                print(f"\n✗ {method_name} FAILED: {e}")
            except Exception as e:
                failed_tests.append((class_name, method_name, str(e)))
                print(f"\n✗ {method_name} ERROR: {e}")

    print(f"\n{'=' * 70}")
    print(f"VALIDATION SUMMARY")
    print(f"{'=' * 70}")
    print(f"Total tests: {total_tests}")
    print(f"Passed: {passed_tests}")
    print(f"Failed: {len(failed_tests)}")

    if failed_tests:
        print(f"\nFAILURES:")
        for class_name, method_name, error in failed_tests:
            print(f"  ✗ {class_name}.{method_name}: {error}")
        return False
    else:
        print(f"\n✓ ALL VALIDATION TESTS PASSED")
        return True


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
