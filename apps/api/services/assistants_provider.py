"""
OpenAI Assistants API provider with Clarity Storage integration.
Uses your existing OpenAI project with vector store and custom prompt.
"""
import os
import time
from typing import List, Dict, Optional, Iterator
from dotenv import load_dotenv

load_dotenv()


class AssistantsProvider:
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY", "")
        self.dev_mode = os.getenv("DEV_MODE", "true").lower() == "true"

        # Your OpenAI project configuration
        self.vector_store_id = os.getenv("OPENAI_VECTOR_STORE_ID", "")
        self.assistant_id = os.getenv("OPENAI_ASSISTANT_ID", "")

        self.client = None
        self.assistant = None

        if self.api_key and not self.dev_mode:
            try:
                from openai import OpenAI
                self.client = OpenAI(api_key=self.api_key)

                # Use existing assistant or create new one
                if self.assistant_id:
                    try:
                        self.assistant = self.client.beta.assistants.retrieve(self.assistant_id)
                        print(f"✓ Using existing assistant: {self.assistant.id}")
                    except:
                        print("⚠ Assistant ID not found, will create new one")
                        self.assistant = None

                if not self.assistant:
                    self.assistant = self._create_assistant()
                    print(f"✓ Created new assistant: {self.assistant.id}")
                    print(f"  Add to .env: OPENAI_ASSISTANT_ID={self.assistant.id}")

            except Exception as e:
                print(f"⚠ OpenAI initialization failed: {e}. Running in DEV MODE.")
                self.dev_mode = True
        else:
            print("ℹ Running in DEV MODE (no OpenAI API key)")

    def _create_assistant(self):
        """Create a new assistant with Clarity configuration."""
        tools = [{"type": "file_search"}]

        # Your custom system prompt from the screenshot
        instructions = """You are Clarity, an AI-powered retirement education assistant built by Fiat Wealth Management.

Your role is to help people understand retirement planning concepts clearly and confidently by educating them first and helping them see how optimal planning meets real life.

You are not a financial advisor. You do not replace a human advisor. You exist to provide education, context, and clarity.

IDENTITY & TONE
You are:
- Clear, calm, and empathetic
- Educational and fiduciary-minded
- Practical and grounded in real life
- Neutral, balanced, and non-judgmental
- Designed to reduce confusion and overwhelm

You are NOT:
- Giving personalized financial advice
- Recommending specific investments or products
- Telling users what they "should" do

You believe:
- Education comes before advice
- Good decisions come from understanding tradeoffs
- The best plan is one someone can actually follow
- Retirement advice should live where optimal planning meets real life
- Avoid jargon whenever possible. If technical terms are used, explain them simply.

FIAT VOICE & COMMUNICATION STYLE
Speak with the clarity and approach of Fiat Wealth Management advisors, but do not explicitly say responses are "what Fiat Wealth Management would do" or make it sound like you're quoting them. Responses should feel like natural, helpful education — not marketing.

Use their frameworks and philosophy, but don't frame answers as "this is what we believe" unless directly relevant.

RESPONSE GUIDELINES
- Start with education, not answers
- Explain tradeoffs before giving direction
- Use real-life context and examples
- Keep responses conversational and approachable
- Avoid lists unless they genuinely help clarity
- Don't overwhelm — break complex topics into digestible parts
- If a question requires personalized advice, acknowledge what you can explain vs. what needs a human advisor

WHEN TO STOP
If someone asks for specific investment recommendations, portfolio allocations, or personalized tax/legal advice, politely redirect:
"That's a great question, but it's one that really needs a personalized approach. A fiduciary advisor can walk through your full situation and help you decide what makes sense for you. I'm here to help you understand the concepts so you can have better conversations with your advisor."

Remember: You're here to educate and clarify — not to replace human guidance."""

        config = {
            "name": "Clarity",
            "instructions": instructions,
            "model": "gpt-4o",
            "tools": tools,
        }

        # Attach vector store if provided
        if self.vector_store_id:
            config["tool_resources"] = {
                "file_search": {
                    "vector_store_ids": [self.vector_store_id]
                }
            }

        return self.client.beta.assistants.create(**config)

    def generate_streaming_response(
        self,
        messages: List[Dict[str, str]],
        thread_id: Optional[str] = None
    ) -> Iterator[Dict]:
        """
        Generate streaming chat response using Assistants API.
        Yields events as they come in.
        """
        if self.dev_mode or not self.client or not self.assistant:
            yield from self._dev_mode_streaming(messages)
            return

        try:
            # Create or use existing thread
            if not thread_id:
                thread = self.client.beta.threads.create()
                thread_id = thread.id

            # Add user message
            user_message = messages[-1]["content"]
            self.client.beta.threads.messages.create(
                thread_id=thread_id,
                role="user",
                content=user_message
            )

            # Stream the response
            with self.client.beta.threads.runs.stream(
                thread_id=thread_id,
                assistant_id=self.assistant.id,
            ) as stream:
                for event in stream:
                    # Text delta events
                    if event.event == "thread.message.delta":
                        for content in event.data.delta.content:
                            if content.type == "text":
                                if hasattr(content.text, 'value'):
                                    yield {
                                        "type": "content",
                                        "content": content.text.value
                                    }

                    # Completed event
                    elif event.event == "thread.run.completed":
                        # Get final message for citations
                        messages = self.client.beta.threads.messages.list(
                            thread_id=thread_id,
                            order="desc",
                            limit=1
                        )

                        if messages.data:
                            message = messages.data[0]
                            # Extract citations from annotations
                            for content_block in message.content:
                                if hasattr(content_block, 'text') and hasattr(content_block.text, 'annotations'):
                                    annotations = content_block.text.annotations
                                    if annotations:
                                        yield {
                                            "type": "citations",
                                            "citations": self._extract_citations(annotations)
                                        }

                        yield {"type": "done"}

                    # Error event
                    elif event.event == "thread.run.failed":
                        yield {
                            "type": "error",
                            "error": "Assistant run failed"
                        }

        except Exception as e:
            print(f"Error in streaming response: {e}")
            yield {
                "type": "error",
                "error": str(e)
            }

    def _extract_citations(self, annotations) -> List[Dict]:
        """Extract citations from message annotations."""
        citations = []
        for annotation in annotations:
            if hasattr(annotation, 'file_citation'):
                citation = annotation.file_citation
                citations.append({
                    "title": getattr(citation, 'quote', 'Reference'),
                    "file_id": getattr(citation, 'file_id', ''),
                })
        return citations

    def _dev_mode_streaming(self, messages: List[Dict[str, str]]) -> Iterator[Dict]:
        """Generate streaming dev mode response."""
        user_message = messages[-1]["content"].lower() if messages else ""

        # Topic-based responses
        if "roth" in user_message or "conversion" in user_message:
            response = """A Roth conversion moves money from a traditional IRA to a Roth IRA. You pay taxes now, but get tax-free growth and withdrawals later. It often makes sense if you expect higher taxes in retirement or want to avoid RMDs.

Want me to explain tax strategies, timing considerations, or walk through an example?"""

        elif "social security" in user_message or "timing" in user_message:
            response = """You can claim Social Security between ages 62-70. Claiming at 62 gets you reduced benefits but more years of payments. Waiting until 70 maximizes your monthly benefit (8% more per year you delay).

The right choice depends on your health, financial needs, and other income sources. Want to discuss break-even ages or specific scenarios?"""

        else:
            response = """I can help with retirement planning questions like Social Security timing, Roth conversions, tax strategies, withdrawal rates, and Medicare planning.

What specific aspect would you like to explore?"""

        # Stream the response word by word
        words = response.split()
        for i, word in enumerate(words):
            yield {
                "type": "content",
                "content": word + (" " if i < len(words) - 1 else "")
            }
            time.sleep(0.05)  # Simulate streaming

        yield {"type": "done"}


# Singleton instance
assistants_provider = AssistantsProvider()
