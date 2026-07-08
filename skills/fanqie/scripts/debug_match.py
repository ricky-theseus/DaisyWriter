import json, subprocess, sys
if len(sys.argv) < 3:
    print("Usage: python debug_match.py <prepare_script> <chapter_dir> [target_filter]")
    sys.exit(1)
res = subprocess.run(['python', sys.argv[1], '--dir', sys.argv[2]], capture_output=True, text=True)
chapters = json.loads(res.stdout)
target_filter = sys.argv[3] if len(sys.argv) > 3 else ''
print(f"Total chapters: {len(chapters)}")
for c in chapters:
    f = c['file']
    if target_filter in f:
        print(f"  file={repr(f)}")
