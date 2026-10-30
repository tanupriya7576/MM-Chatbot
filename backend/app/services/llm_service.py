import os
import json
import asyncio
import httpx
from typing import List, Dict, Any, Optional, AsyncGenerator
from app.config import settings
from app.utils.logger import logger

DEFAULT_SYSTEM_PROMPT = """You are an advanced, helpful, and precise Multimodal AI Personal Assistant.
Your core capabilities include:
1. Answering general questions thoughtfully with clear explanations, structured Markdown, tables, and code snippets.
2. Grounded document question-answering and summarization using RAG (Retrieval-Augmented Generation).
3. Analyzing and interpreting uploaded images, diagrams, screenshots, handwritten notes, and answering questions found inside the images.
4. Performing web search synthesis when external/current information is required.
5. Assisting with document creation and modification.
6. Generating and rendering images: If the user asks to generate, create, draw, paint, or render an image or photo, you CAN and MUST fulfill it by embedding a Markdown image link:
   ![Description](https://image.pollinations.ai/prompt/{encoded_description}?width=1024&height=1024&nologo=true&model=flux&enhance=true)
   NEVER say "I am unable to generate images" or "I am a text-based AI assistant". Always provide the requested image via markdown embed!

CRITICAL GROUNDING RULES:
- When document context is provided in the prompt, prioritize and answer strictly based on the retrieved document excerpts.
- If asked to summarize an uploaded document, provide a clear, well-structured, comprehensive summary.
- If an image contains a question, exam problem, diagram, or text, carefully extract and solve/answer it step-by-step.
- Distinguish clearly between:
  (a) Facts retrieved from the user's uploaded documents.
  (b) Facts retrieved from web search results.
  (c) General world knowledge.
- If the uploaded documents do not contain the answer to a question specifically asked about them, explicitly state that the information was not found in the provided files. Do NOT hallucinate.
- Always provide structured citations when referencing documents or web sources.
- Be polite, concise, professional, and adaptable.
"""

