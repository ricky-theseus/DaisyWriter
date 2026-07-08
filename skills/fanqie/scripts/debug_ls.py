import os, sys
d = sys.argv[1] if len(sys.argv) > 1 else os.getcwd()
for f in sorted(os.listdir(d)):
    if f.endswith('.md'):
        print(repr(f))
