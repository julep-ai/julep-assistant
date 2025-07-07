"""
Feedback Handler Module

Manages user feedback collection and applies it to agent instructions.
"""

import logging
from typing import Dict, Any, Optional
from julep import AsyncJulep
import chainlit as cl
from .feedback_validator import FeedbackValidator

logger = logging.getLogger(__name__)

class FeedbackHandler:
    def __init__(self, julep_client: AsyncJulep, agent_id: str):
        """Initialize the feedback handler with Julep client and agent ID"""
        self.client = julep_client
        self.agent_id = agent_id
        self.validator = FeedbackValidator(julep_client)
    
    async def process_feedback(
        self, 
        feedback_text: str, 
        user_question: str, 
        agent_response: str,
        session_id: str
    ) -> Dict[str, Any]:
        """
        Process user feedback and update agent instructions if valid
        
        Args:
            feedback_text: The user's feedback
            user_question: Original question from the user
            agent_response: The agent's response to the question
            session_id: Current session ID
            
        Returns:
            Dictionary with processing results
        """
        try:
            # Get current agent details
            agent = await self.client.agents.get(agent_id=self.agent_id)
            
            # Get current instructions as string
            if isinstance(agent.instructions, list):
                current_instructions_str = "\n".join(agent.instructions)
            else:
                current_instructions_str = agent.instructions or ""
            
            # Validate the feedback
            validation_result = await self.validator.validate_feedback(
                feedback_text=feedback_text,
                user_question=user_question,
                agent_response=agent_response,
                agent_instructions=current_instructions_str
            )
            
            # Check if feedback is valid and has high confidence
            if validation_result.get("is_valid") and validation_result.get("confidence", 0) >= 0.7:
                # Get the updated instructions from the validator
                updated_instructions = validation_result.get("updated_instructions")
                
                if updated_instructions:
                    logger.info(f"Applying feedback with category: {validation_result.get('category')}")
                    
                    # Update the agent with new instructions
                    await self.client.agents.create_or_update(
                        agent_id=self.agent_id,
                        name=agent.name,
                        instructions=updated_instructions, 
                    )
                    
                    logger.info(f"Applied feedback to agent instructions: {validation_result.get('category')}")
                    
                    return {
                        "status": "success",
                        "message": f"Thank you! Your feedback has been applied. Category: {validation_result.get('category')}",
                        "validation": validation_result
                    }
                else:
                    # Valid feedback but no instruction update needed
                    return {
                        "status": "acknowledged",
                        "message": "Thank you for your feedback. We've noted your input for future improvements.",
                        "validation": validation_result
                    }
            else:
                # Feedback not valid or low confidence
                logger.info(f"Feedback not applied: {validation_result.get('reasoning')}")
                
                return {
                    "status": "not_applied",
                    "message": "Thank you for your feedback. While we appreciate your input, this feedback doesn't meet our criteria for automatic application.",
                    "validation": validation_result
                }
                
        except Exception as e:
            logger.error(f"Error processing feedback: {str(e)}")
            return {
                "status": "error",
                "message": f"An error occurred while processing your feedback: {str(e)}"
            }
    
    def create_feedback_actions(self, message_id: str) -> list:
        """
        Create Chainlit actions for feedback collection
        
        Args:
            message_id: The ID of the message to attach feedback to
            
        Returns:
            List of Chainlit actions
        """
        return [
            cl.Action(
                name="feedback_helpful",
                payload={"value": "helpful"},
                label="👍 Helpful"
            ),
            cl.Action(
                name="feedback_not_helpful",
                payload={"value": "not_helpful"}, 
                label="👎 Not Helpful"
            ),
            cl.Action(
                name="feedback_detailed",
                payload={"value": "detailed"},
                label="💭 Give Detailed Feedback"
            )
        ]
    
    async def handle_feedback_action(self, action: cl.Action, original_question: str, agent_response: str):
        """
        Handle feedback action from the user
        
        Args:
            action: The Chainlit action triggered
            original_question: The original user question
            agent_response: The agent's response
        """
        session_id = cl.user_session.get("session_id")
        
        if action.payload.get("value") == "helpful":
            # Simple positive feedback
            result = await self.process_feedback(
                feedback_text="The response was helpful and answered my question well.",
                user_question=original_question,
                agent_response=agent_response,
                session_id=session_id
            )
            
            await cl.Message(
                content="Thank you for your positive feedback! 🎉",
                author="System"
            ).send()
            
        elif action.payload.get("value") == "not_helpful":
            # Request more details for negative feedback
            res = await cl.AskUserMessage(
                content="What specifically could be improved about this response?",
                timeout=60
            ).send()
            
            if res:
                result = await self.process_feedback(
                    feedback_text=res['output'],
                    user_question=original_question,
                    agent_response=agent_response,
                    session_id=session_id
                )
                
                await cl.Message(
                    content=result.get('message', 'Thank you for your feedback!'),
                    author="System"
                ).send()
                
        elif action.payload.get("value") == "detailed":
            # Request detailed feedback
            res = await cl.AskUserMessage(
                content="Please provide your detailed feedback. What worked well? What could be improved?",
                timeout=90
            ).send()
            
            if res:
                result = await self.process_feedback(
                    feedback_text=res['output'],
                    user_question=original_question,
                    agent_response=agent_response,
                    session_id=session_id
                )
                
                # Show validation details if feedback was applied
                if result.get('status') == 'success':
                    validation = result.get('validation', {})
                    await cl.Message(
                        content=f"""✅ {result.get('message')}

**Analysis Details:**
- Confidence: {validation.get('confidence', 0):.2f}
- Reasoning: {validation.get('reasoning', 'N/A')}""",
                        author="System"
                    ).send()
                else:
                    await cl.Message(
                        content=result.get('message', 'Thank you for your feedback!'),
                        author="System"
                    ).send()