"""
AI Service module for GHCS application.
Handles Google GenAI integration with lazy loading and error handling.
"""
import json
import logging
from typing import Dict, Any, Optional, List
from config import config

logger = logging.getLogger(__name__)

class AIService:
    """AI service for risk analysis using Google GenAI."""
    
    def __init__(self):
        self._model = None
        self._initialized = False
        self._initialization_error = None
        
        # AI analyst prompt template
        self.AI_ANALYST_PROMPT = """You are an expert financial and cybersecurity analyst for a government regulatory body overseeing a Green Hydrogen Credit System. Your task is to assess the risk of a pending credit issuance request. Analyze the provided data for anomalies, fraud, or inconsistencies. DATA PROVIDED: Producer Name, Stated Daily Capacity, Pending Issuance Amount, Recent Transaction History. YOUR ANALYSIS MUST COVER: 1. Volatility Analysis (drastic spikes/drops). 2. Capacity Breach. 3. Pattern Anomalies. RESPONSE FORMAT: You MUST respond with ONLY a valid JSON object. The JSON structure must be: { "risk_score": <integer, 0-100>, "assessment": "<string, "Low Risk" | "Medium Risk" | "High Risk">", "summary": "<string, a one-sentence summary>", "detailed_analysis": ["<string, first point>", "<string, second point>"] } """
    
    def _initialize_ai_model(self) -> bool:
        """Initialize the AI model with lazy loading."""
        if self._initialized:
            return self._model is not None
        
        self._initialized = True
        
        if not config.is_ai_enabled():
            logger.info("AI service is disabled in configuration")
            return False
        
        try:
            # Lazy import to avoid dependency conflicts
            import google.generativeai as genai
            
            # Load API key
            api_key_file = config.get('API_KEY_FILE', 'api_key.txt')
            try:
                with open(api_key_file, 'r') as f:
                    api_key = f.read().strip()
                if not api_key:
                    raise ValueError("API key file is empty")
            except FileNotFoundError:
                logger.error(f"API key file '{api_key_file}' not found")
                self._initialization_error = "API key file not found"
                return False
            
            # Configure GenAI
            genai.configure(api_key=api_key)
            model_name = config.get('AI_MODEL_NAME', 'gemini-2.5-flash')
            self._model = genai.GenerativeModel(model_name=model_name)
            
            logger.info(f"AI service initialized successfully with model: {model_name}")
            return True
            
        except ImportError as e:
            logger.error(f"Failed to import Google GenAI: {e}")
            self._initialization_error = "Google GenAI not available"
            return False
        except Exception as e:
            logger.error(f"Failed to initialize AI service: {e}")
            self._initialization_error = str(e)
            return False
    
    def is_available(self) -> bool:
        """Check if AI service is available."""
        return self._initialize_ai_model()
    
    def get_initialization_error(self) -> Optional[str]:
        """Get the initialization error if any."""
        return self._initialization_error
    
    def get_risk_analysis(self, producer_name: str, capacity: int, pending_amount: int, 
                         transaction_history: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Get AI risk analysis for a credit issuance request.
        
        Args:
            producer_name: Name of the producer
            capacity: Producer's stated daily capacity
            pending_amount: Amount of credits being requested
            transaction_history: List of recent transactions
            
        Returns:
            Dictionary containing risk analysis or error information
        """
        if not self.is_available():
            error_msg = self._initialization_error or "AI service is not available"
            logger.warning(f"AI analysis requested but service unavailable: {error_msg}")
            return {
                "error": error_msg,
                "risk_score": 50,  # Default medium risk
                "assessment": "Medium Risk",
                "summary": "AI analysis unavailable - manual review required",
                "detailed_analysis": ["AI service is not available for automated analysis"]
            }
        
        try:
            # Format transaction history
            history_str = "\n".join([
                f"- {tx.get('amount', 0)} credits on {tx.get('timestamp', 'Unknown')[:10]}" 
                for tx in transaction_history
            ]) or "No previous transactions."
            
            # Create user prompt
            user_prompt = (
                f"ANALYSIS REQUEST:\n"
                f"- Producer Name: {producer_name}\n"
                f"- Stated Daily Capacity: {capacity}\n"
                f"- Pending Issuance Amount: {pending_amount}\n"
                f"- Recent Transaction History:\n{history_str}"
            )
            
            logger.info(f"Generating AI analysis for producer: {producer_name}")
            
            # Generate AI response
            response = self._model.generate_content([self.AI_ANALYST_PROMPT, user_prompt])
            
            # Clean and parse response
            cleaned_text = response.text.strip().replace("```json", "").replace("```", "")
            analysis_result = json.loads(cleaned_text)
            
            logger.info(f"AI analysis completed for {producer_name}: {analysis_result.get('assessment', 'Unknown')}")
            return analysis_result
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse AI response as JSON: {e}")
            return {
                "error": "Failed to parse AI analysis response",
                "risk_score": 75,  # Higher risk due to parsing failure
                "assessment": "High Risk",
                "summary": "AI analysis failed - manual review required",
                "detailed_analysis": ["AI response could not be parsed properly"]
            }
        except Exception as e:
            logger.error(f"Error during AI analysis: {e}")
            return {
                "error": f"AI analysis failed: {str(e)}",
                "risk_score": 75,  # Higher risk due to failure
                "assessment": "High Risk", 
                "summary": "AI analysis encountered an error - manual review required",
                "detailed_analysis": ["AI analysis system encountered an unexpected error"]
            }

# Global AI service instance
ai_service = AIService()