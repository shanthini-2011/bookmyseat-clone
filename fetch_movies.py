import urllib.request
import urllib.error
import re

try:
    req = urllib.request.Request('http://127.0.0.1:8000/movies/')
    urllib.request.urlopen(req)
except urllib.error.HTTPError as e:
    html = e.read().decode('utf-8')
    match = re.search(r'<title>(.*?)</title>', html, re.DOTALL)
    if match:
        print("TITLE:", match.group(1).strip())
    
    # Try to extract the exception value
    match2 = re.search(r'<pre class="exception_value">(.*?)</pre>', html, re.DOTALL)
    if match2:
        print("EXCEPTION:", match2.group(1).strip())
        
    # Get the traceback frames
    print("Traceback snippets:")
    for m in re.finditer(r'<span class="code">(.*?)</span>', html, re.DOTALL):
        if 'raise' in m.group(1) or 'return' in m.group(1) or '=' in m.group(1):
            print(m.group(1).strip().replace('\n', ' '))
