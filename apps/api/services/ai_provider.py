"""
AI provider abstraction layer.
Supports OpenAI with graceful fallback to dev mode.
"""
import os
from typing import List, Dict, Optional
from dotenv import load_dotenv

load_dotenv()


class AIProvider:
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY", "")
        self.dev_mode = os.getenv("DEV_MODE", "true").lower() == "true"
        self.client = None

        if self.api_key and not self.dev_mode:
            try:
                from openai import OpenAI
                self.client = OpenAI(api_key=self.api_key)
                print("✓ OpenAI client initialized")
            except Exception as e:
                print(f"⚠ OpenAI initialization failed: {e}. Running in DEV MODE.")
                self.dev_mode = True
        else:
            print("ℹ Running in DEV MODE (no OpenAI API key)")

    def generate_embedding(self, text: str) -> Optional[List[float]]:
        """Generate embedding for text. Returns None in dev mode."""
        if self.dev_mode or not self.client:
            return None

        try:
            response = self.client.embeddings.create(
                model="text-embedding-3-small",
                input=text
            )
            return response.data[0].embedding
        except Exception as e:
            print(f"Error generating embedding: {e}")
            return None

    def generate_chat_response(
        self,
        messages: List[Dict[str, str]],
        context_chunks: List[Dict],
        system_prompt: str,
        model: str = "gpt-4-turbo-preview",
        temperature: float = 0.7,
        max_tokens: int = 1000
    ) -> str:
        """Generate chat response with RAG context."""
        if self.dev_mode or not self.client:
            return self._dev_mode_response(messages, context_chunks)

        try:
            # Build context from chunks
            context_text = "\n\n".join([
                f"[{chunk.get('title', 'Unknown')}]\n{chunk.get('content', '')}"
                for chunk in context_chunks
            ])

            # Build messages with context
            augmented_messages = [
                {"role": "system", "content": system_prompt}
            ]

            if context_text:
                augmented_messages.append({
                    "role": "system",
                    "content": f"KNOWLEDGE BASE CONTEXT:\n\n{context_text}"
                })

            augmented_messages.extend(messages)

            response = self.client.chat.completions.create(
                model=model,
                messages=augmented_messages,
                temperature=temperature,
                max_tokens=max_tokens
            )

            return response.choices[0].message.content

        except Exception as e:
            print(f"Error generating chat response: {e}")
            return self._dev_mode_response(messages, context_chunks)

    def _dev_mode_response(self, messages: List[Dict[str, str]], context_chunks: List[Dict]) -> str:
        """Generate deterministic dev mode response."""
        user_message = messages[-1]["content"].lower() if messages else ""

        # Build citations from context
        citations = []
        if context_chunks:
            citations = [f"- {chunk.get('title', 'Document')} ({chunk.get('published_date', 'N/A')})"
                        for chunk in context_chunks[:2]]

        citation_text = "\n".join(citations) if citations else ""

        # Topic-based responses - Keep them short and concise
        if "roth" in user_message or "conversion" in user_message:
            response = """A Roth conversion moves money from a traditional IRA to a Roth IRA. You pay taxes now, but get tax-free growth and withdrawals later. It often makes sense if you expect higher taxes in retirement or want to avoid RMDs.

Want me to explain tax strategies, timing considerations, or walk through an example?"""

        elif "social security" in user_message or "timing" in user_message:
            response = """You can claim Social Security between ages 62-70. Claiming at 62 gets you reduced benefits but more years of payments. Waiting until 70 maximizes your monthly benefit (8% more per year you delay).

The right choice depends on your health, financial needs, and other income sources. Want to discuss break-even ages or specific scenarios?"""

        else:
            response = """I can help with retirement planning questions like Social Security timing, Roth conversions, tax strategies, withdrawal rates, and Medicare planning.

What specific aspect would you like to explore?"""

        # Add citations if available
        if citation_text:
            response += f"\n\n**Sources:**\n{citation_text}"

        return response


# Singleton instance
ai_provider = AIProvider()
