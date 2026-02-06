"""
Create Sample Knowledge Base Documents

This script creates sample regulatory documents for testing the knowledge base loader.
It generates JSON documents with realistic content about export regulations, certifications,
and compliance requirements.

Usage:
    python -m services.create_sample_knowledge_base --bucket exportsathi-knowledge-base --upload

    Or to create local files only:
    python -m services.create_sample_knowledge_base --output ./sample_docs
"""

import argparse
import json
import logging
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime
import boto3
from botocore.exceptions import ClientError

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# Sample documents with realistic export compliance content
SAMPLE_DOCUMENTS = [
    {
        "filename": "dgft_export_policy_agriculture.json",
        "content": """
Export Policy for Agricultural Products from India

The Directorate General of Foreign Trade (DGFT) regulates the export of agricultural products from India. 
Key requirements include:

1. HS Code Classification: All agricultural products must be classified under the appropriate HS code 
   (Harmonized System Code) for customs clearance. Common codes include:
   - 0701: Potatoes (fresh or chilled)
   - 0713: Dried legumes
   - 0801: Coconuts, Brazil nuts, and cashew nuts
   - 1006: Rice

2. Export Licenses: Certain agricultural products require export licenses or are subject to Minimum Export 
   Price (MEP) restrictions. Check the current ITC (HS) classification for restrictions.

3. Quality Standards: Agricultural exports must meet quality standards specified by:
   - Agricultural and Processed Food Products Export Development Authority (APEDA)
   - Export Inspection Council (EIC)
   - Food Safety and Standards Authority of India (FSSAI)

4. Phytosanitary Certificates: Required for plant and plant products to certify they are free from pests 
   and diseases. Issued by the Plant Quarantine Division.

5. Certificate of Origin: Required to claim preferential tariff treatment under trade agreements.

6. Packaging and Labeling: Must comply with destination country requirements and include:
   - Product name and description
   - Net weight
   - Country of origin
   - Manufacturer details
   - Batch/lot number
   - Best before date

7. GST Compliance: Exporters must file GST returns and can claim refunds through the RoDTEP scheme.
        """,
        "metadata": {
            "source": "DGFT",
            "country": "IN",
            "product_category": "agriculture",
            "certifications": "APEDA,FSSAI,Phytosanitary",
            "last_updated": "2024-01-15"
        }
    },
    {
        "filename": "fda_food_export_requirements.json",
        "content": """
FDA Requirements for Food Exports to the United States

The U.S. Food and Drug Administration (FDA) regulates food imports under the Federal Food, Drug, and 
Cosmetic Act (FD&C Act) and the Public Health Security and Bioterrorism Preparedness and Response Act.

Key Requirements:

1. Food Facility Registration: All facilities that manufacture, process, pack, or hold food for consumption 
   in the U.S. must register with FDA. Registration must be renewed every two years.

2. Prior Notice: Importers must provide FDA with prior notice of food shipments before they arrive at U.S. 
   ports. This includes:
   - Product description
   - Manufacturer and shipper information
   - Anticipated arrival information
   - FDA product code

3. Food Safety Modernization Act (FSMA) Compliance:
   - Foreign Supplier Verification Program (FSVP)
   - Hazard Analysis and Risk-Based Preventive Controls (HARPC)
   - Sanitary Transportation of Human and Animal Food

4. Labeling Requirements:
   - Nutrition Facts label
   - Ingredient list in descending order by weight
   - Allergen declarations (Big 8 allergens)
   - Net quantity of contents
   - Name and address of manufacturer/distributor

5. Common Rejection Reasons (from FDA Import Refusal Reports):
   - Filth (insect parts, rodent hair)
   - Sal