# superteam-a2a-operator

> Kubernetes Operator for superteam-a2a · Python 3.12+ · Kopf handlers

Manages 4 CRDs (v1alpha1): Agent / AgentSet / Workflow / Memory.

依据 L3-1 Spec v0.2.0 + L1 §2-§4。
L4 Step 1 落地：Memory CRD Pydantic v2 schema（其余 3 CRD 待 #75+）。