"""
ARC LUNA — LUNAR LANDING SITE NAVIGATOR
Direct Scientific Test Runner
"""

import sys
import os
import time

# Ensure backend directory is in sys.path
backend_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, backend_dir)
sys.path.insert(0, os.path.join(backend_dir, "tests"))

from test_scientific_modules import (
    TestLunarCoordinates,
    TestGravityCalculations,
    TestSolarIllumination,
    TestEarthVisibility,
    TestSolarEnergy,
    TestTerrainAnalysis,
    TestReportGenerator
)

test_classes = [
    TestLunarCoordinates,
    TestGravityCalculations,
    TestSolarIllumination,
    TestEarthVisibility,
    TestSolarEnergy,
    TestTerrainAnalysis,
    TestReportGenerator
]

def run_all_tests():
    print("=" * 70)
    print("ARC LUNA — SCIENTIFIC CALCULATION VERIFICATION & TEST SUITE")
    print("=" * 70)
    
    total_run = 0
    total_passed = 0
    total_failed = 0
    start_time = time.time()
    
    for cls in test_classes:
        instance = cls()
        test_methods = [m for m in dir(instance) if m.startswith("test_")]
        print(f"\n--- Running {cls.__name__} ({len(test_methods)} tests) ---")
        for m_name in test_methods:
            total_run += 1
            method = getattr(instance, m_name)
            try:
                t0 = time.time()
                method()
                dt = (time.time() - t0) * 1000.0
                print(f"  [PASS] {m_name} ({dt:.2f} ms)")
                total_passed += 1
            except Exception as e:
                print(f"  [FAIL] {m_name}: {e}")
                total_failed += 1
                
    elapsed = (time.time() - start_time) * 1000.0
    print("\n" + "=" * 70)
    print(f"TEST RESULTS: {total_passed}/{total_run} PASSED in {elapsed:.1f} ms")
    if total_failed == 0:
        print("STATUS: ALL MATHEMATICAL AND SCIENTIFIC TESTS PASSED PERFECTLY!")
    else:
        print(f"STATUS: {total_failed} TESTS FAILED")
    print("=" * 70)
    return total_failed

if __name__ == "__main__":
    sys.exit(run_all_tests())
