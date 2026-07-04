import json, subprocess, sys
res = subprocess.run(['python', r'D:\Writer\.opencode\skills\fanqie-publisher\scripts\prepare_chapters.py', '--dir', r'D:\Writer\未命名者\正文'], capture_output=True, text=True)
chapters = json.loads(res.stdout)
target = r'D:\Writer\未命名者\正文\第0006章-我知道.md'
print(f"Total chapters: {len(chapters)}")
print(f"Target: {target}")
for c in chapters:
    f = c['file']
    if '0006' in f:
        print(f"  file={repr(f)}")
        print(f"  matches target: {f == target}")