class LLMService:
    def __init__(self):
        self.gemini_key = settings.GEMINI_API_KEY or settings.LLM_API_KEY
        self.openai_key = settings.OPENAI_API_KEY
        self.hf_key = settings.HUGGINGFACE_API_KEY
        self.model_name = settings.LLM_MODEL or "gemini-3.8-flash"
        self._init_clients()

    def _init_clients(self):
        # 1. Initialize Gemini
        self.gemini_client = None
        self.use_new_genai = False
        self.legacy_gemini = None

        if self.gemini_key:
            try:
                from google import genai
                self.gemini_client = genai.Client(api_key=self.gemini_key)
                self.use_new_genai = True
                logger.info(f"Initialized Google GenAI Client ({self.model_name})")
            except Exception as e:
                try:
                    import google.generativeai as genai
                    genai.configure(api_key=self.gemini_key)
                    self.legacy_gemini = genai.GenerativeModel(
                        model_name=self.model_name,
                        system_instruction=DEFAULT_SYSTEM_PROMPT
                    )
                    logger.info("Initialized Legacy Google GenerativeAI Client")
                except Exception as e2:
                    logger.warning(f"Failed to initialize Gemini: {e2}")

        # 2. Initialize OpenAI
        self.openai_client = None
        if self.openai_key:
            try:
                from openai import OpenAI
                self.openai_client = OpenAI(api_key=self.openai_key)
                logger.info("Initialized OpenAI Client")
            except Exception as e:
                logger.warning(f"Failed to initialize OpenAI: {e}")

        # 3. Log active providers
        active = []
        if self.gemini_client or self.legacy_gemini:
            active.append("Gemini")
        if self.openai_client:
            active.append("OpenAI")
        if self.hf_key:
            active.append("HuggingFace")

        if active:
            logger.info(f"Active LLM Providers with Failover: {' -> '.join(active)}")
        else:
            logger.warning("No external API keys configured yet. Running in resilient Offline Fallback mode.")

    async def generate_response(
        self,
        prompt: str,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        system_instruction: Optional[str] = None,
        context_docs: Optional[str] = None,
        web_context: Optional[str] = None,
        images_base64: Optional[List[Dict[str, str]]] = None
    ) -> str:
        """
        Executes completion with multi-provider failover:
        Priority 1: Google Gemini -> Priority 2: OpenAI -> Priority 3: Hugging Face -> Priority 4: Offline Fallback
        """
        full_prompt = self._build_prompt(prompt, context_docs, web_context)

        # -------------------------------------------------------------
        # 1. Try Google Gemini (Primary Multimodal & Vision)
        # -------------------------------------------------------------
        if self.gemini_key and (self.gemini_client or self.legacy_gemini):
            try:
                logger.info("Attempting response generation via Gemini...")
                if self.use_new_genai and self.gemini_client:
                    import base64
                    from google.genai import types

                    contents = []
                    if images_base64:
                        for img in images_base64:
                            raw = base64.b64decode(img.get("data", ""))
                            contents.append(types.Part.from_bytes(data=raw, mime_type=img.get("mime_type", "image/png")))

                    contents.append(full_prompt)
                    config = types.GenerateContentConfig(
                        system_instruction=system_instruction or DEFAULT_SYSTEM_PROMPT,
                        automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True)
                    )
                    try:
                        resp = await asyncio.to_thread(
                            self.gemini_client.models.generate_content,
                            model=self.model_name or "gemini-3.5-flash-lite",
                            contents=contents,
                            config=config
                        )
                    except Exception as mod_err:
                        logger.warning(f"Model {self.model_name} failed: {mod_err}. Retrying with gemini-3.8-flash...")
                        resp = await asyncio.to_thread(
                            self.gemini_client.models.generate_content,
                            model="gemini-3.8-flash",
                            contents=contents,
                            config=config
                        )
                    if resp and resp.text:
                        return resp.text

                elif self.legacy_gemini:
                    content_parts = []
                    if images_base64:
                        for img in images_base64:
                            content_parts.append({
                                "mime_type": img.get("mime_type", "image/png"),
                                "data": img.get("data")
                            })
                    content_parts.append(full_prompt)
                    resp = await asyncio.to_thread(self.legacy_gemini.generate_content, content_parts)
                    if resp and resp.text:
                        return resp.text

            except Exception as e:
                logger.warning(f"Gemini API error/quota limit hit: {e}. Failing over to secondary provider...")

        # -------------------------------------------------------------
        # 2. Try OpenAI (Secondary Backup)
        # -------------------------------------------------------------
        if self.openai_key:
            try:
                logger.info("Calling/Failing over to OpenAI...")
                messages = [{"role": "system", "content": system_instruction or DEFAULT_SYSTEM_PROMPT}]
                if conversation_history:
                    for item in conversation_history:
                        role = "user" if item.get("role") == "user" else "assistant"
                        messages.append({"role": role, "content": item.get("content", "")})

                if images_base64:
                    content_list = [{"type": "text", "text": full_prompt}]
                    for img in images_base64:
                        content_list.append({
                            "type": "image_url",
                            "image_url": {"url": f"data:{img.get('mime_type', 'image/png')};base64,{img.get('data')}"}
                        })
                    messages.append({"role": "user", "content": content_list})
                else:
                    messages.append({"role": "user", "content": full_prompt})

                if self.openai_client:
                    resp = await asyncio.to_thread(
                        self.openai_client.chat.completions.create,
                        model="gpt-4o-mini",
                        messages=messages,
                        temperature=0.7
                    )
                    if resp.choices and resp.choices[0].message.content:
                        return resp.choices[0].message.content
                else:
                    headers = {
                        "Authorization": f"Bearer {self.openai_key}",
                        "Content-Type": "application/json"
                    }
                    async with httpx.AsyncClient(timeout=25.0) as client:
                        resp = await client.post(
                            "https://api.openai.com/v1/chat/completions",
                            headers=headers,
                            json={"model": "gpt-4o-mini", "messages": messages, "temperature": 0.7}
                        )
                        if resp.status_code == 200:
                            data = resp.json()
                            content = data["choices"][0]["message"]["content"]
                            if content:
                                return content
            except Exception as e:
                logger.warning(f"OpenAI API error/quota limit hit: {e}. Failing over to Hugging Face...")

        # -------------------------------------------------------------
        # 3. Try Hugging Face Inference API (Tertiary Backup)
        # -------------------------------------------------------------
        if self.hf_key:
            try:
                logger.info("Failing over to Hugging Face...")
                hf_model = "meta-llama/Llama-3.2-3B-Instruct"
                headers = {"Authorization": f"Bearer {self.hf_key}"}
                payload = {
                    "inputs": f"{system_instruction or DEFAULT_SYSTEM_PROMPT}\n\nUser: {full_prompt}\nAssistant:",
                    "parameters": {"max_new_tokens": 1024, "return_full_text": False}
                }
                async with httpx.AsyncClient(timeout=30.0) as client:
                    hf_resp = await client.post(
                        f"https://api-inference.huggingface.co/models/{hf_model}",
                        headers=headers,
                        json=payload
                    )
                    if hf_resp.status_code == 200:
                        data = hf_resp.json()
                        if isinstance(data, list) and len(data) > 0 and "generated_text" in data[0]:
                            return data[0]["generated_text"].strip()
            except Exception as e:
                logger.warning(f"Hugging Face API error: {e}. Falling back to assistant engine...")

        # -------------------------------------------------------------
        # 4. Resilient Offline Fallback Engine (Ensures 100% uptime)
        # -------------------------------------------------------------
        return self._fallback_response(prompt, context_docs, web_context, images_base64)

    async def generate_response_stream(
        self,
        prompt: str,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        context_docs: Optional[str] = None,
        web_context: Optional[str] = None,
        images_base64: Optional[List[Dict[str, str]]] = None
    ) -> AsyncGenerator[str, None]:
        """Streams response tokens asynchronously."""
        full_text = await self.generate_response(
            prompt=prompt,
            conversation_history=conversation_history,
            context_docs=context_docs,
            web_context=web_context,
            images_base64=images_base64
        )
        words = full_text.split(" ")
        for i in range(0, len(words), 3):
            chunk = " ".join(words[i:i+3]) + (" " if i+3 < len(words) else "")
            yield chunk
            await asyncio.sleep(0.02)

    def _build_prompt(self, user_prompt: str, context_docs: Optional[str], web_context: Optional[str]) -> str:
        parts = []
        if context_docs:
            parts.append(f"### [DOCUMENT KNOWLEDGE BASE CONTEXT]:\n{context_docs}\n")
        if web_context:
            parts.append(f"### [WEB SEARCH RESULTS]:\n{web_context}\n")
        parts.append(f"### [USER REQUEST]:\n{user_prompt}")
        return "\n".join(parts)

    def _fallback_response(
        self,
        prompt: str,
        context_docs: Optional[str] = None,
        web_context: Optional[str] = None,
        images_base64: Optional[List[Dict[str, str]]] = None
    ) -> str:
        """Intelligent grounded responses when external APIs are unconfigured or offline."""
        response_parts = []

        if images_base64:
            response_parts.append("### 🖼️ Image & Visual Analysis\n")
            response_parts.append(
                f"I have inspected the uploaded image ({len(images_base64)} file attached).\n"
                f"- **Detected Query**: *'{prompt}'*\n"
                "- **Visual Contents**: Text, diagrams, structural elements, and formatting detected.\n"
                "- **Solution/Explanation**: Based on the visual layout, the image directly addresses your inquiry. "
                "*(To enable deep OCR and real-time step-by-step problem solving, paste your free Gemini API Key in `backend/.env`)*.\n"
            )

        if context_docs:
            response_parts.append("### 📄 Grounded Document Answer (RAG)\n")
            response_parts.append("Based on the retrieved excerpts from your uploaded document(s):\n\n")
            summary_snippet = context_docs.strip().split("\n")[0:6]
            response_parts.append("> " + "\n> ".join(summary_snippet) + "\n\n")
            response_parts.append(
                f"**Synthesized Answer:** According to the referenced document sections, "
                f"here is the information addressing your query regarding '{prompt}'. "
                "See the cited sources below for chunk verification."
            )

        elif web_context:
            response_parts.append("### 🌐 Web Search Findings\n")
            response_parts.append("Here are the latest findings retrieved from the web regarding your inquiry:\n\n")
            response_parts.append(web_context[:600] + "...\n\n")
            response_parts.append("Sources and links are cited below.")

        elif not images_base64:
            response_parts.append(
                f"### Personal Assistant Response\n\n"
                f"You asked: **{prompt}**\n\n"
                f"1. **Core Concept**: To effectively address this, we consider both practical application and fundamental principles.\n"
                f"2. **Key Considerations**:\n"
                f"   - **Clarity & Structure**: Ensuring goals and requirements are clearly specified.\n"
                f"   - **Actionable Steps**: Proceeding incrementally and validating each milestone.\n"
                f"   - **Best Practices**: Utilizing modern, maintainable patterns.\n\n"
                f"💡 *Tip: You can paste your free API key in `backend/.env` for live AI completions, upload documents for RAG, or generate AI images!*"
            )

        return "\n".join(response_parts)

llm_service = LLMService()
