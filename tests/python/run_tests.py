import os
import sys
import datetime

# Resolve paths
script_dir = os.path.dirname(os.path.abspath(__file__))
test_dir = os.path.dirname(script_dir)
base_dir = os.path.dirname(test_dir)
bible_dir = os.path.join(base_dir, "bible")
reports_dir = os.path.join(test_dir, "reports")

# Import tests
sys.path.append(script_dir)
import test_structure
import test_verse_format
import test_verse_count
import test_spot_checks
import test_fingerprints

def main():
    os.makedirs(reports_dir, exist_ok=True)
    today_str = datetime.date.today().strftime("%Y-%m-%d")
    report_file = os.path.join(reports_dir, f"report_{today_str}.txt")
    if os.path.exists(report_file):
        suffix = 2
        while True:
            candidate = os.path.join(reports_dir, f"report_{today_str}_v{suffix}.txt")
            if not os.path.exists(candidate):
                report_file = candidate
                break
            suffix += 1
    
    print("--- RUNNING BIBLE VERIFICATION TEST SUITE ---")
    
    results = {}
    
    # 1. Structure Tests
    print("Running Structure Tests...")
    struct_passes, struct_fails, struct_failures = test_structure.run_test(bible_dir)
    results["Structure Validation"] = (struct_passes, struct_fails, 0, struct_failures)
    
    # 2. Verse Format Tests
    print("Running Verse Format Tests...")
    format_passes, format_fails, format_failures = test_verse_format.run_test(bible_dir)
    results["Verse Format Validation"] = (format_passes, format_fails, 0, format_failures)
    
    # 3. Verse Count Tests
    print("Running Verse Count Tests...")
    count_passes, count_fails, count_failures = test_verse_count.run_test(bible_dir)
    results["Verse Count Validation"] = (count_passes, count_fails, 0, count_failures)
    
    # 4. Spot Checks
    print("Running Spot Checks...")
    spot_passes, spot_fails, spot_failures = test_spot_checks.run_test(bible_dir)
    results["Verse Text Spot Checks"] = (spot_passes, spot_fails, 0, spot_failures)
    
    # 5. Fingerprints Check
    print("Running Translation Fingerprint Checks...")
    fp_passes, fp_fails, fp_skips, fp_failures, fp_log = test_fingerprints.run_test(bible_dir, test_dir)
    results["Translation Fingerprint Validation"] = (fp_passes, fp_fails, fp_skips, fp_failures)
    
    # Compile Report
    total_passes = sum(r[0] for r in results.values())
    total_fails = sum(r[1] for r in results.values())
    total_skips = sum(r[2] for r in results.values())
    total_applicable = total_passes + total_fails
    
    report_content = []
    report_content.append("======================================================================")
    report_content.append(f"BIBLE VERIFICATION TEST SUITE REPORT - {today_str}")
    report_content.append("======================================================================\n")
    
    if total_applicable > 0:
        pct_passed = (total_passes / total_applicable) * 100
    else:
        pct_passed = 0.0
        
    report_content.append(f"Passed: {total_passes}")
    report_content.append(f"Skipped: {total_skips}")
    report_content.append(f"Failed: {total_fails}")
    report_content.append(f"Applicable pass rate: {pct_passed:.2f}% ({total_passes} / {total_applicable} assertions)\n")
    
    if total_skips > 0:
        report_content.append(f"Note: {total_skips} fingerprint checks were explicitly skipped due to documented source-corpus versification limitations.\n")
    
    report_content.append("--- SUMMARY BY TEST CATEGORY ---")
    for cat, (p, f, s, _) in sorted(results.items()):
        status = "PASSED" if f == 0 else "FAILED"
        if s > 0:
            report_content.append(f"  {cat:<35}: {status:<8} ({p} passed, {f} failed, {s} skipped)")
        else:
            report_content.append(f"  {cat:<35}: {status:<8} ({p} passed, {f} failed)")
    report_content.append("")
    
    report_content.append("--- DETAILED FINGERPRINT TEST LOG ---")
    for log_line in fp_log:
        report_content.append(f"  {log_line}")
    report_content.append("")
    
    # Group and log all failures
    all_failures = []
    for cat, (_, f_count, _, f_list) in sorted(results.items()):
        if f_count > 0:
            all_failures.append(f"Category: {cat} ({f_count} failures)")
            for fail in f_list:
                all_failures.append(f"  - {fail}")
                
    if all_failures:
        report_content.append("--- ALL FAILURES DETAIL ---")
        report_content.extend(all_failures)
    else:
        report_content.append("--- NO FAILURES ENCOUNTERED ---")
        report_content.append("All structural, format, count, spot, and fingerprint validations passed successfully!")
        
    report_text = "\n".join(report_content)
    
    with open(report_file, "w", encoding="utf-8") as f:
        f.write(report_text)
        
    print(f"\nTests finished. Report saved to: {report_file}")
    print(f"Passed: {total_passes}")
    print(f"Skipped: {total_skips}")
    print(f"Failed: {total_fails}")
    print(f"Applicable pass rate: {pct_passed:.2f}%")
    
    if total_fails > 0:
        print(f"FAILED: Encountered {total_fails} validation failures. See report for details.")
        sys.exit(1)
    else:
        print("SUCCESS: All tests passed!")
        sys.exit(0)

if __name__ == "__main__":
    main()
