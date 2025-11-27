"""
CO-HERE-US Report Generator
Generates full percentile charts + pass/fail conclusions
"""

import numpy as np

class ReportGenerator:
    def __init__(self, results):
        self.results = results

    def generate(self):
        """Generate comprehensive validation report."""
        print("\n" + "=" * 80)
        print("CO-HERE-US NATIONAL-SCALE VALIDATION REPORT")
        print("=" * 80)
        print("\nTarget: $50,000 - $90,000 at age 25")
        print("Failure threshold: Below $30,000")
        print("=" * 80)

        stats = {}
        test_results = []

        for name, arr in self.results.items():
            arr = np.array(arr).astype(float)

            if arr.size == 0:
                continue

            if len(arr.shape) == 0:
                arr = np.array([arr])

            p10 = np.percentile(arr, 10)
            med = np.percentile(arr, 50)
            p90 = np.percentile(arr, 90)

            print(f"\n{'=' * 80}")
            print(f"{name.upper()}")
            print('=' * 80)
            print(f"10th percentile : ${p10:,.0f}")
            print(f"Median          : ${med:,.0f}")
            print(f"90th percentile : ${p90:,.0f}")

            if len(arr) > 1:
                print(f"Min             : ${np.min(arr):,.0f}")
                print(f"Max             : ${np.max(arr):,.0f}")
                print(f"Count           : {len(arr)}")

                # Check target achievement
                in_target = np.sum((arr >= 50000) & (arr <= 90000))
                above_30k = np.sum(arr >= 30000)

                print(f"\nIn target ($50k-$90k): {in_target}/{len(arr)} ({in_target/len(arr)*100:.1f}%)")
                print(f"Above failure ($30k):  {above_30k}/{len(arr)} ({above_30k/len(arr)*100:.1f}%)")

                # Verdict
                if above_30k == len(arr):
                    verdict = "✓ PASS"
                    test_results.append((name, True))
                else:
                    verdict = "✗ FAIL"
                    test_results.append((name, False))

                print(f"\nVERDICT: {verdict}")
            else:
                # Single value
                if arr[0] >= 30000:
                    verdict = "✓ PASS"
                    test_results.append((name, True))
                else:
                    verdict = "✗ FAIL"
                    test_results.append((name, False))

                print(f"\nVERDICT: {verdict}")

            stats[name] = [p10, med, p90]

        # Final summary
        print("\n" + "=" * 80)
        print("FINAL SUMMARY")
        print("=" * 80)

        passed = sum(1 for _, result in test_results if result)
        total = len(test_results)

        print(f"\nTests passed: {passed}/{total}")
        print("\nDetailed results:")
        for name, result in test_results:
            status = "✓ PASS" if result else "✗ FAIL"
            print(f"  {name}: {status}")

        print("\n" + "=" * 80)
        if passed == total:
            print("✓✓✓ CO-HERE-US PASSES ALL TESTS ✓✓✓")
            print("\nSystem validated for national-scale deployment")
        elif passed >= total * 0.8:
            print("⚠ CO-HERE-US PASSES MOST TESTS")
            print(f"\n{passed}/{total} scenarios validated")
            print("Review failures for production readiness")
        else:
            print("✗ CO-HERE-US NEEDS REFINEMENT")
            print(f"\nOnly {passed}/{total} scenarios passed")

        print("=" * 80)

        return stats
