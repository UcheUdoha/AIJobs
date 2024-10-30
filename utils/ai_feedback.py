import os
from openai import OpenAI
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AIFeedback:
    def __init__(self):
        self.client = OpenAI(api_key=os.environ['OPENAI_API_KEY'])
        
    def analyze_response(self, question: str, response: str, category: str) -> dict:
        """Generate AI feedback for interview response"""
        try:
            system_prompt = f"""You are an expert interviewer evaluating a candidate's response.
            Category: {category}
            Question: {question}
            
            Analyze the response based on:
            1. Clarity and Structure (25 points)
            2. Relevance to Question (25 points)
            3. Technical Accuracy/Depth (25 points)
            4. Communication Style (25 points)
            
            Provide:
            1. A score out of 100
            2. Detailed feedback with specific improvements
            3. Key strengths
            4. Areas for improvement"""

            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": response}
            ]

            completion = self.client.chat.completions.create(
                model="gpt-4",
                messages=messages,
                max_tokens=1000,
                temperature=0.7
            )
            
            feedback = completion.choices[0].message.content
            
            # Extract score from feedback (assuming it's in the first few lines)
            score = 70  # Default score
            for line in feedback.split('\n'):
                if 'score' in line.lower():
                    try:
                        score = int(''.join(filter(str.isdigit, line)))
                        break
                    except ValueError:
                        pass
            
            return {
                'score': score,
                'feedback': feedback
            }
            
        except Exception as e:
            logger.error(f"Error generating AI feedback: {str(e)}")
            return {
                'score': 0,
                'feedback': f"Error generating feedback: {str(e)}"
            }
