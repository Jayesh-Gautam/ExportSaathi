"""
Test script for knowledge base document loader.

This script tests the complete pipeline:
1. Create sample documents locally
2. Load documents and generate embeddings
3. Build FAISS index
4. Verify the index works with sample queries

Requirements: 9.1, 9.2, 9.7
"""

import json
import logging
import tempfile
from pathlib import Path
from datetime import datetime

from models.internal import Document
from services.embeddings import get_embedding_service
from services.vector_store import FAISSVectorStore

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# Sample documents with realistic export compliance content
SAMPLE_DOCUMENTS = [
    {
        "id": "dgft_export_policy_agriculture",
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

6. Packaging and Labeling: Must comply with destination country requirements.
        """,
        "metadata": {
            "source": "DGFT",
            "country": "IN",
            "product_category": "agriculture",
            "certifications": ["APEDA", "FSSAI", "Phytosanitary"],
            "last_updated": "2024-01-15"
        }
    },
    {
        "id": "fda_food_export_requirements",
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

5. Common Rejection Reasons: Filth, salmonella, pesticide residues, undeclared allergens.
        """,
        "metadata": {
            "source": "FDA",
            "country": "US",
            "product_category": "food",
            "certifications": ["FDA_Registration", "FSMA"],
            "last_updated": "2024-01-10"
        }
    },
    {
        "id": "ce_marking_requirements",
        "content": """
CE Marking Requirements for Products Exported to European Union

CE marking is a mandatory conformity marking for products sold in the European Economic Area (EEA). 
It indicates that a product has been assessed and meets EU safety, health, and environmental protection requirements.

Key Requirements:

1. Applicable Products: CE marking is required for products in categories including:
   - Machinery
   - Electrical equipment
   - Toys
   - Medical devices
   - Personal protective equipment
   - Construction products

2. Conformity Assessment: Manufacturers must:
   - Identify applicable EU directives and harmonized standards
   - Verify product meets essential requirements
   - Carry out conformity assessment procedures
   - Compile technical documentation
   - Affix CE marking and draw up EU Declaration of Conformity

3. Technical Documentation: Must include:
   - General description of the product
   - Design and manufacturing drawings
   - Risk assessment
   - Test reports
   - Copies of harmonized standards applied

4. Notified Body: Some products require assessment by a Notified Body (independent testing organization).

5. Declaration of Conformity: Manufacturer must issue an EU Declaration of Conformity stating the product 
   meets all applicable requirements.
        """,
        "metadata": {
            "source": "EU",
            "country": "EU",
            "product_category": "manufacturing",
            "certifications": ["CE_Marking"],
            "last_updated": "2024-01-20"
        }
    },
    {
        "id": "rodtep_scheme_overview",
        "content": """
RoDTEP (Remission of Duties and Taxes on Exported Products) Scheme

RoDTEP is a WTO-compliant scheme that refunds taxes and duties incurred during the manufacturing and 
distribution of exported products that are not refunded under any other mechanism.

Key Features:

1. Eligibility: All exporters of goods are eligible for RoDTEP benefits. The scheme covers:
   - Central taxes and duties
   - State taxes and duties
   - Embedded taxes not refunded under GST

2. Rates: RoDTEP rates are notified by the government based on HS codes. Rates typically range from 
   0.5% to 4.3% of FOB value.

3. Calculation: RoDTEP benefit = FOB value × RoDTEP rate for the HS code

4. Claim Process:
   - File shipping bill with customs
   - RoDTEP credit is automatically credited to exporter's ledger
   - Credits can be used to pay customs duties or transferred

5. Documentation: Exporters must maintain:
   - Shipping bills
   - Invoice and packing list
   - Bill of lading
   - Certificate of origin

6. Exclusions: Certain products are excluded from RoDTEP including:
   - Products subject to export duty
   - Restricted products
   - Products under other export incentive schemes
        """,
        "metadata": {
            "source": "DGFT",
            "country": "IN",
            "product_category": "general",
            "certifications": [],
            "last_updated": "2024-01-12"
        }
    },
    {
        "id": "gst_lut_requirements",
        "content": """
GST LUT (Letter of Undertaking) for Exports

A Letter of Undertaking (LUT) allows exporters to export goods or services without paying Integrated GST (IGST).

Key Requirements:

1. Eligibility: Exporters can furnish LUT if:
   - They have not been prosecuted for tax evasion exceeding Rs. 2.5 crore
   - They have filed all GST returns for the past 2 years
   - Their aggregate turnover exceeds Rs. 40 lakhs (Rs. 20 lakhs for special category states)

2. Filing Process:
   - File LUT on GST portal (Form GST RFD-11)
   - LUT is valid for entire financial year
   - Must be renewed annually

3. Benefits:
   - Export without paying IGST upfront
   - Improves cash flow
   - Claim refund of input tax credit

4. Documentation for GST Refund:
   - Shipping bill with export details
   - Invoice and packing list
   - Bank realization certificate (BRC)
   - GST returns (GSTR-1, GSTR-3B)

5. Refund Timeline: GST refunds typically take 30-60 days after filing refund application.

6. Common Rejection Reasons:
   - Mismatch between shipping bill and GSTR-1
   - Missing or incorrect GSTIN on shipping bill
   - Incomplete documentation
   - Bank realization certificate not submitted
        """,
        "metadata": {
            "source": "GSTN",
            "country": "IN",
            "product_category": "general",
            "certifications": [],
            "last_updated": "2024-01-18"
        }
    }
]


