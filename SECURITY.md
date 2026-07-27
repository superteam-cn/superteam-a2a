# Security Policy

## Reporting a Vulnerability

> ⚠️ **Please do not file public GitHub issues for security vulnerabilities.**

If you discover a security issue in `superteam-a2a`, please email:

**`security@CoderZhangfujiang.dev`** *(placeholder — will be replaced with a real inbox before v0.1 ships)*

Include in your report:
- Description of the vulnerability
- Steps to reproduce or proof-of-concept
- Impact assessment (which component, what an attacker can achieve)
- Your handle / contact for follow-up

We aim to:
- Acknowledge within **3 business days**
- Provide a triage assessment within **10 business days**
- Coordinate disclosure timing with you

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| latest (main) | ✅ actively |
| previous minor | ⚠️ best-effort |
| anything older | ❌ no longer supported |

## Out of Scope

The following are not considered vulnerabilities in `superteam-a2a`:

- Denial-of-service caused by misconfigured `Agent` resources (mitigated via K8s `ResourceQuota`)
- Sensitive data logged by an agent's underlying LLM framework (out of our scope; report upstream)
- Vulnerabilities in agent framework dependencies (LangChain, AutoGen, CrewAI, etc.) — report upstream

## Hall of Fame (planned)

We will publish a thank-you list of reporters (with permission) once v0.1 ships.
