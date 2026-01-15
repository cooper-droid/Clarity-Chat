"""
Routing service for CRM integration and Calendly link generation.
Routes leads to appropriate meeting types and advisors based on conversation content.
"""
from typing import Dict, List
from sqlalchemy.orm import Session

# Import PostgreSQL models
from models import Lead, Conversation, Message

from datetime import datetime
import re


class RoutingService:
    # Routing rules: keyword patterns -> bucket
    ROUTING_RULES = {
        "tax_forward": [
            r"\b(tax|taxes|roth|irmaa|conversion|medicare)\b",
            r"\b(tax planning|tax strategy|tax bracket)\b",
        ],
        "income": [
            r"\b(retirement income|social security|pension|annuity)\b",
            r"\b(withdrawal|distribution|rmd|required minimum)\b",
        ],
        "business": [
            r"\b(business owner|sell.*business|liquidity event)\b",
            r"\b(exit strategy|company sale|equity compensation)\b",
        ],
        "estate": [
            r"\b(estate|legacy|inheritance|trust|beneficiary)\b",
            r"\b(gift|charitable|philanthrop)\b",
        ],
    }

    # Urgency patterns for meeting type selection
    URGENCY_PATTERNS = [
        r"\b(retiring (soon|within|in \d+)|retire next year|retiring in \d+)\b",
        r"\b(major (event|decision|change)|urgent|time-sensitive)\b",
        r"\b(selling business|sold company|windfall)\b",
    ]

    # Calendly URLs (mock for MVP)
    CALENDLY_URLS = {
        "tax_forward_15": "https://calendly.com/fiat-wealth/tax-clarity-call-15min",
        "tax_forward_60": "https://calendly.com/fiat-wealth/tax-clarity-visit-60min",
        "income_15": "https://calendly.com/fiat-wealth/income-clarity-call-15min",
        "income_60": "https://calendly.com/fiat-wealth/income-clarity-visit-60min",
        "business_15": "https://calendly.com/fiat-wealth/business-clarity-call-15min",
        "business_60": "https://calendly.com/fiat-wealth/business-clarity-visit-60min",
        "estate_15": "https://calendly.com/fiat-wealth/estate-clarity-call-15min",
        "estate_60": "https://calendly.com/fiat-wealth/estate-clarity-visit-60min",
        "general_15": "https://calendly.com/fiat-wealth/clarity-call-15min",
        "general_60": "https://calendly.com/fiat-wealth/clarity-visit-60min",
    }

    def __init__(self, db: Session):
        self.db = db

    def route_lead(
        self,
        conversation_id: int,
        first_name: str,
        email: str,
        phone: str
    ) -> Dict:
        """
        Route a lead based on conversation content.
        Returns lead record with bucket, meeting_type, and booking_url.
        """
        # Get conversation transcript
        conversation = self.db.query(Conversation).filter(
            Conversation.id == conversation_id
        ).first()

        if not conversation:
            raise ValueError(f"Conversation {conversation_id} not found")

        # Get all messages
        messages = self.db.query(Message).filter(
            Message.conversation_id == conversation_id
        ).order_by(Message.created_at).all()

        # Build transcript
        transcript = " ".join([msg.content for msg in messages])

        # Determine bucket
        bucket = self._determine_bucket(transcript)

        # Determine meeting type
        meeting_type = self._determine_meeting_type(transcript)

        # Get booking URL
        booking_key = f"{bucket}_{meeting_type.split('_')[-1]}"  # e.g., "tax_forward_15"
        booking_url = self.CALENDLY_URLS.get(
            booking_key,
            self.CALENDLY_URLS["general_15"]
        )

        # Create or update lead
        lead = self.db.query(Lead).filter(Lead.email == email).first()

        if lead:
            # Update existing lead
            lead.first_name = first_name
            lead.phone = phone
            lead.bucket = bucket
            lead.meeting_type = meeting_type
            lead.booking_url = booking_url
            lead.updated_at = datetime.utcnow()
            lead.extra_data = {
                **(lead.extra_data or {}),
                "last_conversation_id": conversation_id,
                "transcript_preview": transcript[:500]
            }
        else:
            # Create new lead
            lead = Lead(
                first_name=first_name,
                email=email,
                phone=phone,
                bucket=bucket,
                meeting_type=meeting_type,
                booking_url=booking_url,
                meta={
                    "first_conversation_id": conversation_id,
                    "transcript_preview": transcript[:500]
                }
            )
            self.db.add(lead)

        # Link conversation to lead
        conversation.lead_id = lead.id

        self.db.commit()
        self.db.refresh(lead)

        return {
            "lead_id": lead.id,
            "bucket": lead.bucket,
            "meeting_type": lead.meeting_type,
            "booking_url": lead.booking_url,
        }

    def _determine_bucket(self, transcript: str) -> str:
        """Determine routing bucket based on transcript content."""
        transcript_lower = transcript.lower()
        scores = {}

        for bucket, patterns in self.ROUTING_RULES.items():
            score = 0
            for pattern in patterns:
                matches = re.findall(pattern, transcript_lower, re.IGNORECASE)
                score += len(matches)
            scores[bucket] = score

        # Return bucket with highest score, or "general" if no matches
        if max(scores.values()) > 0:
            return max(scores, key=scores.get)
        else:
            return "general"

    def _determine_meeting_type(self, transcript: str) -> str:
        """Determine meeting type (15-min call or 60-min visit) based on urgency."""
        transcript_lower = transcript.lower()

        for pattern in self.URGENCY_PATTERNS:
            if re.search(pattern, transcript_lower, re.IGNORECASE):
                return "clarity_visit_60"

        # Default to 15-minute call
        return "clarity_call_15"

    def get_booking_url(self, lead_id: int) -> str:
        """Get Calendly booking URL for a lead."""
        lead = self.db.query(Lead).filter(Lead.id == lead_id).first()
        if lead and lead.booking_url:
            return lead.booking_url
        return self.CALENDLY_URLS["general_15"]
