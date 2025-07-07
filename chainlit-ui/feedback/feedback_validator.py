"""
Feedback Validator Module

Validates user feedback using LLM before applying to agent instructions.
"""

import os
import logging
from typing import Dict, Any
from julep import AsyncJulep

logger = logging.getLogger(__name__)

class FeedbackValidator:
    def __init__(self, julep_client: AsyncJulep):
        """Initialize the feedback validator with Julep client"""
        self.client = julep_client
    
    async def validate_feedback(
        self,
        feedback_text: str,
        user_question: str,
        agent_response: str,
        agent_instructions: str
    ) -> Dict[str, Any]:
        """
        Validate user feedback using LLM
        
        Returns:
            Dictionary with validation results including is_valid, confidence, category, etc.
        """
        validation_prompt = f"""You are analyzing feedback for a Julep documentation assistant to improve its instructions.

Current Agent Instructions:
{agent_instructions}

User Question: {user_question}
Agent Response: {agent_response[:1000]}{'...' if len(agent_response) > 1000 else ''}
User Feedback: {feedback_text}

Your task:
1. Analyze if this feedback is valid and actionable
2. If valid, determine how to update the agent's instructions to address this feedback
3. Create an improved version of the instructions that incorporates this feedback

The updated instructions should:
- Maintain the existing structure and all current capabilities
- Add new guidance based on the feedback
- Be concise and avoid redundancy
- Not include the specific user question or feedback text

Return a JSON object with this structure:
{{
    "is_valid": boolean,
    "confidence": 0.0-1.0,
    "category": "accuracy|completeness|clarity|relevance|code_quality|other",
    "reasoning": "Why this feedback is valid/invalid",
    "updated_instructions": "The complete updated instructions (or null if no update needed)"
}}

Return ONLY the JSON object, no other text."""

        try:
            # Create a temporary session for validation using the existing agent
            # This avoids creating unnecessary agents
            session = await self.client.sessions.create(
                agent=os.getenv("AGENT_UUID", "ce7be83e-db8b-4ba9-808e-7cade6812e98")
            )
            
            # Get validation from the model
            response = await self.client.sessions.chat(
                session_id=session.id,
                messages=[
                    {
                        "role": "user",
                        "content": validation_prompt
                    }
                ],
                recall=False,  # Don't need RAG for validation
                model="claude-sonnet-4",  # Use a fast model for validation
            )
            # Clean up session only
            await self.client.sessions.delete(session_id=session.id)
            
            # Parse the response
            import json
            try:
                result = json.loads(response.choices[0].message.content)
                return result
            except json.JSONDecodeError:
                logger.error("Failed to parse validation response as JSON")
                return {
                    "is_valid": False,
                    "confidence": 0.0,
                    "reasoning": "Failed to parse validation response"
                }
                
        except Exception as e:
            logger.error(f"Error validating feedback: {str(e)}")
            return {
                "is_valid": False,
                "confidence": 0.0,
                "reasoning": f"Validation error: {str(e)}"
            }