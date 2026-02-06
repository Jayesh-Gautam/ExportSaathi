"""
Restricted Substances Analyzer Service for ExportSathi

This service identifies restricted substances from product ingredients and Bill of Materials (BOM).
It queries the knowledge base for substance regulations specific to the destination country
and returns a comprehensive list of restricted substances with reasons and applicable regulations.

Requirements: 2.3
"""

import logging
from typing import List, Optional, Dict, Any
import re

from models.report import RestrictedSubstance
from services.rag_pipeline import RAGPipeline, get_rag_pipeline
from services.llm_client import LLMClient, create_llm_client

logger = logging.getLogger(__name__)


class RestrictedSubstancesAnalyzer:
    """
    Analyzes product ingredients and BOM to identify restricted substances.
    
    This service uses a hybrid approach:
    1. RAG-based retrieval: Queries knowledge base for destination-specific regulations
    2. LLM analysis: Extracts restricted substances from retrieved documents
    3. Keyword matching: Fallback for common restricted substances
    
    The analyzer considers:
    - Destination country regulations (FDA, EU REACH, etc.)
    - Product ingredients and components
    - International standards and banned substances
    
    Requirements: 2.3
    """
    
    # Common restricted substances database (fallback)
    COMMON_RESTRICTED_SUBSTANCES = {
        # Heavy metals
        "lead": {
            "name": "Lead",
            "reason": "Toxic heavy metal that can cause neurological damage",
            "regulation": "EU REACH Annex XVII, US FDA, RoHS Directive"
        },
        "mercury": {
            "name": "Mercury",
            "reason": "Highly toxic heavy metal affecting nervous system",
            "regulation": "EU REACH Annex XVII, Minamata Convention, US EPA"
        },
        "cadmium": {
            "name": "Cadmium",
            "reason": "Toxic heavy metal, carcinogenic",
            "regulation": "EU REACH Annex XVII, RoHS Directive"
        },
        "arsenic": {
            "name": "Arsenic",
            "reason": "Toxic metalloid, carcinogenic",
            "regulation": "EU REACH Annex XVII, US FDA"
        },
        "chromium vi": {
            "name": "Hexavalent Chromium (Chromium VI)",
            "reason": "Highly toxic and carcinogenic form of chromium",
            "regulation": "EU REACH Annex XVII, RoHS Directive"
        },
        
        # Hazardous materials
        "asbestos": {
            "name": "Asbestos",
            "reason": "Carcinogenic fibrous material causing lung diseases",
            "regulation": "Banned in EU, US, and most countries"
        },
        "formaldehyde": {
            "name": "Formaldehyde",
            "reason": "Carcinogenic chemical, respiratory irritant",
            "regulation": "EU REACH, US EPA, restricted in textiles"
        },
        
        # Plasticizers and additives
        "phthalates": {
            "name": "Phthalates",
            "reason": "Endocrine disruptors affecting reproductive health",
            "regulation": "EU REACH Annex XVII, US CPSC (toys)"
        },
        "bpa": {
            "name": "Bisphenol A (BPA)",
            "reason": "Endocrine disruptor, restricted in food contact materials",
            "regulation": "EU Regulation 10/2011, US FDA restrictions"
        },
        "bisphenol": {
            "name": "Bisphenol A (BPA)",
            "reason": "Endocrine disruptor, restricted in food contact materials",
            "regulation": "EU Regulation 10/2011, US FDA restrictions"
        },
        
        # Pesticides and agricultural chemicals
        "ddt": {
            "name": "DDT (Dichlorodiphenyltrichloroethane)",
            "reason": "Persistent organic pollutant, environmental toxin",
            "regulation": "Stockholm Convention, banned globally"
        },
        "chlorpyrifos": {
            "name": "Chlorpyrifos",
            "reason": "Neurotoxic pesticide, harmful to children",
            "regulation": "Banned in EU, restricted in US"
        },
        
        # Food additives and preservatives
        "sudan dye": {
            "name": "Sudan Dyes (I, II, III, IV)",
            "reason": "Carcinogenic azo dyes, illegal in food",
            "regulation": "EU banned in food, US FDA prohibited"
        },
        "melamine": {
            "name": "Melamine",
            "reason": "Toxic chemical causing kidney damage",
            "regulation": "Strictly regulated in food products globally"
        },
        
        # Flame retardants
        "pbde": {
            "name": "Polybrominated Diphenyl Ethers (PBDEs)",
            "reason": "Persistent organic pollutants, endocrine disruptors",
            "regulation": "EU RoHS, Stockholm Convention"
        },
        "hbcd": {
            "name": "Hexabromocyclododecane (HBCD)",
            "reason": "Persistent organic pollutant, bioaccumulative",
            "regulation": "EU REACH, Stockholm Convention"
        },
        
        # Antibiotics and hormones (food/pharma)
        "chloramphenicol": {
            "name": "Chloramphenicol",
            "reason": "Antibiotic with serious side effects, banned in food animals",
            "regulation": "EU banned in food animals, US FDA zero tolerance"
        },
        "nitrofuran": {
            "name": "Nitrofurans",
            "reason": "Carcinogenic veterinary drugs",
            "regulation": "EU banned in food animals, US FDA prohibited"
        },
        "ractopamine": {
            "name": "Ractopamine",
            "reason": "Growth promoter banned in many countries",
            "regulation": "Banned in EU, China, Russia"
        },
        
        # Solvents
        "benzene": {
            "name": "Benzene",
            "reason": "Carcinogenic solvent",
            "regulation": "EU REACH, US EPA, strictly regulated"
        },
        "trichloroethylene": {
            "name": "Trichloroethylene",
            "reason": "Carcinogenic solvent",
            "regulation": "EU REACH Annex XVII, US EPA"
        },
        
        # Azo dyes (textiles)
        "azo dye": {
            "name": "Carcinogenic Azo Dyes",
            "reason": "Can release carcinogenic aromatic amines",
            "regulation": "EU REACH Annex XVII, restricted in textiles"
        },
        
        # Per- and polyfluoroalkyl substances
        "pfas": {
            "name": "PFAS (Per- and Polyfluoroalkyl Substances)",
            "reason": "Persistent chemicals, bioaccumulative, health risks",
            "regulation": "EU REACH restrictions, US EPA emerging contaminant"
        },
        "pfoa": {
            "name": "PFOA (Perfluorooctanoic Acid)",
            "reason": "Persistent organic pollutant, carcinogenic",
            "regulation": "EU REACH Annex XVII, Stockholm Convention"
        },
        "pfos": {
            "name": "PFOS (Perfluorooctane Sulfonate)",
            "reason": "Persistent organic pollutant, toxic",
            "regulation": "EU REACH Annex XVII, Stockholm Convention"
        }
    }
    
    def __init__(
        self,
        rag_pipeline: Optional[RAGPipeline] = None,
        llm_client: Optional[LLMClient] = None
    ):
        """
        Initialize Restricted Substances Analyzer.
        
        Args:
            rag_pipeline: RAG pipeline for document retrieval (uses global if None)
            llm_client: LLM client for analysis (creates new if None)
        """
        self.rag_pipeline = rag_pipeline or get_rag_pipeline()
        self.llm_client = llm_client or create_llm_client()
        
        logger.info("RestrictedSubstancesAnalyzer initialized")
    
    def analyze(
        self,
        ingredients: Optional[str],
        bom: Optional[str],
        destination_country: str,
        product_name: Optional[str] = None
    ) -> List[RestrictedSubstance]:
        """
        Analyze ingredients and BOM to identify restricted substances.
        
        This method uses a multi-stage approach:
        1. Query knowledge base for destination-specific regulations
        2. Use LLM to analyze ingredients against regulations
        3. Apply keyword matching as fallback
        4. Deduplicate and return results
        
        Args:
            ingredients: Product ingredients (comma-separated or free text)
            bom: Bill of Materials (component list)
            destination_country: Destination country for export
            product_name: Optional product name for context
            
        Returns:
            List of RestrictedSubstance objects with name, reason, and regulation
            
        Example:
            >>> analyzer = RestrictedSubstancesAnalyzer()
            >>> substances = analyzer.analyze(
            ...     ingredients="turmeric powder, lead chromate (colorant)",
            ...     bom=None,
            ...     destination_country="United States"
            ... )
            >>> print(substances[0].name)
            'Lead'
            
        Requirements: 2.3
        """
        logger.info(f"Analyzing restricted substances for destination: {destination_country}")
        
        # Combine ingredients and BOM
        content = self._combine_content(ingredients, bom)
        
        if not content:
            logger.info("No ingredients or BOM provided, returning empty list")
            return []
        
        restricted_substances = []
        
        # Stage 1: RAG-based analysis (primary method)
        try:
            rag_substances = self._analyze_with_rag(
                content=content,
                destination_country=destination_country,
                product_name=product_name
            )
            restricted_substances.extend(rag_substances)
            logger.info(f"RAG analysis found {len(rag_substances)} restricted substances")
        except Exception as e:
            logger.warning(f"RAG-based analysis failed: {e}. Falling back to keyword matching.")
        
        # Stage 2: Keyword matching (fallback and supplement)
        keyword_substances = self._analyze_with_keywords(content, destination_country)
        restricted_substances.extend(keyword_substances)
        logger.info(f"Keyword matching found {len(keyword_substances)} restricted substances")
        
        # Deduplicate by substance name
        unique_substances = self._deduplicate_substances(restricted_substances)
        
        logger.info(f"Total unique restricted substances identified: {len(unique_substances)}")
        return unique_substances
    
    def _combine_content(
        self,
        ingredients: Optional[str],
        bom: Optional[str]
    ) -> str:
        """
        Combine ingredients and BOM into single text for analysis.
        
        Args:
            ingredients: Product ingredients
            bom: Bill of Materials
            
        Returns:
            Combined content string
        """
        parts = []
        
        if ingredients:
            parts.append(f"Ingredients: {ingredients}")
        
        if bom:
            parts.append(f"Bill of Materials: {bom}")
        
        return " | ".join(parts)
    
    def _analyze_with_rag(
        self,
        content: str,
        destination_country: str,
        product_name: Optional[str]
    ) -> List[RestrictedSubstance]:
        """
        Analyze using RAG pipeline to query knowledge base.
        
        This method:
        1. Constructs a query for destination-specific regulations
        2. Retrieves relevant regulatory documents
        3. Uses LLM to extract restricted substances from documents
        
        Args:
            content: Combined ingredients and BOM
            destination_country: Destination country
            product_name: Optional product name
            
        Returns:
            List of RestrictedSubstance objects
        """
        # Build query for knowledge base
        query = self._build_regulation_query(content, destination_country, product_name)
        
        logger.info(f"Querying knowledge base: {query}")
        
        # Retrieve relevant documents
        documents = self.rag_pipeline.retrieve_documents(query=query, top_k=5)
        
        if not documents:
            logger.warning("No relevant documents found in knowledge base")
            return []
        
        # Build prompt for LLM analysis
        prompt = self._build_analysis_prompt(
            content=content,
            destination_country=destination_country,
            documents=documents
        )
        
        # Generate structured response
        try:
            response = self.llm_client.generate_structured(
                prompt=prompt,
                schema={
                    "type": "object",
                    "properties": {
                        "restricted_substances": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "name": {"type": "string"},
                                    "reason": {"type": "string"},
                                    "regulation": {"type": "string"}
                                },
                                "required": ["name", "reason", "regulation"]
                            }
                        }
                    },
                    "required": ["restricted_substances"]
                }
            )
            
            # Parse response and create RestrictedSubstance objects
            if response and "restricted_substances" in response:
                return [
                    RestrictedSubstance(
                        name=item["name"],
                        reason=item["reason"],
                        regulation=item["regulation"]
                    )
                    for item in response["restricted_substances"]
                ]
        
        except Exception as e:
            logger.error(f"LLM analysis failed: {e}")
            return []
        
        return []
    
    def _build_regulation_query(
        self,
        content: str,
        destination_country: str,
        product_name: Optional[str]
    ) -> str:
        """
        Build query for retrieving relevant regulations from knowledge base.
        
        Args:
            content: Combined ingredients and BOM
            destination_country: Destination country
            product_name: Optional product name
            
        Returns:
            Query string for knowledge base
        """
        query_parts = [
            f"restricted substances regulations {destination_country}",
            f"banned ingredients {destination_country}",
        ]
        
        if product_name:
            query_parts.append(product_name)
        
        # Extract potential substance names from content for targeted search
        content_lower = content.lower()
        for keyword in self.COMMON_RESTRICTED_SUBSTANCES.keys():
            if keyword in content_lower:
                query_parts.append(keyword)
        
        return " ".join(query_parts[:5])  # Limit query length
    
    def _build_analysis_prompt(
        self,
        content: str,
        destination_country: str,
        documents: List[Any]
    ) -> str:
        """
        Build prompt for LLM to analyze ingredients against regulations.
        
        Args:
            content: Combined ingredients and BOM
            destination_country: Destination country
            documents: Retrieved regulatory documents
            
        Returns:
            Prompt string for LLM
        """
        # Extract document content
        context = "\n\n".join([
            f"Regulatory Document {i+1}:\n{doc.page_content}"
            for i, doc in enumerate(documents[:3])
        ])
        
        return f"""You are an expert in international trade regulations and restricted substances.

Analyze the following product ingredients and Bill of Materials to identify any RESTRICTED or BANNED substances for export to {destination_country}.

Product Content:
{content}

Relevant Regulations:
{context}

Instructions:
1. Carefully review each ingredient and component
2. Check against the regulatory documents provided
3. Identify ANY substances that are:
   - Banned or prohibited in {destination_country}
   - Restricted or require special permits
   - Subject to concentration limits
   - Known to cause rejections at customs

For each restricted substance found, provide:
- name: The specific substance name (be precise)
- reason: Why it's restricted (health, environmental, safety concerns)
- regulation: The specific regulation or law (e.g., "EU REACH Annex XVII", "US FDA 21 CFR 189")

IMPORTANT:
- Only include substances that are ACTUALLY PRESENT in the product content
- Be specific about the substance name (not just "heavy metals" but "Lead", "Mercury", etc.)
- Cite the actual regulation from the documents provided
- If no restricted substances are found, return an empty array

Return ONLY substances that pose a real compliance risk for export to {destination_country}."""
    
    def _analyze_with_keywords(
        self,
        content: str,
        destination_country: str
    ) -> List[RestrictedSubstance]:
        """
        Analyze using keyword matching (fallback method).
        
        This method scans the content for known restricted substance keywords
        and returns matches from the common restricted substances database.
        
        Args:
            content: Combined ingredients and BOM
            destination_country: Destination country
            
        Returns:
            List of RestrictedSubstance objects
        """
        restricted = []
        content_lower = content.lower()
        
        # Scan for each known restricted substance
        for keyword, substance_info in self.COMMON_RESTRICTED_SUBSTANCES.items():
            # Use word boundary matching to avoid false positives
            pattern = r'\b' + re.escape(keyword) + r'\b'
            
            if re.search(pattern, content_lower):
                restricted.append(RestrictedSubstance(
                    name=substance_info["name"],
                    reason=substance_info["reason"],
                    regulation=substance_info["regulation"]
                ))
                logger.debug(f"Keyword match found: {substance_info['name']}")
        
        return restricted
    
    def _deduplicate_substances(
        self,
        substances: List[RestrictedSubstance]
    ) -> List[RestrictedSubstance]:
        """
        Remove duplicate substances based on name.
        
        If multiple entries exist for the same substance, keep the one with
        the most detailed information (longest reason and regulation).
        
        Args:
            substances: List of RestrictedSubstance objects
            
        Returns:
            Deduplicated list
        """
        if not substances:
            return []
        
        # Group by normalized name
        substance_map: Dict[str, RestrictedSubstance] = {}
        
        for substance in substances:
            # Normalize name for comparison
            normalized_name = substance.name.lower().strip()
            
            # If not seen before, add it
            if normalized_name not in substance_map:
                substance_map[normalized_name] = substance
            else:
                # Keep the one with more detailed information
                existing = substance_map[normalized_name]
                existing_detail = len(existing.reason) + len(existing.regulation)
                new_detail = len(substance.reason) + len(substance.regulation)
                
                if new_detail > existing_detail:
                    substance_map[normalized_name] = substance
        
        # Return deduplicated list
        return list(substance_map.values())


# Convenience function for quick analysis
def analyze_restricted_substances(
    ingredients: Optional[str],
    bom: Optional[str],
    destination_country: str,
    product_name: Optional[str] = None
) -> List[RestrictedSubstance]:
    """
    Convenience function to analyze restricted substances.
    
    Args:
        ingredients: Product ingredients
        bom: Bill of Materials
        destination_country: Destination country
        product_name: Optional product name
        
    Returns:
        List of RestrictedSubstance objects
    """
    analyzer = RestrictedSubstancesAnalyzer()
    return analyzer.analyze(
        ingredients=ingredients,
        bom=bom,
        destination_country=destination_country,
        product_name=product_name
    )
