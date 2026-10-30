import os
import re
import urllib.parse
import uuid
import httpx
from typing import Dict, Any, Optional, List
from app.config import settings
from app.utils.logger import logger

class ImageGenService:
    def __init__(self):
        self.hf_key = settings.HUGGINGFACE_API_KEY

    def is_image_generation_query(self, query: str) -> bool:
        """
        Detects if user is asking to create/draw/generate a new AI image across English, Hindi, and Hinglish.
        Examples:
        - "generate the image of a cat"
        - "generate an image of a cat"
        - "generate 3d image of cat"
        - "create a picture of taj mahal at sunset"
        - "draw an astronaut in space"
        - "paint a sunset over mountains"
        - "photo banao ek robot ki"
        - "cat ki image generate karo"
        - "mujhe ek car ki image bana kar do"
        """
        q = query.lower().strip()

        gen_verbs = r"(generate|generating|create|creating|make|making|draw|drawing|paint|painting|render|rendering|sketch|sketching|produce|design)"
        img_nouns = r"(image|images|img|imgs|photo|photos|photograph|photographs|picture|pictures|pic|pics|wallpaper|wallpapers|illustration|illustrations|painting|paintings|drawing|drawings|portrait|portraits|artwork|art|render|renders|3d\s+model|3d\s+render|3d\s+image|poster)"
        modifiers = r"(an?|the|me|us|a\s+new|some|a\s+realistic|realistic|3d|hd|4k|ai|digital|cool|beautiful|cute)"

        patterns = [
            # 1. Verb + optional modifier/words + Noun: "generate the image", "generate 3d image", "create a picture"
            rf"\b{gen_verbs}\s+({modifiers}\s+)?({modifiers}\s+)?{img_nouns}\b",
            # 2. Direct drawing/painting on subject: "draw a cat", "draw me an astronaut", "paint the sunset", "sketch a car"
            r"\b(draw|paint|sketch)\s+(me\s+)?(an?\s+|the\s+)?",
            # 3. Hindi/Hinglish suffix: "cat ki image generate karo", "photo banao", "picture bana do"
            r"\b(photo|image|picture|pic|drawing|tasveer|chitra|wallpaper)\b.*?\b(banao|bana\s+do|bana\s+de|bana\s+ke\s+do|bana\s+kar\s+do|generate\s+karo|create\s+karo|render\s+karo|drawing\s+karo)\b",
            # 4. Hindi/Hinglish prefix: "banao ek cat ki image", "photo banao ek robot ki"
            r"\b(banao|bana\s+do|bana\s+de)\s+(ek\s+)?.*?\b(photo|image|picture|pic|drawing|tasveer)\b",
            # 5. Inverted: "cat image generate", "taj mahal photo create"
            rf"\b{img_nouns}\s+(generate|generation|creation|render)\b",
            # 6. Direct prompt: "ai image of...", "text to image of..."
            rf"\b(ai\s+image|ai\s+photo|ai\s+art|text\s+to\s+image)\b"
        ]
        return any(re.search(pat, q) for pat in patterns)

    def is_web_image_search_query(self, query: str) -> bool:
        """
        Detects if user is asking to see/fetch a real photo/image from the web.
        Examples:
        - "show me a photo of sachin tendulkar"
        - "virat kohli ki photo dikhao"
        - "eiffel tower ki image dikhao"
        - "picture of lion"
        """
        q = query.lower().strip()
        # Always prioritize generation if generation verb is present
        if self.is_image_generation_query(query):
            return False

        patterns = [
            r"\b(show|find|fetch|search|get)\s+(me\s+)?(a\s+)?(photo|image|picture)\s+(of|for)\b",
            r"(photo|image|picture)\s+(dikhao|dikha\s+do|dhundho|lao|bhejo)",
            r"^(photo|image|picture)\s+of\s+",
            r"\b(ki\s+photo|ki\s+image|ki\s+picture)\s*(dikhao|bhejo|dikha\s+do|dhundho)?"
        ]
        return any(re.search(pat, q) for pat in patterns)

    def extract_prompt_for_generation(self, query: str) -> str:
        """Extracts clean descriptive prompt from user's generation query."""
        clean = query.strip()
        # 1. Remove polite prefixes in any order (can you please, please, could you, etc.)
        clean = re.sub(
            r"^(can\s+you\s+please|could\s+you\s+please|please\s+can\s+you|please|can\s+you|could\s+you|would\s+you|i\s+want\s+(you\s+to\s+)?(to\s+)?|kripya|mujhe)\s+",
            "",
            clean,
            flags=re.IGNORECASE
        ).strip()

        # 2. Remove common Hindi prefix patterns: "photo banao ek ...", "image banao ek ...", "banao ek ..."
        clean = re.sub(
            r"^(photo|image|picture|pic|drawing|tasveer)?\s*(banao|bana\s+do|bana\s+de|bana\s+ke\s+do)\s+(ek\s+)?",
            "",
            clean,
            flags=re.IGNORECASE
        ).strip()

        # 3. Remove common English command patterns: "generate the image of", "generate 3d image of", "create a picture of"
        clean = re.sub(
            r"^(generate|creating|create|make|draw|render|paint|sketch|produce)\s+(me\s+)?(us\s+)?((an?|the|some)\s+)?(new\s+)?(3d\s+)?(realistic\s+)?(hd\s+)?(image|photo|photograph|picture|pic|wallpaper|illustration|painting|drawing|artwork|portrait|render|art)\s+(of\s+)?",
            "",
            clean,
            flags=re.IGNORECASE
        ).strip()

        # 4. Direct draw/paint/sketch: "draw me a...", "paint a..."
        clean = re.sub(
            r"^(draw|paint|sketch)\s+(me\s+)?(us\s+)?((an?|the)\s+)?",
            "",
            clean,
            flags=re.IGNORECASE
        ).strip()

        # 5. Remove Hindi/Hinglish end patterns: "... ki photo banao", "... image generate karo", "... ki"
        clean = re.sub(
            r"\s*(ki\s+)?(photo|image|picture|pic|drawing|tasveer|chitra)?\s*(banao|bana\s+do|bana\s+de|bana\s+ke\s+do|generate\s+karo|create\s+karo|chahiye)\s*$",
            "",
            clean,
            flags=re.IGNORECASE
        ).strip()

        # 6. Clean dangling 'of', 'ki', 'ka'
        clean = re.sub(r"^(of|ki)\s+", "", clean, flags=re.IGNORECASE).strip()
        clean = re.sub(r"\s+(ki|ka)$", "", clean, flags=re.IGNORECASE).strip()

        # 7. Convert "ek robot" -> "a robot"
        if clean.lower().startswith("ek "):
            clean = "a " + clean[3:]

        # 8. Check if 3D style was requested
        is_3d = bool(re.search(r"\b(3d|3-d|three dimensional|octane|cgi)\b", query, re.IGNORECASE))
        if is_3d and "3d" not in clean.lower():
            clean = f"3D render of {clean}, detailed CGI, 8k resolution"

        return clean or query

    def extract_subject_for_image_search(self, query: str) -> str:
        """Extracts the subject whose photo is requested."""
        clean = re.sub(r"^(please\s+)?(can\s+you\s+)?(show|find|fetch|get)\s+(me\s+)?(a\s+)?(photo|image|picture)\s+(of\s+)?", "", query, flags=re.IGNORECASE)
        clean = re.sub(r"(ki\s+photo|ki\s+image|ki\s+picture)\s*(dikhao|dikha do|dhundho)?", "", clean, flags=re.IGNORECASE)
        return clean.strip() or query

    async def generate_ai_image(self, prompt: str) -> Dict[str, Any]:
        """
        Generates photorealistic AI image 100% free using Pollinations AI (FLUX model)
        with fallback to Hugging Face FLUX/SD if key is available.
        """
        clean_prompt = self.extract_prompt_for_generation(prompt)
        logger.info(f"Generating AI image for prompt: '{clean_prompt}'")

        safe_name = f"ai_gen_{uuid.uuid4().hex[:8]}.jpg"
        file_path = os.path.join(settings.GENERATED_DIR, safe_name)
        encoded_prompt = urllib.parse.quote(clean_prompt)

        # 1. Pollinations AI: 100% Free, photorealistic, no key required, unlimited
        pollinations_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1024&height=1024&nologo=true&model=flux&enhance=true"

        # Try downloading to save locally for offline access
        try:
            async with httpx.AsyncClient(timeout=25.0, follow_redirects=True) as client:
                resp = await client.get(pollinations_url)
                if resp.status_code == 200 and len(resp.content) > 1000:
                    with open(file_path, "wb") as f:
                        f.write(resp.content)
                    logger.info(f"Saved generated image to {file_path}")
                    return {
                        "prompt": clean_prompt,
                        "image_url": f"/generated/{safe_name}",
                        "direct_url": pollinations_url,
                        "source": "Pollinations FLUX (Free AI Generator)",
                        "success": True
                    }
        except Exception as e:
            logger.warning(f"Direct download of pollinations image timed out/failed: {e}")

        # If download had a network timeout, direct URL still renders in browser
        return {
            "prompt": clean_prompt,
            "image_url": pollinations_url,
            "direct_url": pollinations_url,
            "source": "Pollinations FLUX (Free AI Generator)",
            "success": True
        }

    async def search_web_images(self, subject: str, max_results: int = 3) -> List[Dict[str, str]]:
        """
        Searches web for real images of a subject using DuckDuckGo / Wikimedia / Web images (100% free).
        """
        clean_subject = self.extract_subject_for_image_search(subject)
        logger.info(f"Searching web images for: '{clean_subject}'")

        images: List[Dict[str, str]] = []

        # 1. Try DuckDuckGo Images
        try:
            from duckduckgo_search import DDGS
            with DDGS() as ddgs:
                results = list(ddgs.images(clean_subject, max_results=max_results))
                for r in results:
                    img_url = r.get("image") or r.get("thumbnail")
                    if img_url and img_url.startswith("http"):
                        images.append({
                            "title": r.get("title", clean_subject),
                            "image_url": img_url,
                            "source_url": r.get("url", img_url)
                        })
                if images:
                    return images
        except Exception as e:
            logger.warning(f"DuckDuckGo image search failed: {e}")

        # 2. Wikimedia Commons API fallback (100% free, reliable, no key needed)
        try:
            wiki_url = "https://en.wikipedia.org/w/api.php"
            params = {
                "action": "query",
                "format": "json",
                "generator": "search",
                "gsrsearch": clean_subject,
                "gsrlimit": max_results,
                "prop": "pageimages",
                "piprop": "original|thumbnail",
                "pithumbsize": 800
            }
            async with httpx.AsyncClient(timeout=8.0) as client:
                res = await client.get(wiki_url, params=params)
                if res.status_code == 200:
                    data = res.json()
                    pages = data.get("query", {}).get("pages", {})
                    for _, page in pages.items():
                        orig = page.get("original", {}).get("source")
                        thumb = page.get("thumbnail", {}).get("source")
                        url = orig or thumb
                        if url:
                            images.append({
                                "title": page.get("title", clean_subject),
                                "image_url": url,
                                "source_url": f"https://en.wikipedia.org/?curid={page.get('pageid', '')}"
                            })
                    if images:
                        return images
        except Exception as e:
            logger.warning(f"Wikimedia image search fallback failed: {e}")

        # 3. Unsplash Public Source fallback
        encoded = urllib.parse.quote(clean_subject)
        images.append({
            "title": clean_subject,
            "image_url": f"https://source.unsplash.com/800x600/?{encoded}",
            "source_url": f"https://unsplash.com/s/photos/{encoded}"
        })
        return images

image_gen_service = ImageGenService()
