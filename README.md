# cmpdi.ai
CMPDI.AI is an futuristic application  which will act like a domain specific intelligent enterprise search engine and document assistant for CMPDI and CIL Subsidiaries in offline . It is designed to reduce the burden of searching crucial geological, mining and enterprise documents.
 Key Features & Impact
Lightning-Fast Search: Reduces manual reporting efforts by 95% and transforms multi-day cross-referencing into sub-second retrieval[cite: 7].
Layout-Aware MultiModal RAG: Uses `ColQwen2-v0.1` to preserve table structures, map coordinates, and visual layouts instead of standard OCR[cite: 7].
Autonomous 2-Agent Debate Loop: Agent 1 (Extractor) parses candidate facts into structured JSON, while Agent 2 (Verifier) cross-checks figures against original document pixels to ensure zero hallucinations[cite: 5, 7].
Secure Offline Capability: Fully functional offline on dual NVIDIA T4 GPUs, securing classified mining records in remote field sites without internet connectivity[cite: 5, 7].
Socially Transformative (ISL Support): Integrates Indian Sign Language animations to make mining data accessible to over 1.8 crore hearing-impaired individuals[cite: 7].
 Technical Approach & Stack

Frontend: Streamlit (for a fast, interactive user interface)[cite: 8]
Backend: FastAPI (handling backend orchestration and module integration)[cite: 8]
Core AI/ML Engine: 
  MultiModal RAG with `ColQwen2-v0.1` (Multi-vector LLM)[cite: 8]
   PyTorch & Transformers[cite: 8]
Geospatial & Mapping:** Folium, GeoJson, Matplotlib[cite: 8]
Data Sources & Datasets:** Government official PDFs, Kaggle mining datasets, ISL datasets[cite: 8]
   Implementation Flow

1. Document Preprocessing: Raw PDF pages, CSV tables, and Excel sheets are ingested and converted into layout-aware visual embeddings using ColQwen2[cite: 8].
2. Visual Retrieval: User queries trigger similarity scoring to retrieve top-relevant document pages instantly[cite: 8].
3. Multi-Agent Verification: Retrieved pages pass through the Agent 1 (Extractor) and Agent 2 (Verifier) debate loop to guarantee audit-ready data consistency[cite: 7, 8].
4. Structured Delivery:Final outputs are rendered in clean JSON format, accompanied by visual map spotlights, official PDF download options, and ISL translations[cite: 7, 8].
5. ## 📈 Implementation Flow

1. **Document Preprocessing:** Raw PDF pages, CSV tables, and Excel sheets are ingested and converted into layout-aware visual embeddings using ColQwen2[cite: 8].
2. **Visual Retrieval:** User queries trigger similarity scoring to retrieve top-relevant document pages instantly[cite: 8].
3. **Multi-Agent Verification:** Retrieved pages pass through the Agent 1 (Extractor) and Agent 2 (Verifier) debate loop to guarantee audit-ready data consistency[cite: 7, 8].
4. **Structured Delivery:** Final outputs are rendered in clean JSON format, accompanied by visual map spotlights, official PDF download options, and ISL translations[cite: 7, 8].<img width="1463" height="1075" alt="ChatGPT Image Sep 30, 2026, 09_22_20 PM" src="https://github.com/user-attachments/assets/7b096b46-be44-4f0f-8260-6540fee4cf31" />