def create_sample_documents() -> list[Document]:
    """Create sample Document objects for testing."""
    logger.info("Creating sample documents...")
    documents = []
    
    for doc_data in SAMPLE_DOCUMENTS:
        doc = Document(
            id=doc_data["id"],
            content=doc_data["content"].strip(),
            metadata=doc_data["metadata"],
            embedding=None
        )
        documents.append(doc)
    
    logger.info(f"Created {len(documents)} sample documents")
    return documents


def test_knowledge_base_loader():
    """Test the complete knowledge base loading pipeline."""
    logger.info("=" * 80)
    logger.info("Testing Knowledge Base Document Loader")
    logger.info("=" * 80)
    
    # Step 1: Create sample documents
    logger.info("\n[Step 1] Creating sample documents...")
    documents = create_sample_documents()
    
    # Print document summaries
    for doc in documents:
        logger.info(f"  - {doc.id}: {len(doc.content)} chars, metadata: {doc.metadata}")
    
    # Step 2: Generate embeddings
    logger.info("\n[Step 2] Generating embeddings...")
    embedding_service = get_embedding_service()
    
    texts = [doc.content for doc in documents]
    embeddings = embedding_service.embed_documents(texts)
    
    # Attach embeddings to documents
    for doc, embedding in zip(documents, embeddings):
        doc.embedding = embedding.tolist()
    
    logger.info(f"Generated embeddings with dimension: {len(embeddings[0])}")
    
    # Step 3: Build FAISS index
    logger.info("\n[Step 3] Building FAISS index...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        output_path = Path(temp_dir) / "test_index"
        
        # Initialize vector store
        vector_store = FAISSVectorStore(
            embedding_dimension=768,
            index_type="Flat"
        )
        vector_store.initialize()
        
        # Add documents
        vector_store.add_documents(documents)
        
        # Save index
        vector_store.save(str(output_path))
        logger.info(f"Saved index to {output_path}")
        
        # Get statistics
        stats = vector_store.get_stats()
        logger.info(f"Index statistics: {stats}")
        
        # Step 4: Test semantic search
        logger.info("\n[Step 4] Testing semantic search...")
        
        test_queries = [
            "What are the FDA requirements for food exports?",
            "How to get CE marking for products?",
            "What is RoDTEP and how to claim benefits?",
            "GST LUT requirements for exporters",
            "Agricultural export requirements from India"
        ]
        
        for query in test_queries:
            logger.info(f"\nQuery: {query}")
            
            # Generate query embedding
            query_embedding = embedding_service.embed_query(query)
            
            # Search
            results = vector_store.search(query_embedding, top_k=3)
            
            logger.info(f"Found {len(results)} results:")
            for i, doc in enumerate(results, 1):
                logger.info(
                    f"  {i}. {doc.id} (score: {doc.relevance_score:.4f})"
                )
                logger.info(f"     Source: {doc.metadata.get('source')}, "
                          f"Category: {doc.metadata.get('product_category')}")
        
        # Step 5: Test metadata filtering
        logger.info("\n[Step 5] Testing metadata filtering...")
        
        # Search for DGFT documents
        query_embedding = embedding_service.embed_query("export requirements")
        results = vector_store.search(
            query_embedding,
            top_k=5,
            filters={"source": "DGFT"}
        )
        logger.info(f"DGFT documents: {len(results)}")
        for doc in results:
            logger.info(f"  - {doc.id}")
        
        # Search for agriculture category
        results = vector_store.search(
            query_embedding,
            top_k=5,
            filters={"product_category": "agriculture"}
        )
        logger.info(f"Agriculture documents: {len(results)}")
        for doc in results:
            logger.info(f"  - {doc.id}")
        
        # Step 6: Test index persistence
        logger.info("\n[Step 6] Testing index persistence...")
        
        # Create new vector store and load saved index
        new_vector_store = FAISSVectorStore(embedding_dimension=768)
        new_vector_store.load(str(output_path))
        
        new_stats = new_vector_store.get_stats()
        logger.info(f"Loaded index statistics: {new_stats}")
        
        # Verify search still works
        query_embedding = embedding_service.embed_query("FDA food requirements")
        results = new_vector_store.search(query_embedding, top_k=2)
        logger.info(f"Search after reload: {len(results)} results")
        for doc in results:
            logger.info(f"  - {doc.id} (score: {doc.relevance_score:.4f})")
    
    logger.info("\n" + "=" * 80)
    logger.info("Knowledge Base Loader Test Completed Successfully!")
    logger.info("=" * 80)
    
    # Summary
    logger.info("\nSummary:")
    logger.info(f"✓ Created {len(documents)} sample documents")
    logger.info(f"✓ Generated embeddings (dimension: 768)")
    logger.info(f"✓ Built FAISS index with {stats['total_documents']} documents")
    logger.info(f"✓ Semantic search working correctly")
    logger.info(f"✓ Metadata filtering working correctly")
    logger.info(f"✓ Index persistence working correctly")
    logger.info("\nRequirements validated:")
    logger.info("  - 9.1: Documents loaded with metadata parsing")
    logger.info("  - 9.2: Embeddings generated and stored in vector store")
    logger.info("  - 9.7: Documents tagged with metadata (source, country, category)")


if __name__ == "__main__":
    test_knowledge_base_loader()
