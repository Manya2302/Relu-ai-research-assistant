# AI Company Research Implementation

The AI Company Research pipeline (`backend/app/services/openrouter_service.py` & `research_orchestrator.py`) transforms raw, unstructured web data into verified, highly-structured business intelligence using Large Language Models via OpenRouter/Groq.

## Architecture & Flow

1. **Context Aggregation (RAG-lite)**
   Traditional systems query an LLM and hope it "remembers" facts from its training data. This leads to hallucinations. 
   Instead, Relu AI acts as a Retrieval-Augmented Generation (RAG) system (without the database). It takes the cleaned text from the `WebsiteCrawler` and combines it with real-time snippets from Google (via Serper). This creates a massive, factual "Context Window" containing the company's *current* state.

2. **System Prompting & Constraints**
   The Context Window is sent to the LLM (e.g., Llama 3, Claude, GPT-4) along with a highly rigorous System Prompt (`app/config.py`). 
   - The prompt strictly forbids the AI from confusing Market Cap, Revenue, and Funding.
   - It requires explicit extraction of Founders for subsidiaries (preventing parent-company founder hallucinations).
   - It commands the AI to output the data strictly as a JSON object matching a predefined Pydantic schema.

3. **Data Parsing & Fallbacks**
   When the LLM returns the JSON, the `GroqService` parses it. If the AI was unable to find specific fields (like Address or Phone Number) because they were missing from the website, the `ResearchOrchestrator` triggers Regex-based fallback extractors.
   - For example, if the AI fails to find an address, `_first_address_value()` scans the raw web snippets for combinations of digits and keywords like "Headquarters" or "Street", explicitly filtering out false positives (like URLs or login portal text).

4. **Dynamic AI Recommendations**
   Rather than just extracting data, the AI acts as an analyst. Using the inferred industry and pain points, it generates 3-5 highly specific, actionable recommendations (e.g., "Track EV engineering contracts" for a specialized IT service firm) and injects them into the final report.
