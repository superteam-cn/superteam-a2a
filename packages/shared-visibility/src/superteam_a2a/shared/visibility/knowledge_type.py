"""KnowledgeType re-export · L3-5 §3.2 + L3-6 §3 shared definition.

Single source of truth lives in ``superteam_a2a.knowledge.crd.knowledgeitem``;
this module exists so consumers can depend solely on the shared-visibility
package without importing the knowledge CRD layer.
"""

from superteam_a2a.knowledge.crd.knowledgeitem import KnowledgeType

__all__ = ["KnowledgeType"]
