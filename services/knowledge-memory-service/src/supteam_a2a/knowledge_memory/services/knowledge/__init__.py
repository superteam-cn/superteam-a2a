"""Knowledge 業務邏輯 service 層 · 4 文件（Protocol stub · BM25 實裝推 PR-4c）。

依據 PR-4b plan §1 明確剔除：
- ❌ BM25 倒排索引業務邏輯（text 索引 + tokenization + TF-IDF 評分）→ PR-4c
- ❌ 4 級 scope resolver 業務邏輯（parent_ref 解析 + chain 遍歷）→ PR-4c
- ❌ visibility resolver 業務邏輯（5 維矩陣策略執行）→ PR-4c

Knowledge service 採用 Protocol + stub 模式：
- query · KnowledgeQueryService · 返回空列表
- item · KnowledgeItemService · 返回 None（superseded_by chain 推 PR-4c）
- record · KnowledgeItemRecordService · 派 KnowledgeItem 推 PR-4c
- scope · KnowledgeScopeService · 復用 PR-4a VisibilityScopeValidator 做基礎校驗

ISP：Protocol 接口最小化（execute / get_item / validate_scope / derive_from_memory）。
"""
