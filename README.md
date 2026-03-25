# Overview

This repo contains the payloads recovered from the litellm 1.82.7 compromised package. The malicious code was injected inside `litellm/proxy/proxy_server.py` file starting from line 129 to line 140. During analysis, I found multiple base64 payload variants embedded in the script. However only first one gets executed, which is similar to the payload found in the litellm 1.82.8 compromised package. 

Since both 1.82.7 and 1.82.8 versions share same infrastructure, check out [litellm 1.82.8 payload](https://github.com/HackingLZ/litellm_1.82.8_payload) analysis by HackingLZ for a detailed overview.

Here I mainly focused on the different base64 payloads observed in the sample.

Original Sample : [litellm-1.82.7.tar.gz - malwarebazaar](https://bazaar.abuse.ch/sample/8a2a05fd8bdc329c8a86d2d08229d167500c01ecad06e40477c49fb0096efdea/)

## What Was Modified

The original file of interest is `proxy_server.py`.

The legitimate LiteLLM proxy code is present, but a malicious block was inserted immediately after `REALTIME_REQUEST_SCOPE_TEMPLATE`. That injected block:

- imports `subprocess`, `base64`, `sys`, `tempfile`, and `os`
- defines one active outer payload as `b64_payload`
- keeps two additional outer payloads as commented alternates on the following lines
- writes the decoded active payload to a temporary `p.py`
- launches it with `subprocess.run([sys.executable, p])`

In the sample as written, only the first outer payload is executed. The second and third outer payloads are preserved in comments and appear to be alternate operator variants.

## End-to-End Flow

The infection chain works as a staged loader:

1. `proxy_server.py`
   The injected code decodes the active base64 blob and runs it as a temporary Python file.

2. `exfil_variant*.py`
   This is the first decoded stage. It is the exfiltration wrapper.
   It contains an embedded RSA public key and another embedded collector payload.
   Depending on the variant, it either:
   - runs the collector through `subprocess` and captures stdout, or
   - `exec()`s the collector while redirecting stdout to `StringIO`
   Finally exfiltrates data to `models[.]litellm[.]cloud` C2 over curl.

3. `collector_*.py`
   This is the main theft / collection stage.
   It gathers credentials, secrets, tokens, keys, environment files, cloud metadata, Kubernetes material, wallet files, and system logs.
   It also contains the embedded persistence payload.

4. `persistence_variant*.py`
   This is the long-lived downloader / persistence stage.
   It polls a remote URL (`hxxps[:]//checkmarx[.]zone/raw`), downloads a follow-on payload to `/tmp/pglog`, tracks state in `/tmp/.pg_state`, and executes the fetched file.

## Variant Mapping

### Variant 1

This is the only branch that executes in the sample as written.

- Initial trigger: active `b64_payload` in `proxy_server.py`
- Stage 1: `exfil_variant1.py`
- Stage 2: `collector_vatiant1.py`
- Stage 3: `persistence_variant1.py`

### Variant 2

This is a commented alternate outer payload preserved in `proxy_server.py`.

- Initial trigger: commented alternate base64 blob
- Stage 1: `exfil_variant2.py`
- Stage 2: `collector_variant2.py`
- Alternate commented collector form: `collector_variant2-commented.py`
- Stage 3: `persistence_variant2.py`

Operationally, this branch is in the same family as Variant 1. The collector logic is effectively the same collection and persistence chain, but the wrapper structure differs. In this version, the wrapper captures collector output through `StringIO` and writes `collected_vars.txt` before packaging and exfiltration.

### Variant 3

This is the second commented alternate outer payload preserved in `proxy_server.py`.

- Initial trigger: commented alternate base64 blob
- Stage 1: `exfil_variant3.py`
- Stage 2: `collector_variant3.py`
- Stage 3: `persistence_variant3.py`

This branch is the more distinct alternate family. The collector uses RC4-obfuscated strings internally, but the overall mission is the same: collect secrets, exfiltrate them, and establish persistence.

## IOCs :-

- `proxy_server.py`
  * MD5 : f5560871f6002982a6a2cc0b3ee739f7 
  * SHA256 : a0d229be8efcb2f9135e2ad55ba275b76ddcfeb55fa4370e0a522a5bdee0120b
- `models[.]litellm[.]cloud`
- `checkmarx[.]zone`

## Files

- `proxy_server.py`
  The infected original file with the malicious injection.
- `exfil_variant1.py`
  Active outer stage decoded from the live branch.
- `exfil_variant2.py`
  Alternate outer wrapper from the first commented branch.
- `exfil_variant3.py`
  Alternate outer wrapper from the second commented branch.
- `collector_vatiant1.py`
  Collector for the active branch.
- `collector_variant2.py`
  Collector associated with Variant 2.
- `collector_variant2-commented.py`
  Commented collector form preserved from the variant chain.
- `collector_variant3.py`
  Distinct RC4-obfuscated collector branch.
- `persistence_variant1.py`
  Persistence stage recovered from Variant 1.
- `persistence_variant2.py`
  Persistence stage recovered from Variant 2.
- `persistence_variant3.py`
  Persistence stage recovered from Variant 3.

## References

[[Security]: litellm PyPI package (v1.82.7 + v1.82.8) compromised — full timeline and status](https://github.com/BerriAI/litellm/issues/24518)
