import google.generativeai as genai
import json
import re
from fastapi import HTTPException
from typing import Dict, Any

# Configure Gemini API
GEMINI_API_KEY = "AIzaSyDAH3gZbmTJQJ_rN2EK1qHpBTUB-WdjTE8"
genai.configure(api_key=GEMINI_API_KEY)

class PitchDeckAnalyzer:
    def __init__(self):
        self.model = genai.GenerativeModel(model_name="models/gemini-1.5-pro")
    
    @staticmethod
    def clean_json_response(response_text: str) -> str:
        """Remove markdown code blocks and clean the response text"""
        cleaned_text = re.sub(r'```json\s*|\s*```', '', response_text)
        return cleaned_text.strip()
    
    def create_analysis_prompt(self, extracted_text: str) -> str:
        """Create the prompt for pitch deck analysis"""
        return f"""
        You are an expert presentation and pitch deck analyst. Analyze this presentation text and provide a detailed analysis.
        Focus on specific content from the slides and provide concrete examples in your analysis.

        Presentation text:
        {extracted_text}

        Return only a JSON object with this exact structure:
        {{
            "score": <number 0-100>,
            "pitch_deck_purpose": <string>,
            "company_name": <string>,
            "industry": <string>,
            "target_audience": <string>,
            "key_metrics": {{
                "market_size": <string>,
                "target_market": <string>,
                "current_traction": <string>
            }},
            "strengths": [
                {{
                    "point": <string>,
                    "evidence": <string from the slides>,
                    "impact": <string>
                }}
            ],
            "weaknesses": [
                {{
                    "point": <string>,
                    "slide_reference": <string>,
                    "improvement_needed": <string>,
                    "priority": <string: "High"|"Medium"|"Low">
                }}
            ],
            "improvement_suggestions": [
                {{
                    "area": <string>,
                    "current_state": <string from the slides>,
                    "suggested_improvement": <string>,
                    "expected_impact": <string>
                }}
            ],
            "notable_quotes": [<array of important text directly from slides>],
            "presentation_structure": {{
                "flow_rating": <number 0-100>,
                "narrative_strength": <string>,
                "slide_organization": <string>
            }}
        }}
        """

    async def analyze_content(self, extracted_text: str) -> Dict[str, Any]:
        """
        Analyze the extracted text from the pitch deck and return structured analysis
        
        Args:
            extracted_text (str): The text extracted from the pitch deck
            
        Returns:
            Dict[str, Any]: Structured analysis of the pitch deck
            
        Raises:
            HTTPException: If analysis fails or response parsing fails
        """
        try:
            # Create chat instance
            chat = self.model.start_chat(history=[])
            
            # Generate the analysis prompt
            prompt = self.create_analysis_prompt(extracted_text)
            
            # Get response from Gemini
            response = chat.send_message(prompt)
            
            if not response.text:
                raise HTTPException(
                    status_code=500,
                    detail="Failed to get response from Gemini API"
                )
            
            # Clean and parse the response
            cleaned_response = self.clean_json_response(response.text)
            analysis_json = json.loads(cleaned_response)
            
            # Validate required fields
            required_fields = [
                "score", "pitch_deck_purpose", "company_name",
                "industry", "strengths", "weaknesses"
            ]
            
            for field in required_fields:
                if field not in analysis_json:
                    raise HTTPException(
                        status_code=500,
                        detail=f"Missing required field in analysis: {field}"
                    )
            
            return analysis_json

        except json.JSONDecodeError as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to parse analysis response: {str(e)}"
            )
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Analysis failed: {str(e)}"
            )

# Create singleton instance
analyzer = PitchDeckAnalyzer()

async def analyze_presentation_content(extracted_text: str) -> Dict[str, Any]:
    """
    Wrapper function for the PitchDeckAnalyzer
    
    Args:
        extracted_text (str): The text extracted from the pitch deck
        
    Returns:
        Dict[str, Any]: Structured analysis of the pitch deck
    """
    return await analyzer.analyze_content(extracted_text)